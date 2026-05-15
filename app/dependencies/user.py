import secrets
from typing import Annotated

from core.config import settings
from core.security import verify_access_token
from dependencies.sso import SsoClientDep
from dependencies.uow import UowDependency
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from models.user import User
from services.user import UserService



def get_user_service(
    uow: UowDependency,
    ssoClient: SsoClientDep,
):
    """
    Factory function to create an instance of UserService.
    """
    return UserService(
        uow=uow,
        ssoClient=ssoClient,
    )


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


security = HTTPBearer()


async def get_request_user(
    uow: UowDependency, credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    payload = await verify_access_token(token)

    if payload is None or "user_id" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    userId = int(payload["user_id"])

    async with uow:
        user = await uow.user.get_user_by_id(userId)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


RequestUserDep = Annotated[User, Depends(get_request_user)]


basic_security = HTTPBasic()


async def get_basic_auth_user(
    credentials: HTTPBasicCredentials = Depends(basic_security),
) -> str:
    correctUsername = secrets.compare_digest(
        credentials.username, settings.INTERNAL_USERNAME
    )
    correctPassword = secrets.compare_digest(
        credentials.password, settings.INTERNAL_PASSWORD
    )
    if not (correctUsername and correctPassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


BasicAuthUserDep = Annotated[str, Depends(get_basic_auth_user)]
