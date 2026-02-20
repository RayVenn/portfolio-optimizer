from fastapi import APIRouter, Depends, HTTPException

from app.api.auth import verify_api_key
from app.models.portfolio import HealthResponse, OptimizationResult, PortfolioRequest
from app.services.optimizer import (
    optimize_efficient_return,
    optimize_efficient_risk,
    optimize_max_sharpe,
    optimize_min_volatility,
)

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", version="0.1.0")


@router.post("/optimize/max-sharpe", response_model=OptimizationResult)
async def max_sharpe(request: PortfolioRequest, _: str = Depends(verify_api_key)):
    """Optimize portfolio for maximum Sharpe ratio."""
    try:
        return optimize_max_sharpe(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize/min-volatility", response_model=OptimizationResult)
async def min_volatility(request: PortfolioRequest, _: str = Depends(verify_api_key)):
    """Optimize portfolio for minimum volatility."""
    try:
        return optimize_min_volatility(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize/efficient-return", response_model=OptimizationResult)
async def efficient_return(request: PortfolioRequest, _: str = Depends(verify_api_key)):
    """Optimize portfolio for a target return with minimum volatility."""
    try:
        return optimize_efficient_return(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize/efficient-risk", response_model=OptimizationResult)
async def efficient_risk(request: PortfolioRequest, _: str = Depends(verify_api_key)):
    """Optimize portfolio for a target volatility with maximum return."""
    try:
        return optimize_efficient_risk(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
