from abc import ABC, abstractmethod

from schemas.gateway import (
    FetchOrgDistrictResponse,
    OrgAccountNumbersList,
    UserJobDetailResponse,
    UserPassportInfoResponse,
    UserPersonalInfoResponse,
)
from schemas.sso import SsoSuccessResponse, SsoUserInfoResponse


class SsoClientABC(ABC):
    """
    Sso client Interface Class
    """

    @abstractmethod
    async def get_access_token(
        self, code: str, codeVerify: str, redirectUri: str
    ) -> SsoSuccessResponse:
        """
        Get access token using the provided code and redirect URI.
        """
        raise NotImplementedError("Method get_access_token must be implemented.")

    @abstractmethod
    async def get_user_info(self, accessToken: str) -> SsoUserInfoResponse:
        """
        Get user information from sso
        """
        raise NotImplementedError("Method get_user_info must be implemented.")


class GatewayClientABC(ABC):
    @abstractmethod
    async def get_access_token(
        self, grantType: str, username: str, password: str
    ) -> str:
        """
        Get access token using the provided grant type, username, and password.
        """
        raise NotImplementedError("Method get_access_token must be implemented.")

    @abstractmethod
    async def get_user_job_detail(
        self, accessToken: str, pinfl: str
    ) -> UserJobDetailResponse:
        """
        Get user position using the provided access token and pinfl.
        """
        raise NotImplementedError("Method get_user_job_detail must be implemented.")

    @abstractmethod
    async def get_user_personal_info(
        self, accessToken: str, pinfl: str, birthDate: str
    ) -> UserPersonalInfoResponse:
        """
        Get user personal information using the provided access token.
        """
        raise NotImplementedError("Method get_user_personal_info must be implemented.")

    @abstractmethod
    async def get_user_passport_info(
        self, accessToken: str, pinfl: str
    ) -> UserPassportInfoResponse:
        """
        Get user passport information using the provided access token.
        """
        raise NotImplementedError("Method get_user_passport_info must be implemented.")

    @abstractmethod
    async def get_org_account_numbers(
        self, accessToken: str, tin: str
    ) -> OrgAccountNumbersList:
        """
        Get organization account numbers by organization TIN.
        :param tin: TIN of the organization.
        :return: List of OrganizationAccountNumber objects.
        """
        raise NotImplementedError("Method get_org_account_numbers must be implemented.")

    @abstractmethod
    async def fetch_org_district(
        self, accessToken: str, tin: str
    ) -> FetchOrgDistrictResponse:
        """
        Fetch organization district by organization TIN.
        :param tin: TIN of the organization.
        :return: District of the organization as a string.
        """
        raise NotImplementedError("Method fetch_org_district must be implemented.")
