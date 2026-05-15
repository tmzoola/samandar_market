from models.organization import Organization
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class OrganizationRepository:
    """
    Organization Repository Implementation Class
    This class implements the UserRepositoryABC interface and provides methods
    for user-related database operations.
    """

    def __init__(self, session: AsyncSession, model=Organization) -> None:
        self.session = session
        self.model = model

    async def add(self, organization: Organization) -> Organization:
        self.session.add(organization)
        await self.session.flush()
        await self.session.refresh(organization)
        return organization

    async def get_org_by_tin(self, tin: str) -> Organization | None:
        """
        Get a organization by their TIN.
        :param tin: The TIN of the organization to retrieve.
        :return: The organization object if found, otherwise None.
        """
        stmt = select(Organization).where(Organization.tin == tin)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()