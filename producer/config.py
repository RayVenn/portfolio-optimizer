from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Kafka
    kafka_bootstrap_servers: str = "kafka:9092"
    kafka_topic: str = "binance-trades"
    kafka_dlq_topic: str = "binance-trades-dlq"
    kafka_flush_every: int = 100  # flush after N messages

    # Binance
    binance_ws_url: str = "wss://data-stream.binance.vision/stream"
    symbols: str = "BTCUSDT"  # comma-separated, e.g. "BTCUSDT,ETHUSDT"

    # Reconnect
    reconnect_delay_s: float = 5.0
    max_reconnect_delay_s: float = 60.0

    # Health server
    health_port: int = 8080

    def symbols_list(self) -> list[str]:
        return [s.strip().upper() for s in self.symbols.split(",") if s.strip()]


settings = Settings()
