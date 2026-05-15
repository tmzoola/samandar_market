import json
import logging
import uuid
from abc import ABC, abstractmethod

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient
from core.config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MessagePublisher(ABC):
    """Abstract base class for message publishers."""

    @abstractmethod
    async def publish(
        self, topic: str, type: str, created_at: str, payload: dict, aggregate_id: str
    ) -> None:
        """Publish a message to the specified topic."""
        raise NotImplementedError("This method should be implemented by subclasses.")

    @abstractmethod
    async def check_kafka_cluster_health(self) -> bool:
        """Check the health of the Kafka cluster."""
        raise NotImplementedError("This method should be implemented by subclasses.")


class KafkaPublisher(MessagePublisher):
    def __init__(
        self,
        bootstrap_servers: str,
        username: str | None = None,
        password: str | None = None,
        sasl_mechanism: str = "PLAIN",  # or "SCRAM-SHA-256", "SCRAM-SHA-512"
        security_protocol: str = "SASL_PLAINTEXT",  # or "SASL_SSL"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.username = username
        self.password = password
        self.sasl_mechanism = sasl_mechanism
        self.security_protocol = security_protocol
        self._producer = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
        )
        await self._producer.start()

    async def stop(self):
        if self._producer:
            await self._producer.stop()

    async def publish(
        self, topic: str, type: str, created_at: str, payload: dict, aggregate_id: str
    ):
        headers = [
            ("eventType", type.encode("utf-8")),
            ("recordTime", created_at.encode("utf-8")),
            ("id", str(uuid.uuid4()).encode("utf-8")),
        ]
        payload = json.dumps(payload).encode("utf-8")
        if not self._producer:
            raise RuntimeError("Kafka producer is not started")
        await self._producer.send_and_wait(
            topic=topic,
            headers=headers,
            value=payload,
            key=aggregate_id.encode("utf-8"),
        )

    async def check_kafka_cluster_health(self) -> bool:
        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers,
            security_protocol=self.security_protocol,
            sasl_mechanism=self.sasl_mechanism,
            sasl_plain_username=self.username,
            sasl_plain_password=self.password,
        )
        try:
            await admin_client.start()
            await admin_client.list_topics()
            logger.info(f"Kafka is reachable")
            return True
        except Exception as e:
            logger.error(f"Error checking Kafka cluster health: {e}")
            return False
        finally:
            await admin_client.close()


publisher = KafkaPublisher(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    username=settings.KAFKA_USERNAME,
    password=settings.KAFKA_PASSWORD,
    # sasl_mechanism="PLAIN",  # or SCRAM-SHA-256 / SCRAM-SHA-512
    security_protocol="PLAINTEXT",  # or SASL_PLAINTEXT
)
