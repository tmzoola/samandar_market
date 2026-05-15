from typing import Annotated

from clients.ports import SsoClientABC
from clients.sso import SsoClient
from fastapi import Depends


def get_sso_client() -> SsoClientABC:
    return SsoClient()


SsoClientDep = Annotated[SsoClientABC, Depends(get_sso_client)]
