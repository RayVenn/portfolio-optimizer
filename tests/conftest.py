import os

import pytest
from fastapi.testclient import TestClient

TEST_API_KEY = "test-api-key-for-testing"


@pytest.fixture(autouse=True)
def set_api_key_env():
    """Set API_KEY env var for all tests."""
    os.environ["API_KEY"] = TEST_API_KEY
    yield
    os.environ.pop("API_KEY", None)


@pytest.fixture
def client():
    """FastAPI test client."""
    from main import app

    return TestClient(app)


@pytest.fixture
def auth_header():
    """Auth header with valid API key."""
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def sample_portfolio_data():
    """Sample portfolio data for testing."""
    return {
        "tickers": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
        "expected_returns": [0.12, 0.10, 0.11, 0.14, 0.09],
        "covariance_matrix": [
            [0.04, 0.01, 0.015, 0.02, 0.01],
            [0.01, 0.035, 0.012, 0.018, 0.008],
            [0.015, 0.012, 0.03, 0.016, 0.009],
            [0.02, 0.018, 0.016, 0.05, 0.012],
            [0.01, 0.008, 0.009, 0.012, 0.025],
        ],
        "risk_free_rate": 0.02,
    }


@pytest.fixture
def small_portfolio_data():
    """Small portfolio for faster tests."""
    return {
        "tickers": ["A", "B", "C"],
        "expected_returns": [0.10, 0.12, 0.08],
        "covariance_matrix": [
            [0.04, 0.01, 0.005],
            [0.01, 0.05, 0.01],
            [0.005, 0.01, 0.03],
        ],
        "risk_free_rate": 0.02,
    }
