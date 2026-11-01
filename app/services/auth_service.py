from datetime import datetime, timedelta, timezone
import secrets
from uuid import UUID
from fastapi import BackgroundTasks, HTTPException, status
import jwt
import psycopg
from app.config import settings
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.user import MessageResponse, UserResponse
from app.utils.email import send_otp_email
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class AuthService:
    @staticmethod
    def register(conn: psycopg.Connection, data: RegisterRequest) -> UserResponse:
        # Check existing email
        if UserRepository.get_by_email(conn, data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already registered"
            )

        # Check existing username
        if UserRepository.get_by_username(conn, data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )

        hashed_password = hash_password(data.password)

        created_user = UserRepository.create(
            conn=conn,
            name=data.name,
            email=data.email,
            username=data.username,
            hashed_password=hashed_password,
            avatar=data.avatar
        )

        conn.commit()
        return UserResponse.model_validate(created_user)

    @staticmethod
    def login(conn: psycopg.Connection, data: LoginRequest) -> TokenResponse:
        user = UserRepository.get_by_email_or_username(conn, data.identifier.strip())
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is currently inactive"
            )

        user_id_str = str(user.id)
        access_token = create_access_token(user_id_str)
        refresh_token = create_refresh_token(user_id_str)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )

    @staticmethod
    def refresh(conn: psycopg.Connection, refresh_token_str: str) -> TokenRefreshResponse:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

        try:
            payload = decode_token(refresh_token_str)
            token_type = payload.get("type")
            user_id = payload.get("sub")
            jti = payload.get("jti")
            exp = payload.get("exp")

            if token_type != "refresh" or not user_id:
                raise credentials_exception

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired, please log in again",
                headers={"WWW-Authenticate": "Bearer"}
            )
        except jwt.PyJWTError:
            raise credentials_exception

        # Check if this token was revoked
        if jti and UserRepository.is_token_revoked(conn, jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked, please log in again",
                headers={"WWW-Authenticate": "Bearer"}
            )

        try:
            parsed_uuid = UUID(user_id)
        except ValueError:
            raise credentials_exception

        user = UserRepository.get_by_id(conn, parsed_uuid)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Token Rotation: Revoke old refresh token jti so it cannot be reused
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, timezone.utc)
            UserRepository.revoke_token(conn, jti, user.id, expires_at)

        new_access_token = create_access_token(str(user.id))
        new_refresh_token = create_refresh_token(str(user.id))

        conn.commit()

        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    @staticmethod
    def logout(conn: psycopg.Connection, refresh_token_str: str) -> MessageResponse:
        try:
            payload = decode_token(refresh_token_str)
            jti = payload.get("jti")
            user_id = payload.get("sub")
            exp = payload.get("exp")

            if jti and user_id and exp:
                expires_at = datetime.fromtimestamp(exp, timezone.utc)
                UserRepository.revoke_token(conn, jti, UUID(user_id), expires_at)
                conn.commit()

        except (jwt.PyJWTError, ValueError):
            # If token is already malformed or expired, still treat logout as successful
            pass

        return MessageResponse(message="Logged out successfully")

    @staticmethod
    def forgot_password(
        conn: psycopg.Connection,
        email: str,
        background_tasks: BackgroundTasks
    ) -> MessageResponse:
        user = UserRepository.get_by_email(conn, email.strip())
        if user and user.is_active:
            # 1. Invalidate any existing unused OTPs
            UserRepository.invalidate_previous_otps(conn, user.id)

            # 2. Generate 6-digit numeric OTP
            otp_code = f"{secrets.randbelow(900000) + 100000}"
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

            # 3. Save OTP in database
            UserRepository.create_password_reset_otp(conn, user.id, otp_code, expires_at)
            conn.commit()

            # 4. Dispatch email sending in background task
            background_tasks.add_task(send_otp_email, user.email, otp_code, user.name)

        # Always return generic message to prevent email enumeration
        return MessageResponse(
            message="If your email is registered in our system, a 6-digit OTP code has been sent."
        )

    @staticmethod
    def reset_password(
        conn: psycopg.Connection,
        data: ResetPasswordRequest
    ) -> MessageResponse:
        user = UserRepository.get_by_email(conn, data.email.strip())
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email or OTP code"
            )

        otp_record = UserRepository.get_valid_otp(conn, user.id, data.otp.strip())
        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP code"
            )

        # Mark OTP as used
        UserRepository.mark_otp_used(conn, otp_record["id"])

        # Update password
        new_hashed = hash_password(data.new_password)
        UserRepository.update_password(conn, user.id, new_hashed)

        conn.commit()

        return MessageResponse(
            message="Password has been successfully reset. You can now log in with your new password."
        )
