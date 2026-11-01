from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
import psycopg
from app.database.queries import user_queries
from app.models.user import User


class UserRepository:
    @staticmethod
    def _map_row_to_user(row: Optional[Dict[str, Any]]) -> Optional[User]:
        if not row:
            return None
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            username=row["username"],
            password=row["password"],
            avatar=row.get("avatar"),
            level=row.get("level", 1),
            is_active=row.get("is_active", True),
            is_verified=row.get("is_verified", False),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )

    @classmethod
    def create(
        cls,
        conn: psycopg.Connection,
        name: str,
        email: str,
        username: str,
        hashed_password: str,
        avatar: Optional[str] = None
    ) -> User:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.CREATE_USER,
                {
                    "name": name,
                    "email": email,
                    "username": username,
                    "password": hashed_password,
                    "avatar": avatar,
                }
            )
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def get_by_id(cls, conn: psycopg.Connection, user_id: UUID) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(user_queries.GET_USER_BY_ID, {"id": user_id})
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def get_by_email(cls, conn: psycopg.Connection, email: str) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(user_queries.GET_USER_BY_EMAIL, {"email": email})
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def get_by_username(cls, conn: psycopg.Connection, username: str) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(user_queries.GET_USER_BY_USERNAME, {"username": username})
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def get_by_email_or_username(cls, conn: psycopg.Connection, identifier: str) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(user_queries.GET_USER_BY_EMAIL_OR_USERNAME, {"identifier": identifier})
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def is_username_taken(cls, conn: psycopg.Connection, username: str, exclude_user_id: UUID) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.CHECK_USERNAME_TAKEN,
                {"username": username, "id": exclude_user_id}
            )
            return cur.fetchone() is not None

    @classmethod
    def update_profile(
        cls,
        conn: psycopg.Connection,
        user_id: UUID,
        name: Optional[str] = None,
        username: Optional[str] = None
    ) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.UPDATE_USER_PROFILE,
                {
                    "id": user_id,
                    "name": name,
                    "username": username
                }
            )
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def update_avatar(
        cls,
        conn: psycopg.Connection,
        user_id: UUID,
        avatar: Optional[str] = None
    ) -> Optional[User]:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.UPDATE_USER_AVATAR,
                {
                    "id": user_id,
                    "avatar": avatar
                }
            )
            row = cur.fetchone()
            return cls._map_row_to_user(row)

    @classmethod
    def update_password(
        cls,
        conn: psycopg.Connection,
        user_id: UUID,
        hashed_password: str
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.UPDATE_USER_PASSWORD,
                {
                    "id": user_id,
                    "password": hashed_password
                }
            )

    @classmethod
    def delete(
        cls,
        conn: psycopg.Connection,
        user_id: UUID
    ) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.DELETE_USER,
                {"id": user_id}
            )
            return cur.rowcount > 0

    # --- OTP Password Reset ---
    @classmethod
    def create_password_reset_otp(
        cls,
        conn: psycopg.Connection,
        user_id: UUID,
        otp_code: str,
        expires_at: datetime
    ) -> UUID:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.INSERT_PASSWORD_RESET_OTP,
                {
                    "user_id": user_id,
                    "otp_code": otp_code,
                    "expires_at": expires_at,
                }
            )
            row = cur.fetchone()
            return row["id"]

    @classmethod
    def invalidate_previous_otps(cls, conn: psycopg.Connection, user_id: UUID) -> None:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.INVALIDATE_PREVIOUS_OTPS,
                {"user_id": user_id}
            )

    @classmethod
    def get_valid_otp(
        cls,
        conn: psycopg.Connection,
        user_id: UUID,
        otp_code: str
    ) -> Optional[Dict[str, Any]]:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.GET_VALID_OTP,
                {"user_id": user_id, "otp_code": otp_code}
            )
            return cur.fetchone()

    @classmethod
    def mark_otp_used(cls, conn: psycopg.Connection, otp_id: UUID) -> None:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.MARK_OTP_USED,
                {"id": otp_id}
            )

    # --- Token Revocation (Logout & Blacklist) ---
    @classmethod
    def revoke_token(
        cls,
        conn: psycopg.Connection,
        token_jti: str,
        user_id: UUID,
        expires_at: datetime
    ) -> None:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.REVOKE_TOKEN,
                {
                    "token_jti": token_jti,
                    "user_id": user_id,
                    "expires_at": expires_at,
                }
            )

    @classmethod
    def is_token_revoked(cls, conn: psycopg.Connection, token_jti: str) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                user_queries.IS_TOKEN_REVOKED,
                {"token_jti": token_jti}
            )
            return cur.fetchone() is not None
