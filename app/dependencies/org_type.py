from typing import Annotated

from dependencies.uow import UowDependency
from fastapi import Depends
from services.org_type import OrganizationTypeService


def get_organization_type_service(uow: UowDependency) -> OrganizationTypeService:
    """
    Factory function to create an instance of RegionService
    """
    return OrganizationTypeService(uow=uow)


OrganizationTypeServiceDep = Annotated[
    OrganizationTypeService, Depends(get_organization_type_service)
]
