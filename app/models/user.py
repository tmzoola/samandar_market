import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class GenderType(enum.Enum):
    Male = "Male"
    Female = "Female"


class User(Base):
    """
    User model for the application.
    This model represents a user in the system.
    It inherits from Base, which is the base class for all models.
    """

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(
        "username", String, nullable=True, unique=True
    )
    userUuid: Mapped[uuid.UUID] = mapped_column(
        "user_uuid",
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    password: Mapped[str] = mapped_column("password", String, nullable=True)
    isSuperuser: Mapped[bool] = mapped_column("is_superuser", Boolean, default=False)
    pinfl: Mapped[str] = mapped_column("pinfl", String, nullable=False)
    firstName: Mapped[str] = mapped_column("first_name", String, nullable=False)
    lastName: Mapped[str] = mapped_column("last_name", String, nullable=False)
    fullName: Mapped[str] = mapped_column("full_name", String, nullable=False)
    middleName: Mapped[str] = mapped_column("middle_name", String, nullable=True)
    gender: Mapped[GenderType] = mapped_column(Enum(GenderType), nullable=True)
    birthDate: Mapped[str] = mapped_column("birth_date", String, nullable=True)
    phoneNumber: Mapped[str] = mapped_column("phone_number", String, nullable=True)
    passportSeriaNumber: Mapped[str] = mapped_column(
        "passport_seria_number", String, nullable=True
    )
    passportGivenBy: Mapped[str] = mapped_column(
        "passport_given_by", String, nullable=True
    )
    passportGivenDate: Mapped[str] = mapped_column(
        "passport_given_date", String, nullable=True
    )
    passportImage: Mapped[str] = mapped_column("passport_image", String, nullable=True)

    def __str__(self):
        return self.fullName
