from typing import Annotated

from core.kafka_publisher import MessagePublisher
from dependencies.uow import UowDependency
from fastapi import Depends
from services.out import HybridOutBoxService, OutBoxService
from services.ports import OutBoxServiceABC


def get_publisher() -> MessagePublisher:
    from main import app

    return app.state.publisher


PublisherDependency = Annotated[MessagePublisher, Depends(get_publisher)]


def get_outbox_service(
    uow: UowDependency, publisher: PublisherDependency
) -> OutBoxServiceABC:
    return OutBoxService(uow=uow, publisher=publisher)


def get_hybrid_outbox_service(
    uow: UowDependency, publisher: PublisherDependency
) -> HybridOutBoxService:
    return HybridOutBoxService(uow=uow, publisher=publisher)


OutBoxServiceDep = Annotated[OutBoxServiceABC, Depends(get_outbox_service)]
HybridOutBoxServiceDep = Annotated[
    HybridOutBoxService, Depends(get_hybrid_outbox_service)
]
