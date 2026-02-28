"""Kafka producer wrapper with DLQ support."""

import time

import structlog
from confluent_kafka import KafkaException, Producer

from producer.config import Settings
from producer.models import BinanceTrade, DLQMessage

log = structlog.get_logger()


class KafkaClient:
    def __init__(self, settings: Settings) -> None:
        self._topic = settings.kafka_topic
        self._dlq_topic = settings.kafka_dlq_topic
        self._flush_every = settings.kafka_flush_every
        self._produced = 0
        self._producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "acks": "all",
                "retries": 5,
                "retry.backoff.ms": 500,
            }
        )

    def produce_trade(self, trade: BinanceTrade) -> None:
        payload = trade.model_dump_json().encode()
        self._producer.produce(
            self._topic,
            key=trade.symbol.encode(),
            value=payload,
            on_delivery=self._delivery_report,
        )
        self._produced += 1
        if self._produced % self._flush_every == 0:
            self._producer.poll(0)

    def produce_dlq(self, raw: str, error: str) -> None:
        msg = DLQMessage(
            raw_payload=raw,
            error=error,
            ingestion_time_ms=time.time_ns() // 1_000_000,
        )
        self._producer.produce(
            self._dlq_topic,
            value=msg.model_dump_json().encode(),
            on_delivery=self._delivery_report,
        )
        self._producer.poll(0)

    def flush(self) -> None:
        remaining = self._producer.flush(timeout=10)
        if remaining:
            log.warning("kafka.flush_incomplete", remaining=remaining)

    @staticmethod
    def _delivery_report(err: KafkaException | None, msg: object) -> None:
        if err:
            log.error("kafka.delivery_failed", error=str(err))
        else:
            log.debug("kafka.delivered", topic=msg.topic(), partition=msg.partition(), offset=msg.offset())
