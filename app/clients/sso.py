import json

import httpx
from clients.ports import SsoClientABC
from core.config import settings
from core.exceptions import BusinessException, CustomValidationException, ExternalServiceException
from schemas.sso import SsoSuccessResponse, SsoUserInfoResponse
from utils.http_client import get_http_client


# SSO Client implementation
class SsoClient(SsoClientABC):
    def __init__(self):
        self.client = get_http_client()
        self.base_url = settings.SSO_CLIENT_URL
        self.auth = (
            settings.SSO_CLIENT_ID,
            settings.SSO_CLIENT_SECRET,
        )

    # Override the get_access_token method from SsoClientABC
    async def get_access_token(
        self, code: str, codeVerify: str, redirectUri: str
    ) -> SsoSuccessResponse:
        # Implement the logic to get the access token here
        self.url = (
            f"{self.base_url}/oauth2/token"
            f"?redirect_uri={redirectUri}"
            f"&grant_type=authorization_code"
            f"&code={code}"
            f"&code_verifier={codeVerify}"
        )
        headers = {"Content-Type": "application/json"}

        try:
            response: httpx.Response = await self.client.post(
                url=self.url, data=json.dumps({}), headers=headers, auth=self.auth
            )
        except httpx.RequestError as e:
            raise ExternalServiceException(service="SSO", detail=f"SSO servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            raise CustomValidationException(
                detail=f"Xodim One Id tizimida token olishda xatolik:{response.text}"
            )
        resultData = SsoSuccessResponse(
            accessToken=response.json().get("access_token"),
        )
        return resultData

    async def get_user_info(self, accessToken: str) -> SsoUserInfoResponse:
        self.url = f"{self.base_url}/oauth2/introspect?token={accessToken}"
        headers = {"Content-Type": "application/json"}
        try:
            response: httpx.Response = await self.client.post(
                url=self.url, data=json.dumps({}), headers=headers, auth=self.auth
            )
        except httpx.RequestError as e:
            raise ExternalServiceException(service="SSO", detail=f"SSO servisiga ulanib bo'lmadi: {e}")
        if response.status_code != 200:
            raise CustomValidationException(
                detail=f"Xodim One Id tizimida xodim ma'lumotlarini olishda xatolik: {response.text}"
            )

        jsonData = response.json()
        if jsonData.get("active") is False:
            raise BusinessException(detail="Xodim One Id tizimida faol emas")
        resultData = SsoUserInfoResponse(
            firstName=jsonData.get("firstname"),
            lastName=jsonData.get("lastname"),
            pinfl=jsonData.get("pinfl"),
            birthDate=jsonData.get("birth_date"),
            passportSeriaNumber=jsonData.get("doc_serial_number"),
            patronymicName=jsonData.get("patronymic"),
            phoneNumber=jsonData.get("phone_number"),
            tin=jsonData.get("tin"),
        )
        return resultData
