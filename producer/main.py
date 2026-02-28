"""Entry point for the Binance WebSocket → Kafka producer."""

import asyncio
import json
import signal

import structlog
from pydantic import ValidationError

from producer import health, ws_client
from producer.config import settings
from producer.kafka_client import KafkaClient
from producer.models import BinanceTrade

log = structlog.get_logger()


async def _run(kafka: KafkaClient, state: health.HealthState) -> None:
    state.set_ws_connected(False)
    stream = ws_client.stream(
        base_url=settings.binance_ws_url,
        symbols=settings.symbols_list(),
        reconnect_delay=settings.reconnect_delay_s,
        max_delay=settings.max_reconnect_delay_s,
    )

    async for raw in stream:
        # The combined stream wraps each event: {"stream": "...", "data": {...}}
        try:
            envelope = json.loads(raw)
            data = envelope.get("data", envelope)
            state.set_ws_connected(True)
        except json.JSONDecodeError as exc:
            log.error("producer.json_decode_error", error=str(exc), raw=raw[:200])
            kafka.produce_dlq(raw, f"JSONDecodeError: {exc}")
            state.increment_dlq()
            continue

        try:
            trade = BinanceTrade.model_validate(data)
            kafka.produce_trade(trade)
            state.increment_produced()
            log.debug(
                "producer.trade",
                symbol=trade.symbol,
                price=trade.price,
                qty=trade.quantity,
                latency_ms=trade.latency_ms,
            )
        except (ValidationError, KeyError) as exc:
            log.warning("producer.validation_error", error=str(exc), data=str(data)[:200])
            kafka.produce_dlq(raw, str(exc))
            state.increment_dlq()


async def main() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ]
    )

    log.info("producer.starting", symbols=settings.symbols_list(), topic=settings.kafka_topic)

    state = health.start(settings.health_port)
    log.info("producer.health_server_started", port=settings.health_port)

    kafka = KafkaClient(settings)

    loop = asyncio.get_running_loop()
    stop = loop.create_future()

    def _shutdown(sig: signal.Signals) -> None:
        log.info("producer.shutdown", signal=sig.name)
        stop.set_result(None)

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    run_task = asyncio.create_task(_run(kafka, state))
    await asyncio.wait([run_task, asyncio.ensure_future(stop)], return_when=asyncio.FIRST_COMPLETED)

    run_task.cancel()
    kafka.flush()
    log.info("producer.stopped")


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
