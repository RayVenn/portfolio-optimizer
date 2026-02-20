import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


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
