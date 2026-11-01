import os
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import HTTPException, UploadFile, status
import psycopg
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import (
    AvatarUploadResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    MessageResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.utils.security import hash_password, verify_password

UPLOAD_DIR = Path("uploads/avatars")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class UserService:
    @staticmethod
    def update_profile(
        conn: psycopg.Connection,
        user_id: UUID,
        data: UpdateProfileRequest
    ) -> UserResponse:
        if data.username is not None:
            if UserRepository.is_username_taken(conn, data.username, user_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username is already taken by another user"
                )

        updated_user = UserRepository.update_profile(
            conn=conn,
            user_id=user_id,
            name=data.name,
            username=data.username
        )

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        conn.commit()
        return UserResponse.model_validate(updated_user)

    @classmethod
    async def upload_avatar(
        cls,
        conn: psycopg.Connection,
        current_user: UserResponse,
        file: UploadFile,
        base_url: str
    ) -> AvatarUploadResponse:
        # Validate content type
        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Validate file extension
        original_ext = Path(file.filename or "").suffix.lower()
        if original_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file extension"
            )

        # Read and validate size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum allowed limit of 5MB"
            )

        # Ensure upload directory exists
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Delete old avatar file if stored locally in uploads/avatars
        cls._delete_local_avatar_file(current_user.avatar)

        # Save new file
        filename = f"{current_user.id}_{uuid4().hex[:8]}{original_ext}"
        destination_path = UPLOAD_DIR / filename
        destination_path.write_bytes(content)

        # Build accessible URLs
        relative_path = f"/uploads/avatars/{filename}"
        full_avatar_url = f"{base_url.rstrip('/')}{relative_path}"

        # Update in database
        updated_user = UserRepository.update_avatar(
            conn=conn,
            user_id=current_user.id,
            avatar=full_avatar_url
        )

        conn.commit()

        return AvatarUploadResponse(
            message="Avatar uploaded successfully",
            avatar_url=full_avatar_url,
            user=UserResponse.model_validate(updated_user)
        )

    @classmethod
    def delete_avatar(
        cls,
        conn: psycopg.Connection,
        current_user: UserResponse
    ) -> UserResponse:
        cls._delete_local_avatar_file(current_user.avatar)

        updated_user = UserRepository.update_avatar(
            conn=conn,
            user_id=current_user.id,
            avatar=None
        )

        conn.commit()
        return UserResponse.model_validate(updated_user)

    @staticmethod
    def change_password(
        conn: psycopg.Connection,
        user_id: UUID,
        data: ChangePasswordRequest
    ) -> MessageResponse:
        user = UserRepository.get_by_id(conn, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(data.current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password does not match"
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password cannot be the same as the current password"
            )

        new_hashed = hash_password(data.new_password)
        UserRepository.update_password(conn, user_id, new_hashed)
        conn.commit()

        return MessageResponse(message="Password changed successfully")

    @classmethod
    def delete_account(
        cls,
        conn: psycopg.Connection,
        current_user: UserResponse,
        data: DeleteAccountRequest
    ) -> MessageResponse:
        user = UserRepository.get_by_id(conn, current_user.id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if not verify_password(data.password, user.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password confirmation is incorrect"
            )

        # Remove local avatar file if exists
        cls._delete_local_avatar_file(current_user.avatar)

        # Delete user record from database
        UserRepository.delete(conn, current_user.id)
        conn.commit()

        return MessageResponse(message="Account successfully deleted")

    @staticmethod
    def _delete_local_avatar_file(avatar_url: str | None):
        if not avatar_url:
            return
        if "/uploads/avatars/" in avatar_url:
            filename = avatar_url.split("/uploads/avatars/")[-1].split("?")[0]
            local_path = UPLOAD_DIR / filename
            if local_path.is_file():
                try:
                    os.remove(local_path)
                except OSError:
                    pass
