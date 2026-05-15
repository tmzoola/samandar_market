from typing import Annotated

from clients.ports import SsoClientABC
from clients.sso import SsoClient
from dependencies.uow import UowDependency
from fastapi import Depends
from services.ports import RoleServiceABC
from services.role import EmployeeRoleService


def get_role_service(uow: UowDependency) -> RoleServiceABC:
    return EmployeeRoleService(uow=uow)


RoleServiceDep = Annotated[RoleServiceABC, Depends(get_role_service)]
