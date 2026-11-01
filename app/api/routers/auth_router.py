from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
import psycopg
from app.api.dependencies import get_current_user, get_db
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenRefreshResponse,
    TokenResponse,
)
from app.schemas.user import MessageResponse, UserResponse
from app.services.auth_service import AuthService
from app.utils.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Max 10 req/min)"
)
@limiter.limit("10/minute")
def register(
    request: Request,
    data: RegisterRequest,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.register(conn=conn, data=data)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login with identifier and password (Max 5 req/min)"
)
@limiter.limit("5/minute")
def login(
    request: Request,
    data: LoginRequest,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.login(conn=conn, data=data)


@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token using a valid refresh token (Max 30 req/min)"
)
@limiter.limit("30/minute")
def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.refresh(conn=conn, refresh_token_str=data.refresh_token)


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout user and revoke refresh token"
)
def logout(
    request: Request,
    data: LogoutRequest,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.logout(conn=conn, refresh_token_str=data.refresh_token)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Request OTP code for password reset via Gmail SMTP (Max 3 req/min)"
)
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.forgot_password(
        conn=conn,
        email=data.email,
        background_tasks=background_tasks
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password using received 6-digit OTP code (Max 5 req/min)"
)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    conn: psycopg.Connection = Depends(get_db)
):
    return AuthService.reset_password(conn=conn, data=data)


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current authenticated user profile"
)
def get_me(
    current_user: UserResponse = Depends(get_current_user)
):
    return current_user
