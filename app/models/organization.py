from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column
import enum
from .base import Base


class OrgStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    NOT_ACTIVE = "NOT_ACTIVE"


class Organization(Base):
    __tablename__ = "organizations"

    name_uz: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ru: Mapped[str | None] = mapped_column(String(255))
    tin: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    director_name: Mapped[str | None] = mapped_column(String(255))

    status: Mapped[OrgStatus] = mapped_column(
        Enum(OrgStatus, name="org_status"),
        nullable=False,
        default=OrgStatus.ACTIVE,
    )

    def __str__(self):
        return self.name_uz

    def __repr__(self):
        return f"<Organization tin={self.tin} name={self.name_uz}>"
