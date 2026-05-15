import json
import logging

import httpx
from clients.ports import GatewayClientABC
from core.config import settings
from core.exceptions import BusinessException, CustomValidationException, ExternalServiceException
from schemas.gateway import (
    FetchOrgDistrictResponse,
    OrgAccountNumbersList,
    UserJobDetailResponse,
    UserJobPositionDetail,
    UserPassportInfoResponse,
    UserPersonalInfoResponse,
)
from utils.http_client import get_http_client

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class GatewayClient(GatewayClientABC):
    def __init__(self):
        self.client = get_http_client()
        self.base_url = settings.GATEWAY_CLIENT_URL
        self.auth = (
            settings.GATEWAY_CLIENT_ID,
            settings.GATEWAY_CLIENT_SECRET,
        )
        self.grant_type = settings.GATEWAY_CLIENT_GRANT_TYPE

    async def get_access_token(
        self, grantType: str, username: str, password: str
    ) -> str:
        """
        Get access token using the provided grant type, username, and password.
        """
        self.url = f"{self.base_url}/api/v1/auth/token"
        headers = {"Content-Type": "application/json"}
        data = {
            "grant_type": grantType,
            "username": username,
            "password": password,
        }

        try:
            response = await self.client.post(url=self.url, json=data, headers=headers)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to get access token: {response.status_code} {response.text}"
            )
            raise CustomValidationException(
                detail=f"Failed to get access token: {response.text}"
            )

        return response.json().get("access_token")

    async def get_user_job_detail(
        self, accessToken: str, pinfl: str
    ) -> UserJobDetailResponse:
        """
        Get user job details using the provided access token and pinfl.
        """
        self.url = f"{self.base_url}/api/v1/egov/current-citizen"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }
        data = json.dumps({"pinfl": pinfl})

        try:
            response = await self.client.post(url=self.url, headers=headers, data=data)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to get user job detail: {response.status_code} {response.text}"
            )
            raise CustomValidationException(
                detail=f"Failed to get user job detail: {response.text}"
            )
        error = response.json().get("error")
        if error:
            raise BusinessException(
                detail=f"Sizningizning ish joyingiz topilmadi: {error.get('message', 'No message provided')}"
            )
        result = response.json()["result"]
        positions = [] if not result["positions"] else result["positions"]
        userPositions = [
            UserJobPositionDetail(
                orgTin=position["org_tin"],
                organizationName=position["org"],
                positionName=position["position"],
                departmentName=position["dep_name"],
                beginDate=position["begin_date"],
                rate=position["rate"],
            )
            for position in positions
        ]
        jobDetail = UserJobDetailResponse(
            pinfl=result["pnfl"], jobPositions=userPositions
        )
        return jobDetail

    async def get_user_personal_info(
        self, accessToken: str, pinfl: str, birthDate: str
    ) -> UserPersonalInfoResponse:
        """
        Get user personal information using the provided access token.
        """
        self.url = f"{self.base_url}/api/v1/egov/passport-gcp-birth-date"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }
        data = json.dumps({"pinfl": pinfl, "birthDate": birthDate})
        logger.info(f"get_user_personal_info data:{data}")

        try:
            response = await self.client.post(url=self.url, headers=headers, data=data)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to get user personal info: {response.status_code} {response.text} {data}"
            )
            raise CustomValidationException(
                detail=f"Failed to get user personal info: {response.text}"
            )

        return UserPersonalInfoResponse(**response.json())

    async def get_user_passport_info(
        self, accessToken: str, pinfl: str
    ) -> UserPassportInfoResponse:
        """
        Get user passport information using the provided access token.
        """
        self.url = f"{self.base_url}/api/v1/passport/by-pinfl-v1"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
            "no-cache": "true",
        }
        data = json.dumps({"pinfl": pinfl})

        try:
            response = await self.client.post(url=self.url, headers=headers, data=data)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to get user passport info: {response.status_code} {response.text}"
            )
            raise CustomValidationException(
                detail=f"Failed to get user passport info: {response.text}"
            )
        jsonData = response.json()
        resData = UserPassportInfoResponse(
            pinfl=str(jsonData.get("pinfl")),
            fullName=f"{jsonData.get('firstName')} {jsonData.get('lastName')} {jsonData.get('middleName', '')}",
            liveStatus=jsonData.get("liveStatus"),
            birthDate=jsonData.get("birthDate"),
            genderCode=jsonData.get("genderCode"),
            firstName=jsonData.get("firstName"),
            lastName=jsonData.get("lastName"),
            middleName=jsonData.get("middleName"),
            birthPlace=jsonData.get("birthPlace") or None,
            passportSeriaNumber=jsonData["document"].get("document"),
            passportGivenBy=jsonData["document"].get("givePlace"),
            passportGivenDate=jsonData["document"].get("beginDate"),
        )
        return resData

    async def get_org_account_numbers(
        self, accessToken: str, tin: str
    ) -> OrgAccountNumbersList:
        """
        Get organization account numbers using the provided access token and organization tin.
        """
        self.url = f"{self.base_url}/api/v1/uzasbo/treas-info"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }
        data = json.dumps({"tin": tin})

        try:
            response = await self.client.post(url=self.url, headers=headers, data=data)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to get organization account numbers: {response.status_code} {response.text}"
            )
            raise CustomValidationException(
                detail=f"Failed to get organization account numbers: {response.text}"
            )
        jsonData = response.json()
        resData = OrgAccountNumbersList(
            accountNumbers=[item["code"] for item in jsonData]
        )
        return resData

    async def fetch_org_district(
        self, accessToken: str, tin: str
    ) -> FetchOrgDistrictResponse:
        """
        Fetch organization district information using the provided access token and organization tin.
        """
        self.url = f"{self.base_url}/api/v1/tax/org"
        headers = {
            "Authorization": f"Bearer {accessToken}",
            "Content-Type": "application/json",
        }
        params = {"tin": tin}

        try:
            response = await self.client.get(url=self.url, headers=headers, params=params)
        except httpx.RequestError as e:
            raise ExternalServiceException(service="Gateway", detail=f"Gateway servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            logger.error(
                f"Failed to fetch organization district: {response.status_code} {response.text}"
            )
            raise CustomValidationException(
                detail=f"Failed to fetch organization district: {response.text}"
            )
        parentOrgTin = None
        jsonData = response.json()
        districtCode = jsonData["companyBillingAddress"]["soatoCode"]
        orgName = jsonData["company"]["name"]
        founders = jsonData.get("founders", [])
        if founders:
            firstFounder = founders[0].get("founderLegal")
            if firstFounder:
                parentOrgTin = firstFounder.get("tin")
        resData = FetchOrgDistrictResponse(
            parentOrgTin=parentOrgTin, districtCode=districtCode, orgName=orgName
        )
        return resData
