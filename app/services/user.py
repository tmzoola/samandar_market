from clients.sso import SsoClient
from core.exceptions import NotFoundException
from core.security import create_access_token
from schemas.user import UserOneIdResponse
from uow.ports import UnitOfWorkABC


class UserService:
    def __init__(self, uow: UnitOfWorkABC, ssoClient: SsoClient):
        self.uow = uow
        self.ssoClient = ssoClient

    async def get_user_by_pinfl(self, pinfl: str):
        async with self.uow:
            user = await self.uow.user.get_user_by_pinfl(pinfl)
            if not user:
                raise NotFoundException(detail=f"Pinfl {pinfl} bo'yicha xodim topilmadi")
            return user

    async def one_id(
        self,
        code: str,
        codeVerify: str,
        redirectUri: str,
    ) -> UserOneIdResponse:
        ssoRes = await self.ssoClient.get_access_token(code, codeVerify, redirectUri)
        userInfo = await self.ssoClient.get_user_info(ssoRes.accessToken)

        async with self.uow:
            user = await self.uow.user.get_user_by_pinfl(userInfo.pinfl)
            if not user:
                raise NotFoundException(
                    detail=f"Taqiqlangan! Xodim {userInfo.firstName} {userInfo.lastName} tizimda mavjud emas"
                )

            token = create_access_token(userId=user.id, userPinfl=user.pinfl)

        return UserOneIdResponse(accessToken=token, ssoToken=ssoRes.accessToken)