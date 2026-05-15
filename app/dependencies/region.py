from typing import Annotated

from dependencies.uow import UowDependency
from fastapi import Depends
from services.region import RegionService


def get_region_service(uow: UowDependency) -> RegionService:
    """
    Factory function to create an instance of RegionService
    """
    return RegionService(uow=uow)


RegionServiceDep = Annotated[RegionService, Depends(get_region_service)]
