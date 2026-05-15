from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """
    User Repository Implementation Class
    This class implements the UserRepositoryABC interface and provides methods
    for user-related database operations.
    """

    def __init__(self, session: AsyncSession, model=User) -> None:
        self.session = session
        self.model = model

    async def add(self, user: User) -> User:
        """
        Add a new user to the database.
        :param user: User object to be added.
        :return: The added User object.
        """
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def get_user_by_pinfl(self, pinfl: str) -> User | None:
        """
        Get a user by their PINFL.
        :param pinfl: The PINFL of the user to retrieve.
        :return: The User object if found, otherwise None.
        """
        stmt = select(User).where(User.pinfl == pinfl)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()