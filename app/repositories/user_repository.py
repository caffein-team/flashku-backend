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
