"""User repository — Postgres (asyncpg) and in-memory implementations."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Protocol

from app.db.models import User


class UserRepository(Protocol):
    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_id(self, user_id: str) -> User | None: ...
    async def create(self, email: str, password_hash: str, name: str) -> User: ...


class InMemoryUserRepository:
    """Dev/test fallback when no database is configured."""

    def __init__(self) -> None:
        self._by_id: dict[str, User] = {}
        self._by_email: dict[str, User] = {}

    async def get_by_email(self, email: str) -> User | None:
        return self._by_email.get(email.lower())

    async def get_by_id(self, user_id: str) -> User | None:
        return self._by_id.get(user_id)

    async def create(self, email: str, password_hash: str, name: str) -> User:
        user = User(
            id=str(uuid.uuid4()),
            email=email.lower(),
            password_hash=password_hash,
            name=name,
            created_at=datetime.now(timezone.utc),
        )
        self._by_id[user.id] = user
        self._by_email[user.email] = user
        return user


class PgUserRepository:
    """asyncpg-backed user store (Neon/Postgres)."""

    def __init__(self, pool) -> None:
        self._pool = pool

    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=str(row["id"]),
            email=row["email"],
            password_hash=row["password_hash"],
            name=row["name"],
            role=row["role"],
            created_at=row["created_at"],
        )

    async def get_by_email(self, email: str) -> User | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email.lower())
        return self._row_to_user(row) if row else None

    async def get_by_id(self, user_id: str) -> User | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", uuid.UUID(user_id))
        return self._row_to_user(row) if row else None

    async def create(self, email: str, password_hash: str, name: str) -> User:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, name)
                VALUES ($1, $2, $3)
                RETURNING *
                """,
                email.lower(),
                password_hash,
                name,
            )
        return self._row_to_user(row)
