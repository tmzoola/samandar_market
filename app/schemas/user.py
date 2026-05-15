from pydantic import BaseModel

class UserOneIdResponse(BaseModel):
    """
    Response model for user login via One ID.
    """

    accessToken: str
    ssoToken: str


class UserTokenRequestSchema(BaseModel):
    pinfl: str


class UserTokenResponseSchema(BaseModel):
    """
    Response model for user token generation.
    """

    accessToken: str


class UserOneIdRequest(BaseModel):
    """
    Request model for user login via One ID.
    """

    code: str
    codeVerify: str
    redirectUri: str
