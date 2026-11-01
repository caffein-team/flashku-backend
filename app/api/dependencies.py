from collections.abc import Generator
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
import psycopg
from app.database.connection import get_connection
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse
from app.utils.security import decode_token

security = HTTPBearer()


def get_db() -> Generator[psycopg.Connection, None, None]:
    with get_connection() as conn:
        try:
            yield conn
        finally:
            conn.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    conn: psycopg.Connection = Depends(get_db)
) -> UserResponse:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        token_type = payload.get("type")
        user_id = payload.get("sub")
        if token_type != "access" or not user_id:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = UserRepository.get_by_id(conn, user_uuid)
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )

    return UserResponse.model_validate(user)
