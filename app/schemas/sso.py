from pydantic import BaseModel, Field


class SsoSuccessResponse(BaseModel):
    accessToken: str


class SsoUserInfoResponse(BaseModel):
    firstName: str
    lastName: str
    pinfl: str
    birthDate: str
    passportSeriaNumber: str
    patronymicName: str | None
    phoneNumber: str | None
    tin: str | None
