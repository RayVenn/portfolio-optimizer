"""Binance WebSocket client with exponential backoff reconnection."""

import asyncio
import ssl
from collections.abc import AsyncGenerator

import certifi
import structlog
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

log = structlog.get_logger()

PING_INTERVAL = 30  # seconds
SSL_CTX = ssl.create_default_context(cafile=certifi.where())


async def stream(base_url: str, symbols: list[str], reconnect_delay: float, max_delay: float) -> AsyncGenerator[str, None]:
    """Async generator yielding raw JSON trade messages from Binance.

    Automatically reconnects with exponential backoff on any disconnect.
    Each yielded string is the raw JSON payload of a single trade event.
    """
    streams = "/".join(f"{sym.lower()}@trade" for sym in symbols)
    url = f"{base_url}?streams={streams}"
    delay = reconnect_delay

    while True:
        try:
            log.info("ws.connecting", url=url)
            async with websockets.connect(url, ssl=SSL_CTX, ping_interval=PING_INTERVAL) as ws:
                log.info("ws.connected", streams=streams)
                delay = reconnect_delay  # reset backoff on successful connect
                async for message in ws:
                    yield message
        except ConnectionClosed as exc:
            log.warning("ws.disconnected", reason=str(exc), reconnect_in=delay)
        except WebSocketException as exc:
            log.error("ws.error", error=str(exc), reconnect_in=delay)
        except Exception as exc:
            log.error("ws.unexpected_error", error=str(exc), reconnect_in=delay)

        await asyncio.sleep(delay)
        delay = min(delay * 2, max_delay)
