import json
from aiokafka import AIOKafkaProducer
from app.config import settings
from app.utils.logger import logger


class EventStreamProducer:


    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        if not settings.event_streaming_enabled:
            logger.info("Kafka event streaming devre dışı")
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode(),
        )
        await self._producer.start()
        logger.info(f"Kafka producer başlatıldı: {settings.kafka_bootstrap_servers}")

    async def publish(self, event: dict):
        if self._producer is None:
            return
        await self._producer.send_and_wait(settings.kafka_traffic_topic, event)

    async def stop(self):
        if self._producer is not None:
            await self._producer.stop()


event_stream_producer = EventStreamProducer()
