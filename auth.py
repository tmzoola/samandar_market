"""Admin authentication helpers — bcrypt passwords, JWT cookies."""

from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, Depends, HTTPException, Request, Response, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_session
from models import Admin

log = logging.getLogger("auth")

ADMIN_COOKIE_NAME = "pos_admin_token"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def _resolve_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    # Generate a per-process random secret so dev still works out of the box.
    # NOTE: every restart invalidates existing admin sessions in this mode.
    generated = secrets.token_urlsafe(48)
    log.warning(
        "JWT_SECRET is not set — using an ephemeral random secret. "
        "Set JWT_SECRET in .env to keep admin sessions across restarts."
    )
    return generated


JWT_SECRET = _resolve_secret()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_admin_token(admin_id: int) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {"sub": str(admin_id), "exp": expires}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def set_admin_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ADMIN_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
        path="/",
    )


def clear_admin_cookie(response: Response) -> None:
    response.delete_cookie(key=ADMIN_COOKIE_NAME, path="/")


async def get_current_admin(
    pos_admin_token: str | None = Cookie(default=None, alias=ADMIN_COOKIE_NAME),
    db: AsyncSession = Depends(get_session),
) -> Admin:
    if not pos_admin_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(pos_admin_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        admin_id = int(payload.get("sub", 0))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if admin_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(Admin).where(Admin.id == admin_id))
    admin = result.scalar_one_or_none()
    if admin is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    return admin
