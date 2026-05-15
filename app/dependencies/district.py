from typing import Annotated

from dependencies.uow import UowDependency
from fastapi import Depends
from services.district import DistrictService


def get_district_service(uow: UowDependency) -> DistrictService:
    """
    Factory function to create an instance of DistrictService
    """
    return DistrictService(uow=uow)


DistrictServiceDep = Annotated[DistrictService, Depends(get_district_service)]
