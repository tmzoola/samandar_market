import uuid
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import jwt
from fastapi import HTTPException, status

from .config import settings
from .redis import redis_client

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")


def create_access_token(userId: int, userPinfl: str) -> str:
    expire = datetime.now(TASHKENT_TZ) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    jti = str(uuid.uuid4())

    payload = {
        "user_id": str(userId),
        "user_pinfl": str(userPinfl),
        "jti": jti,
        "exp": expire,
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")


async def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        jti = payload.get("jti")
        if jti:
            is_blacklisted = await redis_client.get(f"blacklist:{jti}")
            if is_blacklisted:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been invalidated (logged out).",
                )

        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=TASHKENT_TZ) < datetime.now(
            TASHKENT_TZ
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def logout(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        jti = payload.get("jti")
        exp = payload.get("exp")

        now_ts = datetime.now(TASHKENT_TZ).timestamp()
        ttl = int(exp - now_ts)
        if ttl <= 0:
            ttl = 1

        await redis_client.setex(f"blacklist:{jti}", ttl, "true")

        return {"message": "Logged out successfully"}

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
