# Portfolio Optimizer

A FastAPI-based REST API for mean-variance portfolio optimization using Modern Portfolio Theory (MPT).

## Features

- **Mean-Variance Optimization** using PyPortfolioOpt's Efficient Frontier
- **Multiple optimization strategies:**
  - Maximum Sharpe Ratio
  - Minimum Volatility
  - Efficient Return (target return with minimum risk)
  - Efficient Risk (target volatility with maximum return)
- **Transaction Cost Models:**
  - Proportional costs (e.g., 0.1% per trade)
  - Supports rebalancing from current portfolio
- **Portfolio Constraints:**
  - Min/max weight per asset
  - Per-asset custom weight bounds
  - Sector exposure limits
- **High concurrency** with FastAPI's async support
- **Load testing** with Locust for throughput benchmarking

## Installation

Requires Python 3.9+ and [uv](https://docs.astral.sh/uv/).

```bash
# Install dependencies
uv sync

# Install with dev dependencies (for testing)
uv sync --dev
```

## Usage

### Start the server

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uv run uvicorn main:app --reload
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/optimize/max-sharpe` | Maximum Sharpe ratio optimization |
| POST | `/api/v1/optimize/min-volatility` | Minimum volatility optimization |
| POST | `/api/v1/optimize/efficient-return` | Target return optimization |
| POST | `/api/v1/optimize/efficient-risk` | Target volatility optimization |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/optimize/max-sharpe \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
    "expected_returns": [0.12, 0.10, 0.11, 0.14, 0.09],
    "covariance_matrix": [
      [0.04, 0.01, 0.015, 0.02, 0.01],
      [0.01, 0.035, 0.012, 0.018, 0.008],
      [0.015, 0.012, 0.03, 0.016, 0.009],
      [0.02, 0.018, 0.016, 0.05, 0.012],
      [0.01, 0.008, 0.009, 0.012, 0.025]
    ],
    "risk_free_rate": 0.02
  }'
```

### Example Response

```json
{
  "weights": {
    "AAPL": 0.25,
    "GOOGL": 0.15,
    "MSFT": 0.30,
    "AMZN": 0.20,
    "META": 0.10
  },
  "expected_return": 0.115,
  "volatility": 0.18,
  "sharpe_ratio": 0.53
}
```

### With Portfolio Constraints

```bash
curl -X POST http://localhost:8000/api/v1/optimize/max-sharpe \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
    "expected_returns": [0.12, 0.10, 0.11, 0.14, 0.09],
    "covariance_matrix": [
      [0.04, 0.01, 0.015, 0.02, 0.01],
      [0.01, 0.035, 0.012, 0.018, 0.008],
      [0.015, 0.012, 0.03, 0.016, 0.009],
      [0.02, 0.018, 0.016, 0.05, 0.012],
      [0.01, 0.008, 0.009, 0.012, 0.025]
    ],
    "risk_free_rate": 0.02,
    "constraints": {
      "min_weight": 0.05,
      "max_weight": 0.40,
      "sector_mapper": {
        "AAPL": "Tech",
        "GOOGL": "Tech",
        "MSFT": "Tech",
        "AMZN": "Consumer",
        "META": "Tech"
      },
      "sector_upper": {"Tech": 0.60}
    }
  }'
```

### With Transaction Costs (Rebalancing)

```bash
curl -X POST http://localhost:8000/api/v1/optimize/max-sharpe \
  -H "Content-Type: application/json" \
  -d '{
    "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
    "expected_returns": [0.12, 0.10, 0.11, 0.14, 0.09],
    "covariance_matrix": [
      [0.04, 0.01, 0.015, 0.02, 0.01],
      [0.01, 0.035, 0.012, 0.018, 0.008],
      [0.015, 0.012, 0.03, 0.016, 0.009],
      [0.02, 0.018, 0.016, 0.05, 0.012],
      [0.01, 0.008, 0.009, 0.012, 0.025]
    ],
    "risk_free_rate": 0.02,
    "transaction_costs": {
      "proportional": 0.001,
      "current_weights": [0.20, 0.20, 0.20, 0.20, 0.20]
    }
  }'
```

## Constraints Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `min_weight` | float | Minimum weight per asset (default: 0, long-only) |
| `max_weight` | float | Maximum weight per asset (default: 1) |
| `weight_bounds` | list | Per-asset bounds as `[(min, max), ...]` |
| `sector_mapper` | dict | Map ticker → sector name |
| `sector_lower` | dict | Minimum allocation per sector |
| `sector_upper` | dict | Maximum allocation per sector |

## Transaction Costs Reference

| Parameter | Type | Description |
|-----------|------|-------------|
| `proportional` | float | Cost as fraction of trade value (e.g., 0.001 = 0.1%) |
| `current_weights` | list | Current portfolio weights for rebalancing |

## Load Testing

Run the Locust load test to benchmark throughput:

```bash
# Start the API server first, then in another terminal:
uv run locust --host http://localhost:8000
```

Open http://localhost:8089 to configure:
- Number of users
- Spawn rate
- Run duration

## Project Structure

```
portfolio-optimizer/
├── app/
│   ├── api/
│   │   └── routes.py         # API endpoint definitions
│   ├── models/
│   │   └── portfolio.py      # Pydantic request/response models
│   └── services/
│       └── optimizer.py      # Mean-variance optimization logic
├── main.py                   # FastAPI application entry point
├── locustfile.py             # Load testing configuration
├── pyproject.toml            # Project dependencies
└── README.md
```

## API Documentation

Once the server is running, interactive API docs are available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Dependencies

- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **PyPortfolioOpt** - Portfolio optimization library
- **NumPy/SciPy** - Numerical computing
- **Pandas** - Data manipulation
- **Locust** - Load testing (dev)
