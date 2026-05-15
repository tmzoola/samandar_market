from pydantic import BaseModel, ConfigDict
from typing import Optional
from models.organization import OrgStatus


class OrganizationResponse(BaseModel):
    id: int
    name_uz: str
    name_ru: Optional[str]
    tin: str
    address: Optional[str]
    director_name: Optional[str]
    status: OrgStatus

    model_config = ConfigDict(from_attributes=True)
