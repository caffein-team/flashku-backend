from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    name: str
    email: EmailStr
    username: str
    avatar: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    level: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="New full name")
    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="New alphanumeric username"
    )


class AvatarUploadResponse(BaseModel):
    message: str = "Avatar uploaded successfully"
    avatar_url: str
    user: UserResponse


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password min 6 chars")


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Confirm your password to proceed with account deletion")


class MessageResponse(BaseModel):
    message: str
