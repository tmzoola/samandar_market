from typing import Annotated

from dependencies.user import RequestUserDep
from fastapi import Depends, HTTPException
from models.role import Role, RoleKey
from models.user import User


def get_hr_user(user: RequestUserDep) -> User:
    if RoleKey.HR == user.currentRole.key:
        return user
    raise HTTPException(403, "Request user is not HR")


HRUserDep = Annotated[User, Depends(get_hr_user)]
