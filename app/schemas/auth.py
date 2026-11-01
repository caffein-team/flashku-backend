from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric username"
    )
    password: str = Field(..., min_length=6, max_length=128, description="Password min 6 chars")
    avatar: Optional[str] = Field(None, max_length=500, description="Optional avatar URL")


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="Email or Username")
    password: str = Field(..., min_length=1, description="Password")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered user email")


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered user email")
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit OTP code")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password min 6 chars")


class LogoutRequest(BaseModel):
    refresh_token: str = Field(..., description="Current refresh token to revoke")
