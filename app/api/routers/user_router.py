from fastapi import APIRouter, Depends, File, Request, UploadFile, status
import psycopg
from app.api.dependencies import get_current_user, get_db
from app.schemas.user import (
    AvatarUploadResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    MessageResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.patch(
    "/profile",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user's profile (name, username)"
)
def update_profile(
    data: UpdateProfileRequest,
    current_user: UserResponse = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db)
):
    return UserService.update_profile(
        conn=conn,
        user_id=current_user.id,
        data=data
    )


@router.post(
    "/avatar",
    response_model=AvatarUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload user avatar image to project storage"
)
async def upload_avatar(
    request: Request,
    file: UploadFile = File(..., description="Image file (jpg, png, webp, gif max 5MB)"),
    current_user: UserResponse = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db)
):
    base_url = str(request.base_url)
    return await UserService.upload_avatar(
        conn=conn,
        current_user=current_user,
        file=file,
        base_url=base_url
    )


@router.delete(
    "/avatar",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete current user's avatar"
)
def delete_avatar(
    current_user: UserResponse = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db)
):
    return UserService.delete_avatar(
        conn=conn,
        current_user=current_user
    )


@router.post(
    "/change-password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change user password"
)
def change_password(
    data: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db)
):
    return UserService.change_password(
        conn=conn,
        user_id=current_user.id,
        data=data
    )


@router.delete(
    "/account",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Permanently delete user account and uploaded assets"
)
def delete_account(
    data: DeleteAccountRequest,
    current_user: UserResponse = Depends(get_current_user),
    conn: psycopg.Connection = Depends(get_db)
):
    return UserService.delete_account(
        conn=conn,
        current_user=current_user,
        data=data
    )
