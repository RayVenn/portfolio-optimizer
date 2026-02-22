"""Portfolio Optimizer CLI — thin client over the Portfolio Optimizer API."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Optional

import httpx
import typer

app = typer.Typer(help="Portfolio Optimizer CLI")
optimize_app = typer.Typer(help="Run portfolio optimization strategies.")
app.add_typer(optimize_app, name="optimize")

# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------

BaseUrlOption = Annotated[
    str,
    typer.Option("--base-url", envvar="PORTFOLIO_BASE_URL", help="API base URL."),
]
ApiKeyOption = Annotated[
    Optional[str],
    typer.Option(
        "--api-key", envvar="PORTFOLIO_API_KEY", help="API key for authentication."
    ),
]
FileOption = Annotated[
    Optional[Path],
    typer.Option(
        "--file",
        "-f",
        help="Path to a JSON file containing the portfolio request payload.",
    ),
]
DataOption = Annotated[
    Optional[str],
    typer.Option(
        "--data", "-d", help="Inline JSON string with the portfolio request payload."
    ),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_payload(file: Optional[Path], data: Optional[str]) -> dict:
    """Resolve --file (priority) or --data into a dict."""
    if file is not None:
        try:
            return json.loads(file.read_text())
        except Exception as exc:
            typer.echo(f"Error reading file '{file}': {exc}", err=True)
            raise typer.Exit(1)
    if data is not None:
        try:
            return json.loads(data)
        except json.JSONDecodeError as exc:
            typer.echo(f"Error parsing JSON: {exc}", err=True)
            raise typer.Exit(1)
    typer.echo("Error: provide --file or --data.", err=True)
    raise typer.Exit(1)


def _build_client(base_url: str, api_key: Optional[str]) -> httpx.Client:
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    return httpx.Client(base_url=base_url, headers=headers, timeout=30)


def _post(client: httpx.Client, path: str, payload: dict) -> dict:
    try:
        response = client.post(path, json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.json().get("detail", exc.response.text)
        typer.echo(f"API error {exc.response.status_code}: {detail}", err=True)
        raise typer.Exit(1)
    except httpx.RequestError as exc:
        typer.echo(f"Connection error: {exc}", err=True)
        raise typer.Exit(1)


def _print_result(result: dict) -> None:
    """Print optimization result as a formatted table."""
    weights: dict = result["weights"]
    typer.echo("\nOptimal Weights")
    typer.echo("-" * 30)
    for ticker, weight in sorted(weights.items(), key=lambda x: -x[1]):
        bar = "#" * int(weight * 40)
        typer.echo(f"  {ticker:<8} {weight:>7.2%}  {bar}")
    typer.echo("-" * 30)
    typer.echo(f"  Expected return : {result['expected_return']:.4%}")
    typer.echo(f"  Volatility      : {result['volatility']:.4%}")
    typer.echo(f"  Sharpe ratio    : {result['sharpe_ratio']:.4f}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def health(
    base_url: BaseUrlOption = "http://localhost:8000",
    api_key: ApiKeyOption = None,
) -> None:
    """Check API health."""
    with _build_client(base_url, api_key) as client:
        try:
            response = client.get("/api/v1/health")
            response.raise_for_status()
            data = response.json()
            typer.echo(f"Status : {data['status']}")
            typer.echo(f"Version: {data['version']}")
        except httpx.HTTPStatusError as exc:
            typer.echo(
                f"API error {exc.response.status_code}: {exc.response.text}", err=True
            )
            raise typer.Exit(1)
        except httpx.RequestError as exc:
            typer.echo(f"Connection error: {exc}", err=True)
            raise typer.Exit(1)


@optimize_app.command("max-sharpe")
def max_sharpe(
    file: FileOption = None,
    data: DataOption = None,
    base_url: BaseUrlOption = "http://localhost:8000",
    api_key: ApiKeyOption = None,
) -> None:
    """Optimize for maximum Sharpe ratio."""
    payload = _load_payload(file, data)
    with _build_client(base_url, api_key) as client:
        result = _post(client, "/api/v1/optimize/max-sharpe", payload)
    _print_result(result)


@optimize_app.command("min-volatility")
def min_volatility(
    file: FileOption = None,
    data: DataOption = None,
    base_url: BaseUrlOption = "http://localhost:8000",
    api_key: ApiKeyOption = None,
) -> None:
    """Optimize for minimum volatility."""
    payload = _load_payload(file, data)
    with _build_client(base_url, api_key) as client:
        result = _post(client, "/api/v1/optimize/min-volatility", payload)
    _print_result(result)


@optimize_app.command("efficient-return")
def efficient_return(
    file: FileOption = None,
    data: DataOption = None,
    target_return: Annotated[
        Optional[float],
        typer.Option(
            "--target-return", help="Target annual return (overrides value in payload)."
        ),
    ] = None,
    base_url: BaseUrlOption = "http://localhost:8000",
    api_key: ApiKeyOption = None,
) -> None:
    """Optimize for minimum volatility at a target return."""
    payload = _load_payload(file, data)
    if target_return is not None:
        payload["target_return"] = target_return
    if "target_return" not in payload or payload["target_return"] is None:
        typer.echo(
            "Error: target_return is required (use --target-return or include it in the payload).",
            err=True,
        )
        raise typer.Exit(1)
    with _build_client(base_url, api_key) as client:
        result = _post(client, "/api/v1/optimize/efficient-return", payload)
    _print_result(result)


@optimize_app.command("efficient-risk")
def efficient_risk(
    file: FileOption = None,
    data: DataOption = None,
    target_volatility: Annotated[
        Optional[float],
        typer.Option(
            "--target-volatility",
            help="Target annual volatility (overrides value in payload).",
        ),
    ] = None,
    base_url: BaseUrlOption = "http://localhost:8000",
    api_key: ApiKeyOption = None,
) -> None:
    """Optimize for maximum return at a target volatility."""
    payload = _load_payload(file, data)
    if target_volatility is not None:
        payload["target_volatility"] = target_volatility
    if "target_volatility" not in payload or payload["target_volatility"] is None:
        typer.echo(
            "Error: target_volatility is required (use --target-volatility or include it in the payload).",
            err=True,
        )
        raise typer.Exit(1)
    with _build_client(base_url, api_key) as client:
        result = _post(client, "/api/v1/optimize/efficient-risk", payload)
    _print_result(result)


if __name__ == "__main__":
    app()
