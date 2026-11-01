from uuid import UUID
from fastapi import HTTPException, status
import jwt
import psycopg
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenRefreshResponse, TokenResponse
from app.schemas.user import UserResponse
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

        new_access_token = create_access_token(str(user.id))
        new_refresh_token = create_refresh_token(str(user.id))

        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
