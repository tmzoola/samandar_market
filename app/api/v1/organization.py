from fastapi import APIRouter
from dependencies.org import OrgServiceDep
from schemas.organization import OrganizationResponse

router = APIRouter(prefix="/organizations", tags=["Organization"])


@router.get("/{tin}", response_model=OrganizationResponse)
async def get_organization_by_tin(
    tin: str,
    service: OrgServiceDep,
):
    return await service.get_org_by_tin(tin)