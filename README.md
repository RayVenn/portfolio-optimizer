# Crypto Market Monitor

Real-time monitoring system for crypto market data — tracking both market behaviour and pipeline health.

## Architecture

```
Binance WebSocket API
        ↓
Python Producer  (parse · validate · ingestion timestamp)
        ↓
Kafka
  ├── binance-trades        (main topic, 24 h retention)
  └── binance-trades-dlq    (failed / invalid messages)
        ↓
Flink Stream Processing  [milestone 3+]
  ├── Market Metrics  (volatility · volume spikes · buy/sell ratio · whale detection)
  └── Pipeline Health (throughput · consumer lag · latency · DLQ rate)
        ↓
  Alert Engine  [milestone 5+]
  ├── InfluxDB   (aggregated time-series metrics)
  └── Slack      (threshold / anomaly alerts)
        ↓
Grafana Dashboard  [milestone 5+]
```

## Tech Stack

| Component        | Technology                |
|------------------|---------------------------|
| Data source      | Binance WebSocket API     |
| Message broker   | Apache Kafka              |
| Stream processing| Apache Flink (PyFlink)    |
| Time-series DB   | InfluxDB 2                |
| Visualisation    | Grafana                   |
| Alerting         | Slack webhook             |
| Infrastructure   | Docker Compose / Kubernetes (Helm + ArgoCD) |

---

## Milestones

- [x] **M1** Docker Compose — Kafka, InfluxDB stub, Grafana stub
- [x] **M2** Python Binance WebSocket producer → Kafka (DLQ + retry)
- [ ] **M3** Basic Flink job reading from Kafka
- [ ] **M4** Flink windowed aggregation → InfluxDB sink
- [ ] **M5** Grafana dashboard + Alert engine → Slack

---

## Quick Start

### Prerequisites
- Docker + Docker Compose v2
- Internet access (Binance WebSocket is public, no API key required for trade streams)

### Run

```bash
# Copy env template
cp .env.example .env

# Start Kafka + producer (core pipeline)
docker compose up --build

# Start with monitoring stack (InfluxDB + Grafana)
docker compose --profile monitoring up --build
```

### Verify data is flowing

```bash
# Watch live trade messages
docker compose exec kafka \
  kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic binance-trades \
  --from-beginning

# Check producer health
curl http://localhost:8080/health
# → {"status": "ok", "produced": 142, "dlq": 0, "ws_connected": true}

# Check DLQ
docker compose exec kafka \
  kafka-console-consumer \
  --bootstrap-server localhost:29092 \
  --topic binance-trades-dlq \
  --from-beginning
```

---

## Producer Configuration

All settings are environment variables (see [.env.example](.env.example)).

| Variable | Default | Description |
|---|---|---|
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:9092` | Kafka broker address |
| `KAFKA_TOPIC` | `binance-trades` | Main topic |
| `KAFKA_DLQ_TOPIC` | `binance-trades-dlq` | Dead-letter queue topic |
| `SYMBOLS` | `BTCUSDT` | Comma-separated pairs, e.g. `BTCUSDT,ETHUSDT` |
| `RECONNECT_DELAY_S` | `5.0` | Initial WebSocket reconnect delay (s) |
| `MAX_RECONNECT_DELAY_S` | `60.0` | Max reconnect delay after backoff (s) |
| `HEALTH_PORT` | `8080` | Health check HTTP port |

---

## Trade Message Schema

Each message on `binance-trades`:

```json
{
  "event_type": "trade",
  "event_time_ms": 1709000000000,
  "symbol": "BTCUSDT",
  "trade_id": 3456789,
  "price": 62345.67,
  "quantity": 0.012,
  "trade_time_ms": 1709000000000,
  "is_buyer_maker": false,
  "ingestion_time_ms": 1709000000042,
  "latency_ms": 42
}
```

Failed messages on `binance-trades-dlq`:

```json
{
  "raw_payload": "...",
  "error": "ValidationError: ...",
  "ingestion_time_ms": 1709000000000
}
```

---

## Kubernetes Deployment

The Helm chart lives in [helm/crypto-monitor/](helm/crypto-monitor/) and is managed via [ArgoCD](argocd/application.yaml).

```bash
# Manual deploy
helm upgrade --install crypto-monitor ./helm/crypto-monitor \
  --namespace crypto-monitor \
  --create-namespace \
  --set image.tag=<SHA>
```
