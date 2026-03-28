"""
AstroFin Sentinel v5 — Main Orchestrator
RAG-First Multi-Agent Architecture with LangGraph.

Thompson Sampling replaces static AGENT_WEIGHTS for agent selection:
  At each orchestration step, for each candidate pool:
    - Sample θ_i ~ Beta(α_i, β_i) for all agents (from belief tracker)
    - Select top-K agents by sampled θ_i
    - Only selected agents are called

Flow:
  User Query → Router → [Thompson Selection] → [Parallel Specialist Flows] → Synthesis → Final Report
                    │
        ┌───────────┼────────────┐
        ▼           ▼            ▼
  Technical    Astro       Electional
    Team     Council        Agent
        │           │            │
        ▼           ▼            ▼
  Confluence  Confluence  Confluence
        └───────────┼────────────┘
                    ▼
             Synthesis Agent
                    │
                    ▼
            Final Recommendation
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from agents.astro_council_agent import run_astro_council
from agents._impl.electoral_agent import run_electoral_agent
from agents._impl.synthesis_agent import SynthesisAgent, CATEGORY_WEIGHTS
from agents.karl_synthesis import KARLSynthesisAgent, get_karl_agent
from agents._impl.market_analyst import run_market_analyst
from agents._impl.bull_researcher import run_bull_researcher
from agents._impl.bear_researcher import run_bear_researcher
from agents.base_agent import AgentResponse, SignalDirection
from orchestration.router import route_query
from core.history_db import save_session
from core.belief import update_beliefs_from_session
from core.thompson import (
    ThompsonSampler,
    AgentPool,
    TECHNICAL_POOL,
    ELECTORAL_POOL,
    ASTRO_POOL,
    get_thompson_sampler,
    thompson_select,
)


# ─── Agent Weights ─────────────────────────────────────────────────────────────

# ─── Parallel Flow Runners ──────────────────────────────────────────────────────

async def run_technical_flow(
    state: dict,
    selected_agents: Optional[list[str]] = None,
) -> dict:
    """
    Run technical analysis team.
    selected_agents: list of agent names to call (Thompson-selected).
                    Defaults to all known agents in TECHNICAL_POOL.
    """
    pool_agents = selected_agents or TECHNICAL_POOL.agents

    tasks = []
    names = []

    if "MarketAnalyst" in pool_agents:
        tasks.append(run_market_analyst(state))
        names.append("MarketAnalyst")

    if "BullResearcher" in pool_agents:
        tasks.append(run_bull_researcher(state))
        names.append("BullResearcher")

    if "BearResearcher" in pool_agents:
        tasks.append(run_bear_researcher(state))
        names.append("BearResearcher")

    if not tasks:
        return {}

    results = await asyncio.gather(*tasks, return_exceptions=True)

    merged = {}
    for name, r in zip(names, results):
        if isinstance(r, dict):
            merged[f"{name.lower()}_signal"] = r.get(f"{name.lower()}_signal") or list(r.values())[0]
        elif isinstance(r, Exception):
            merged[f"{name.lower()}_signal"] = AgentResponse(
                agent_name=name,
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning=f"Agent error: {str(r)[:100]}",
                sources=[],
            ).to_dict()
    return merged


async def run_astro_flow(
    state: dict,
    selected_agents: Optional[list[str]] = None,
) -> dict:
    """
    Run astro council with Thompson-selected sub-agents.
    selected_agents: list of agent names to pass to AstroCouncilAgent.
                     Defaults to all known agents in ASTRO_POOL.
    """
    pool_agents = selected_agents or ASTRO_POOL.agents

    # Inject selected agents into state so AstroCouncilAgent respects them
    state = {**state, "_thompson_selected_astro": pool_agents}

    return await run_astro_council(state)


async def run_electoral_flow(
    state: dict,
    selected_agents: Optional[list[str]] = None,
) -> dict:
    """Run electoral/muhurta agent (always single agent)."""
    return await run_electoral_agent(state)


# ─── Thompson Sampling Helpers ─────────────────────────────────────────────────

def _select_for_flow(
    pool: AgentPool,
    excluded: Optional[list[str]] = None,
    k: Optional[int] = None,
) -> list[str]:
    """
    Run Thompson sampling for one pool.
    Returns list of selected agent names.
    """
    sampler = get_thompson_sampler()
    if excluded:
        selected = sampler.select_with_exclusions(pool, excluded=excluded, k=k)
    else:
        selected = sampler.select(pool, k=k)
    return [name for name, _ in selected]


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
    persist: bool = True,
    thompson_k: int = 4,
) -> dict:
    """
    Main entry point for AstroFin Sentinel v5.

    Thompson Sampling is applied at each orchestration step to dynamically
    select which agents to call, replacing static AGENT_WEIGHTS.

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
        persist: Save session and update belief tracker
        thompson_k: Default number of agents to select per pool
                    (can be overridden per-pool via pool.max_select)

    Returns:
        dict with final_recommendation, all_signals, flows_run, thompson_selections
    """
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # ── Step 1: Route query ──────────────────────────────────────────────────
    route_output = route_query(user_query)
    print(f"[Router] Query type: {route_output.query_type.value}")
    print(f"[Router] Symbols: {route_output.symbols}")
    print(f"[Router] Flows: tech={include_technical}, astro={include_astro}, elec={include_electional}")

    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    # ── Step 2: Fetch price if needed ───────────────────────────────────────
    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

    # ── Step 3: Build initial state ──────────────────────────────────────────
    state = {
        "symbol": symbols[0],
        "timeframe_requested": timeframe,
        "current_price": current_price,
        "birth_data": birth_data,
        "user_query": user_query,
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "all_signals": [],
    }

    # ── Step 4: Thompson Sampling selection per flow ─────────────────────────
    # Technical → Astro → Electoral (order matters for dependency)
    thompson_selections: dict = {}

    technical_selected: list[str] = []
    astro_selected: list[str] = []

    if include_technical:
        technical_selected = _select_for_flow(TECHNICAL_POOL, k=thompson_k)
        thompson_selections["technical"] = technical_selected

    if include_astro:
        # Exclude agents already selected in technical (e.g. BullResearcher, BearResearcher)
        astro_selected = _select_for_flow(
            ASTRO_POOL,
            excluded=technical_selected,
            k=thompson_k,
        )
        thompson_selections["astro"] = astro_selected

    if include_electional:
        electoral_selected = _select_for_flow(ELECTORAL_POOL, k=1)
        thompson_selections["electoral"] = electoral_selected

    # Log Thompson sampling decisions
    print(f"[Thompson] technical: {technical_selected}")
    print(f"[Thompson] astro:     {astro_selected}")

    # ── Step 5: Run flows in parallel ────────────────────────────────────────
    flow_tasks = []

    if include_technical:
        flow_tasks.append(run_technical_flow(state, selected_agents=technical_selected))

    if include_astro:
        flow_tasks.append(run_astro_flow(state, selected_agents=astro_selected))

    if include_electional:
        flow_tasks.append(run_electoral_flow(state))

    if flow_tasks:
        flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)

        for result in flow_results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_signal") and value is not None:
                        state["all_signals"].append(value)

        if not state["all_signals"]:
            fallback_response = AgentResponse(
                agent_name="SystemFallback",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="All agents failed to produce a signal.",
            )
            state["all_signals"].append(fallback_response)

    # ── Step 6: Run Synthesis ────────────────────────────────────────────────
    synthesis_agent = SynthesisAgent()
    try:
        synthesis_result = await synthesis_agent.run(state)
    except Exception as e:
        print(f"[SynthesisAgent] Skipped — agent unavailable: {e}")
        synthesis_result = None

    # ── Step 7: Build final output ───────────────────────────────────────────
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
        "thompson_selections": thompson_selections,
        "agent_count": len(state["all_signals"]),
        "final_recommendation": synthesis_result.to_dict() if synthesis_result else None,
        "final_report": synthesis_result.to_dict() if synthesis_result else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if persist:
        save_session(final_output)
        update_beliefs_from_session(final_output)

    return final_output


# ─── KARL-013: Main Orchestrator with Full KARL Integration ───────────────────

async def run_sentinel_v5_karl(
    user_query: str,
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    current_price: float = 0.0,
    birth_data: dict = None,
    include_technical: bool = True,
    include_astro: bool = True,
    include_electional: bool = False,
    session_id: str = None,
    persist: bool = True,
    thompson_k: int = 4,
    enable_self_question: bool = False,
    enable_backtest: bool = True,
    sync_interval: int = 10,
) -> dict:
    """
    AstroFin Sentinel v5 with full KARL-013 integration.

    Adds to run_sentinel_v5:
    - DecisionRecord на каждое решение
    - OAPOptimizer updates
    - ContinuousBacktest samples
    - Self-questioning (optional)
    - Periodic sync_with_audit() every N decisions

    Args:
        enable_self_question: Run SelfQuestioningEngine before synthesis
        enable_backtest: Add samples to ContinuousBacktest
        sync_interval: Run sync_with_audit() every N decisions

    Returns:
        dict with all run_sentinel_v5 fields PLUS:
          - karl_diagnostics
          - decision_record
          - amre_output
    """
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    # ── Step 1: Route query ──────────────────────────────────────────────────
    route_output = route_query(user_query)
    print(f"[Router] Query type: {route_output.query_type.value}")
    print(f"[Router] Symbols: {route_output.symbols}")
    print(f"[Router] Flows: tech={include_technical}, astro={include_astro}, elec={include_electional}")

    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    # ── Step 2: Fetch price if needed ───────────────────────────────────────
    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

    # ── Step 3: Build initial state ──────────────────────────────────────────
    state = {
        "symbol": symbols[0],
        "timeframe_requested": timeframe,
        "current_price": current_price,
        "birth_data": birth_data,
        "user_query": user_query,
        "session_id": session_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "all_signals": [],
    }

    # ── Step 4: Thompson Sampling selection per flow ─────────────────────────
    thompson_selections: dict = {}
    technical_selected: list[str] = []
    astro_selected: list[str] = []

    if include_technical:
        technical_selected = _select_for_flow(TECHNICAL_POOL, k=thompson_k)
        thompson_selections["technical"] = technical_selected

    if include_astro:
        astro_selected = _select_for_flow(
            ASTRO_POOL,
            excluded=technical_selected,
            k=thompson_k,
        )
        thompson_selections["astro"] = astro_selected

    if include_electional:
        electoral_selected = _select_for_flow(ELECTORAL_POOL, k=1)
        thompson_selections["electoral"] = electoral_selected

    print(f"[Thompson] technical: {technical_selected}")
    print(f"[Thompson] astro:     {astro_selected}")

    # ── Step 5: Run flows in parallel ────────────────────────────────────────
    flow_tasks = []

    if include_technical:
        flow_tasks.append(run_technical_flow(state, selected_agents=technical_selected))

    if include_astro:
        flow_tasks.append(run_astro_flow(state, selected_agents=astro_selected))

    if include_electional:
        flow_tasks.append(run_electoral_flow(state))

    if flow_tasks:
        flow_results = await asyncio.gather(*flow_tasks, return_exceptions=True)

        for result in flow_results:
            if isinstance(result, dict):
                for key, value in result.items():
                    if key.endswith("_signal") and value is not None:
                        state["all_signals"].append(value)

        if not state["all_signals"]:
            fallback_response = AgentResponse(
                agent_name="SystemFallback",
                signal=SignalDirection.NEUTRAL,
                confidence=30,
                reasoning="All agents failed to produce a signal.",
            )
            state["all_signals"].append(fallback_response)

    # ── Step 6: Run KARL Synthesis (AMRE post-processing) ───────────────────
    karl_agent = KARLSynthesisAgent(
        sync_interval=sync_interval,
        enable_self_question=enable_self_question,
        enable_backtest=enable_backtest,
    )
    try:
        karl_result = await karl_agent.run(state)
        synthesis_result = karl_result.get("synthesis_result")
        amre_output = karl_result.get("amre_output")
        decision_record = karl_result.get("decision_record")
        karl_diagnostics = karl_result.get("karl_diagnostics")
    except Exception as e:
        print(f"[KARLSynthesisAgent] Fell back to base synthesis: {e}")
        # Fallback to base synthesis
        synthesis_agent = SynthesisAgent()
        synthesis_result = await synthesis_agent.run(state)
        synthesis_result = synthesis_result.to_dict() if hasattr(synthesis_result, 'to_dict') else synthesis_result
        amre_output = None
        decision_record = None
        karl_diagnostics = None

    # ── Step 7: Build final output ───────────────────────────────────────────
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
        "thompson_selections": thompson_selections,
        "agent_count": len(state["all_signals"]),
        "final_recommendation": synthesis_result,
        "final_report": synthesis_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # KARL-013 additions
        "karl_enabled": True,
        "decision_record": decision_record,
        "amre_output": amre_output,
        "karl_diagnostics": karl_diagnostics,
    }

    if persist:
        save_session(final_output)
        update_beliefs_from_session(final_output)

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


# ─── KARL Diagnostics CLI ───────────────────────────────────────────────────────

async def karl_diagnostics():
    """Print full KARL system diagnostics."""
    agent = get_karl_agent()
    status = agent.get_status()
    print("\n╔══════════════════════════════════════════════╗")
    print("║      ATOM-KARL-013: System Diagnostics      ║")
    print("╚══════════════════════════════════════════════╝")
    print(f"\n📊 Decision Count: {status['decision_counter']}")
    print(f"🔄 Sync Interval: {status['sync_interval']}")
    print(f"❓ Self-Questioning: {'ON' if status['self_question_enabled'] else 'OFF'}")
    print(f"🧪 Backtest: {'ON' if status['backtest_enabled'] else 'OFF'}")

    diag = status.get("karl_diagnostics", {})
    oap = diag.get("oap_kpi", {})
    print(f"\n📈 OAP KPIs:")
    print(f"   TTC Depth:   {oap.get('current_ttc_depth', 'N/A')}")
    print(f"   OOS Fail %: {oap.get('oos_fail_rate', 'N/A')}")
    print(f"   Entropy:    {oap.get('entropy_avg', 'N/A')}")

    audit = diag.get("audit_summary", {})
    print(f"\n📋 Audit Log:")
    print(f"   Total Decisions: {audit.get('total', 0)}")
    print(f"   Avg Confidence:  {audit.get('avg_confidence_final', 0)}")
    print(f"   Action Dist:     {audit.get('action_distribution', {})}")

    drift = status.get("drift_status", {})
    print(f"\n🔍 Drift Analysis:")
    print(f"   Status: {drift.get('status', 'N/A')}")
    if drift.get("status") == "degrading":
        print(f"   ⚠️  Confidence drift: {drift.get('confidence_drift', 0)}")
        print(f"   ⚠️  Uncertainty drift: {drift.get('uncertainty_drift', 0)}")

    print()


if __name__ == "__main__":
    # Delegate to karl_cli for all CLI entry points
    from orchestration import karl_cli
    asyncio.run(karl_cli.main())
