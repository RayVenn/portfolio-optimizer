import pytest
from pydantic import ValidationError

from app.models.portfolio import (
    Asset,
    HealthResponse,
    OptimizationResult,
    PortfolioConstraints,
    PortfolioRequest,
    TransactionCosts,
)


class TestAsset:
    def test_create_asset(self):
        asset = Asset(ticker="AAPL", expected_return=0.12)
        assert asset.ticker == "AAPL"
        assert asset.expected_return == 0.12

    def test_asset_requires_fields(self):
        with pytest.raises(ValidationError):
            Asset()


class TestTransactionCosts:
    def test_default_values(self):
        tc = TransactionCosts()
        assert tc.proportional is None
        assert tc.flat is None
        assert tc.current_weights is None

    def test_with_proportional(self):
        tc = TransactionCosts(proportional=0.001)
        assert tc.proportional == 0.001

    def test_with_current_weights(self):
        tc = TransactionCosts(
            proportional=0.001, current_weights=[0.25, 0.25, 0.25, 0.25]
        )
        assert tc.current_weights == [0.25, 0.25, 0.25, 0.25]


class TestPortfolioConstraints:
    def test_default_values(self):
        pc = PortfolioConstraints()
        assert pc.min_weight == 0.0
        assert pc.max_weight == 1.0
        assert pc.weight_bounds is None
        assert pc.sector_mapper is None

    def test_with_weight_bounds(self):
        pc = PortfolioConstraints(min_weight=0.05, max_weight=0.40)
        assert pc.min_weight == 0.05
        assert pc.max_weight == 0.40

    def test_with_sector_constraints(self):
        pc = PortfolioConstraints(
            sector_mapper={"AAPL": "Tech", "JPM": "Finance"},
            sector_lower={"Tech": 0.1},
            sector_upper={"Tech": 0.5, "Finance": 0.3},
        )
        assert pc.sector_mapper["AAPL"] == "Tech"
        assert pc.sector_upper["Tech"] == 0.5

    def test_with_per_asset_bounds(self):
        pc = PortfolioConstraints(weight_bounds=[(0.1, 0.3), (0.2, 0.5), (0.0, 1.0)])
        assert pc.weight_bounds[0] == (0.1, 0.3)

    def test_with_max_assets(self):
        pc = PortfolioConstraints(max_assets=5)
        assert pc.max_assets == 5


class TestPortfolioRequest:
    def test_minimal_request(self):
        req = PortfolioRequest(
            tickers=["A", "B"],
            expected_returns=[0.1, 0.12],
            covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
        )
        assert len(req.tickers) == 2
        assert req.risk_free_rate == 0.02  # default

    def test_with_target_return(self):
        req = PortfolioRequest(
            tickers=["A", "B"],
            expected_returns=[0.1, 0.12],
            covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
            target_return=0.11,
        )
        assert req.target_return == 0.11

    def test_with_target_volatility(self):
        req = PortfolioRequest(
            tickers=["A", "B"],
            expected_returns=[0.1, 0.12],
            covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
            target_volatility=0.15,
        )
        assert req.target_volatility == 0.15

    def test_with_constraints(self):
        req = PortfolioRequest(
            tickers=["A", "B"],
            expected_returns=[0.1, 0.12],
            covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
            constraints=PortfolioConstraints(min_weight=0.1),
        )
        assert req.constraints.min_weight == 0.1

    def test_with_transaction_costs(self):
        req = PortfolioRequest(
            tickers=["A", "B"],
            expected_returns=[0.1, 0.12],
            covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
            transaction_costs=TransactionCosts(proportional=0.001),
        )
        assert req.transaction_costs.proportional == 0.001

    def test_requires_tickers(self):
        with pytest.raises(ValidationError):
            PortfolioRequest(
                expected_returns=[0.1, 0.12],
                covariance_matrix=[[0.04, 0.01], [0.01, 0.05]],
            )


class TestOptimizationResult:
    def test_create_result(self):
        result = OptimizationResult(
            weights={"A": 0.6, "B": 0.4},
            expected_return=0.108,
            volatility=0.18,
            sharpe_ratio=0.49,
        )
        assert result.weights["A"] == 0.6
        assert result.expected_return == 0.108
        assert result.volatility == 0.18
        assert result.sharpe_ratio == 0.49


class TestHealthResponse:
    def test_create_response(self):
        resp = HealthResponse(status="healthy", version="0.1.0")
        assert resp.status == "healthy"
        assert resp.version == "0.1.0"
