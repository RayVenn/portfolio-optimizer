import time

from pydantic import BaseModel, model_validator


class BinanceTrade(BaseModel):
    event_type: str       # "e"
    event_time_ms: int    # "E"
    symbol: str           # "s"
    trade_id: int         # "t"
    price: float          # "p"
    quantity: float       # "q"
    trade_time_ms: int    # "T"
    is_buyer_maker: bool  # "m"
    ingestion_time_ms: int
    latency_ms: int

    @model_validator(mode="before")
    @classmethod
    def from_binance_payload(cls, data: dict) -> dict:
        now_ms = time.time_ns() // 1_000_000
        trade_time = int(data["T"])
        return {
            "event_type": data["e"],
            "event_time_ms": int(data["E"]),
            "symbol": data["s"],
            "trade_id": int(data["t"]),
            "price": float(data["p"]),
            "quantity": float(data["q"]),
            "trade_time_ms": trade_time,
            "is_buyer_maker": bool(data["m"]),
            "ingestion_time_ms": now_ms,
            "latency_ms": now_ms - trade_time,
        }


class DLQMessage(BaseModel):
    raw_payload: str
    error: str
    ingestion_time_ms: int
