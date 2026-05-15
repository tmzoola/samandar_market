from clients.ports import GatewayClientABC
from core.exceptions import NotFoundException
from uow.ports import UnitOfWorkABC


class OrganizationService:
    def __init__(
        self,
        uow: UnitOfWorkABC,
        gateway_client: GatewayClientABC,
    ):
        self.uow = uow
        self.gateway_client = gateway_client

    async def get_org_by_tin(self, tin: str):
        async with self.uow:
            organization = await self.uow.organization.get_org_by_tin(tin=tin)
            if not organization:
                raise NotFoundException(detail=f"TIN {tin} bo'yicha tashkilot topilmadi")
            return organization
