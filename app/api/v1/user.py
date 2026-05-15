from fastapi import APIRouter
from dependencies.user import UserServiceDep
from schemas.user import UserOneIdResponse, UserOneIdRequest

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/{pinfl}")
async def get_user_by_pinfl(pinfl: str, service: UserServiceDep):
    return await service.get_user_by_pinfl(pinfl)


@router.post("/oneId/", response_model=UserOneIdResponse)
async def one_id(
    params: UserOneIdRequest, service: UserServiceDep
) -> UserOneIdResponse:
    """
    Endpoint to handle user login via One ID.
    """
    userServiceResult = await service.one_id(
        code=params.code,
        codeVerify=params.codeVerify,
        redirectUri=params.redirectUri,
    )
    return userServiceResult