from pydantic import BaseModel


class UserJobPositionDetail(BaseModel):
    orgTin: str
    organizationName: str
    positionName: str
    departmentName: str
    beginDate: str
    rate: str


class UserJobDetailResponse(BaseModel):
    pinfl: str
    jobPositions: list[UserJobPositionDetail]


class UserPersonalInfoResponse(BaseModel):
    photo: str
    pinfl: str
    surnameLatin: str
    docSeria: str
    docNumber: str
    nameLatin: str
    patronymLatin: str | None = None
    birthDate: str
    birthPlace: str | None = None
    liveStatus: int
    sex: int
    docGivePlace: str
    docDateBegin: str
    docDateEnd: str | None = None


class UserPassportInfoResponse(BaseModel):
    pinfl: str
    birthDate: str | None = None
    genderCode: int | None = None
    firstName: str | None = None
    fullName: str
    liveStatus: int | None = None
    lastName: str | None = None
    middleName: str | None = None
    birthPlace: str | None = None
    passportSeriaNumber: str | None = None
    passportGivenBy: str | None = None
    passportGivenDate: str | None = None


class OrgAccountNumbersList(BaseModel):
    accountNumbers: list[str]


class OrgAccountCheckRequest(BaseModel):
    tin: str
    accountNumber: str


class OrgAccountCheckResponse(BaseModel):
    tin: str
    accountNumber: str
    exists: bool


class FetchOrgDistrictResponse(BaseModel):
    parentOrgTin: str | None = None
    districtCode: int
    orgName: str
