"""Doctor authentication — register / login / me.

Credentials are stored in Neon (bcrypt-hashed); login returns a short-lived JWT
the frontend sends as ``Authorization: Bearer``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.auth.security import create_access_token, hash_password, verify_password
from app.config import Settings
from app.dependencies import current_user_id, settings_dep, users_dep

if TYPE_CHECKING:
    from app.db.users import UserRepository

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field("", max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


def _issue(user, settings: Settings) -> TokenResponse:
    token = create_access_token(
        user.id,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expire_minutes=settings.jwt_expire_minutes,
        extra={"email": user.email, "role": user.role},
    )
    return TokenResponse(access_token=token, user=user.public())


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    users: "UserRepository" = Depends(users_dep),
    settings: Settings = Depends(settings_dep),
) -> TokenResponse:
    if await users.get_by_email(payload.email):
        raise HTTPException(status_code=409, detail="email already registered")
    user = await users.create(payload.email, hash_password(payload.password), payload.name)
    return _issue(user, settings)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    users: "UserRepository" = Depends(users_dep),
    settings: Settings = Depends(settings_dep),
) -> TokenResponse:
    user = await users.get_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid email or password")
    return _issue(user, settings)


@router.get("/me")
async def me(
    user_id: str = Depends(current_user_id),
    users: "UserRepository" = Depends(users_dep),
) -> dict:
    user = await users.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user.public()
