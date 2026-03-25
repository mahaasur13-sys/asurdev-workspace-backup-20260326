"""
AstroFin Sentinel v5 — Main Orchestrator
RAG-First Multi-Agent Architecture with LangGraph.

Flow:
  User Query → Router → [Parallel Specialist Flows] → Synthesis → Final Report
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
Technical    Astro       Electional
  Team      Council        Agent
    │            │            │
    ▼            ▼            ▼
Confluence  Confluence  Best Windows
    └────────────┼────────────┘
                 ▼
          Synthesis Agent
                 │
                 ▼
         Final Recommendation
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional

from orchestration.router import route_query, QueryType
from agents.base_agent import AgentResponse, SignalDirection
from agents.astro_council_agent import run_astro_council_agent
from agents.electoral_agent import run_electoral_agent
from agents.synthesis_agent import SynthesisAgent


# ─── Agent Weights ─────────────────────────────────────────────────────────────

AGENT_WEIGHTS = {
    "MarketAnalyst": 0.25,
    "AstroCouncil": 0.20,
    "BullResearcher": 0.15,
    "BearResearcher": 0.15,
    "ElectoralAgent": 0.10,
    "CycleAgent": 0.05,
    "RiskAgent": 0.05,
}


# ─── Parallel Flow Runners ──────────────────────────────────────────────────────

async def run_technical_flow(state: dict) -> dict:
    """Run technical analysis team (MarketAnalyst + Bull/Bear)."""
    try:
        from agents.market_analyst import run_market_analyst
    except ImportError:
        return {"market_analyst_signal": None}

    try:
        from agents.directional_agents import run_bull_researcher, run_bear_researcher
    except ImportError:
        return {"bull_signal": None, "bear_signal": None}

    results = await asyncio.gather(
        run_market_analyst(state),
        run_bull_researcher(state),
        run_bear_researcher(state),
        return_exceptions=True,
    )

    merged = {}
    for r in results:
        if isinstance(r, dict):
            merged.update(r)
    return merged


async def run_astro_flow(state: dict) -> dict:
    """Run astro council (Western + Vedic + Financial)."""
    return await run_astro_council_agent(state)


async def run_electoral_flow(state: dict) -> dict:
    """Run electoral/muhurta agent."""
    return await run_electoral_agent(state)


# ─── Main Orchestrator ─────────────────────────────────────────────────────────

async def run_sentinel_v5(
    user_query: str,
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    current_price: float = 0.0,
    birth_data: dict = None,
    include_technical: bool = True,
    include_astro: bool = True,
    include_electional: bool = False,
    session_id: str = None,
) -> dict:
    """
    Main entry point for AstroFin Sentinel v5.

    Args:
        user_query: Natural language query from user
        symbol: Trading symbol (e.g., BTCUSDT)
        timeframe: INTRADAY / SWING / POSITIONAL
        current_price: Current price (auto-fetched if 0)
        birth_data: Optional birth data for natal chart
        include_technical: Run technical team
        include_astro: Run AstroCouncil
        include_electional: Run ElectoralAgent
        session_id: Optional session ID for checkpointing

    Returns:
        dict with final_recommendation, all_signals, council_votes
    """
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # Step 1: Route query
    route_output = route_query(user_query)
    print(f"[Router] Query type: {route_output.query_type.value}")
    print(f"[Router] Symbols: {route_output.symbols}")
    print(f"[Router] Flows: tech={include_technical}, astro={include_astro}, elec={include_electional}")

    # Override with explicit params
    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    # Step 2: Fetch price if needed
    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

    # Step 3: Build initial state
    state = {
        "symbol": symbols[0],
        "timeframe_requested": timeframe,
        "current_price": current_price,
        "birth_data": birth_data,
        "user_query": user_query,
        "session_id": session_id,
        "started_at": datetime.utcnow().isoformat(),
        "all_signals": [],
    }

    # Step 4: Run flows in parallel
    flow_tasks = []

    if include_technical:
        flow_tasks.append(run_technical_flow(state))

    if include_astro:
        flow_tasks.append(run_astro_flow(state))

    if include_electional:
        flow_tasks.append(run_electoral_flow(state))

    if flow_tasks:
        flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)

        # Merge signals into state
        for result in flow_results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_signal") and value is not None:
                        state["all_signals"].append(value)

    # Step 5: Run Synthesis
    synthesis_agent = SynthesisAgent()
    synthesis_result = await synthesis_agent.run(state)

    # Step 6: Build final output
    final_output = {
        "session_id": session_id,
        "symbol": symbols[0],
        "timeframe": timeframe,
        "current_price": current_price,
        "query_type": route_output.query_type.value,
        "flows_run": {
            "technical": include_technical,
            "astro": include_astro,
            "electional": include_electional,
        },
        "agent_count": len(state["all_signals"]),
        "final_recommendation": synthesis_result.to_dict(),
        "final_report": synthesis_agent.format_final_report(synthesis_result),
        "timestamp": datetime.utcnow().isoformat(),
    }

    return final_output


async def _fetch_price(symbol: str) -> float:
    """Fetch current price from Binance."""
    try:
        import requests
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return float(data.get("price", 0))
    except Exception:
        return 0.0


# ─── CLI Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("Usage: python -m orchestration.sentinel_v5 <query> [symbol] [timeframe]")
            print("Example: python -m orchestration.sentinel_v5 'Analyze BTC for swing trade' BTCUSDT SWING")
            sys.exit(1)

        query = sys.argv[1]
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
        timeframe = sys.argv[3] if len(sys.argv) > 3 else "SWING"

        print(f"\n🚀 AstroFin Sentinel v5 — RAG-First Multi-Agent System")
        print(f"   Query: {query}")
        print(f"   Symbol: {symbol} | Timeframe: {timeframe}")
        print(f"   {'='*60}\n")

        result = await run_sentinel_v5(
            user_query=query,
            symbol=symbol,
            timeframe=timeframe,
        )

        print(result["final_report"])

    asyncio.run(main())
