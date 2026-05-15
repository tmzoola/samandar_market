from typing import Annotated

from clients.gateway import GatewayClient
from clients.ports import GatewayClientABC
from fastapi import Depends


def get_gateway_client() -> GatewayClientABC:
    return GatewayClient()


GatewayClientDep = Annotated[GatewayClientABC, Depends(get_gateway_client)]
