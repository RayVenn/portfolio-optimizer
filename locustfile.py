from locust import HttpUser, task, between


class PortfolioUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def on_start(self):
        # Sample portfolio data for testing
        self.sample_request = {
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

        # Request with constraints
        self.constrained_request = {
            **self.sample_request,
            "constraints": {
                "min_weight": 0.05,
                "max_weight": 0.40,
                "sector_mapper": {
                    "AAPL": "Tech",
                    "GOOGL": "Tech",
                    "MSFT": "Tech",
                    "AMZN": "Consumer",
                    "META": "Tech",
                },
                "sector_upper": {"Tech": 0.60},
            },
        }

        # Request with transaction costs
        self.rebalance_request = {
            **self.sample_request,
            "transaction_costs": {
                "proportional": 0.001,
                "current_weights": [0.20, 0.20, 0.20, 0.20, 0.20],
            },
        }

    @task(3)
    def max_sharpe(self):
        self.client.post("/api/v1/optimize/max-sharpe", json=self.sample_request)

    @task(2)
    def min_volatility(self):
        self.client.post("/api/v1/optimize/min-volatility", json=self.sample_request)

    @task(2)
    def max_sharpe_constrained(self):
        self.client.post("/api/v1/optimize/max-sharpe", json=self.constrained_request)

    @task(2)
    def max_sharpe_with_costs(self):
        self.client.post("/api/v1/optimize/max-sharpe", json=self.rebalance_request)

    @task(1)
    def efficient_return(self):
        request = {**self.sample_request, "target_return": 0.11}
        self.client.post("/api/v1/optimize/efficient-return", json=request)

    @task(1)
    def health_check(self):
        self.client.get("/api/v1/health")
