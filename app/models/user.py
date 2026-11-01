from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class User:
    id: UUID
    name: str
    email: str
    username: str
    password: str
    avatar: Optional[str] = None
    level: int = 1
    is_active: bool = True
    is_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
