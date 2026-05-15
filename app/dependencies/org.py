from typing_extensions import Annotated
from fastapi import Depends

from dependencies.gateway import GatewayClientDep
from dependencies.uow import UowDependency
from services.organization import OrganizationService


def get_org_service(
    uow: UowDependency,
    gateway_client: GatewayClientDep,
) -> OrganizationService:
    return OrganizationService(
        uow=uow,
        gateway_client=gateway_client,
    )


OrgServiceDep = Annotated[OrganizationService, Depends(get_org_service)]
