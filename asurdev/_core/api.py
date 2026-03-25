"""FastAPI for asurdev Sentinel"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from .agents import (
    analyze_market, analyze_dow, analyze_andrews, analyze_smc,
    analyze_gann, analyze_monte_carlo, analyze_astrology, synthesize_signals
)
from .types import AgentResult

app = FastAPI(title="asurdev Sentinel API", version="2.1")

class AnalysisRequest(BaseModel):
    symbol: str = "BTC"
    price: float = 0
    prices: List[float] = []
    highs: Optional[List[float]] = None
    lows: Optional[List[float]] = None
    timestamp: Optional[str] = None
    agents: List[str] = ["all"]

class AnalysisResponse(BaseModel):
    symbol: str
    final_signal: AgentResult
    agent_results: List[AgentResult]

@app.get("/")
async def root():
    return {"message": "asurdev Sentinel API v2.1", "status": "running"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalysisRequest):
    """Run full analysis"""
    results = []
    
    # Generate synthetic data if not provided
    if not request.prices and request.price > 0:
        import random
        random.seed(42)
        p = request.price
        request.prices = [p := p * (1 + random.uniform(-0.02, 0.02)) for _ in range(50)]
    
    request.highs = request.highs or request.prices
    request.lows = request.lows or request.prices
    
    # Run selected agents
    agent_list = request.agents if "all" not in request.agents else [
        "market", "dow", "andrews", "smc", "gann", "monte_carlo", "astrology"
    ]
    
    if "market" in agent_list:
        results.append(analyze_market(request.prices, request.symbol))
    if "dow" in agent_list:
        results.append(analyze_dow(request.prices, request.symbol))
    if "andrews" in agent_list:
        results.append(analyze_andrews(request.prices, request.symbol))
    if "smc" in agent_list:
        results.append(analyze_smc(request.prices, request.highs, request.lows, request.symbol))
    if "gann" in agent_list:
        results.append(analyze_gann(request.price or request.prices[-1], request.symbol))
    if "monte_carlo" in agent_list:
        results.append(analyze_monte_carlo(request.prices, request.symbol))
    if "astrology" in agent_list:
        results.append(analyze_astrology(request.timestamp))
    
    # Synthesize
    final = synthesize_signals(results, request.symbol)
    
    return AnalysisResponse(
        symbol=request.symbol,
        final_signal=final,
        agent_results=results
    )

@app.get("/agents")
async def list_agents():
    """List available agents"""
    return {
        "agents": [
            {"name": "market", "description": "Technical analysis (RSI, MA, trends)"},
            {"name": "dow", "description": "Dow Theory trend detection"},
            {"name": "andrews", "description": "Andrews Pitchfork median line"},
            {"name": "smc", "description": "Smart Money Concepts (Order Blocks, FVG)"},
            {"name": "gann", "description": "W.D. Gann Square of 9"},
            {"name": "monte_carlo", "description": "Monte Carlo price projection"},
            {"name": "astrology", "description": "Moon phase analysis"},
        ]
    }
