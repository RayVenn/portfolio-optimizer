"""Standalone script: connect to Binance WebSocket and print trades to terminal.
No Kafka or Docker required.

Run: uv run python watch_trades.py
"""

import asyncio
import json
import ssl
import time

import certifi
import websockets

URL = "wss://data-stream.binance.vision/stream?streams=btcusdt@trade"
SSL_CTX = ssl.create_default_context(cafile=certifi.where())


async def main() -> None:
    print(f"Connecting to Binance WebSocket: {URL}\n")
    async with websockets.connect(URL, ssl=SSL_CTX) as ws:
        print(f"{'Time':12}  {'Symbol':10}  {'Price':>12}  {'Qty':>10}  {'Side':8}  {'Latency':>10}")
        print("-" * 72)
        async for raw in ws:
            envelope = json.loads(raw)
            d = envelope["data"]

            ingestion_ms = time.time_ns() // 1_000_000
            latency_ms = ingestion_ms - int(d["T"])
            side = "SELL" if d["m"] else "BUY "  # m=True means buyer is maker → seller is taker

            print(
                f"{d['s']:12}  "
                f"{float(d['p']):>12,.2f}  "
                f"{float(d['q']):>10.5f}  "
                f"{side:8}  "
                f"{latency_ms:>7} ms"
            )


if __name__ == "__main__":
    asyncio.run(main())
