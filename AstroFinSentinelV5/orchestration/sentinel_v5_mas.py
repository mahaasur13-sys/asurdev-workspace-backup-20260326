""""orchestration/sentinel_v5_mas.py - ATOM-R-025: MASFactory Integration"""
import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from mas_factory import MASFactoryArchitect, TopologyExecutor
from mas_factory import get_meta_questioning_engine as get_meta_questioning
from mas_factory.topology import Topology
from agents.base_agent import AgentResponse, SignalDirection
from orchestration.router import route_query
from core.history_db import save_session
from core.belief import update_beliefs_from_session

try:
    from db import is_postgres_available, init_db_if_needed
    from db.repositories import DecisionRecordRepository
    PG_AVAILABLE = is_postgres_available()
except Exception:
    PG_AVAILABLE = False


async def run_sentinel_v5_mas(
    user_query: str,
    symbol: str = "BTCUSDT",
    timeframe: str = "SWING",
    current_price: float = 0.0,
    birth_data: dict = None,
    session_id: str = None,
    persist: bool = True,
    enable_meta_questioning: bool = True,
) -> dict:
    if not session_id:
        session_id = str(uuid.uuid4())[:8]

    route_output = route_query(user_query)
    print("[MASFactory] Query:", user_query)
    print("[Router] Query type:", route_output.query_type.value)

    symbols = route_output.symbols or [symbol]
    timeframe = route_output.timeframe or timeframe

    if current_price == 0 and symbols:
        current_price = await _fetch_price(symbols[0])
    current_price = current_price or 50000

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

    print()
    print("[MASFactory] Building topology...")
    architect = MASFactoryArchitect()
    karl_context = {"enable_meta_questioning": enable_meta_questioning, "symbol": symbols[0], "timeframe": timeframe}
    topology = architect.build(intention=user_query, context=karl_context)
    print("[MASFactory] Topology:", topology.hash[:8])
    print("[MASFactory] Roles:", [r.name for r in topology.roles])
    print("[MASFactory] Switches:", len(topology.switch_nodes))

    meta_questions = []
    if enable_meta_questioning:
        print()
        print("[MetaQuestioning] Generating meta-questions...")
        meta = get_meta_questioning()
        ctx = {"confidence": 50, "regime": state.get("regime", "NORMAL")}
        questions = meta.generate_questions(ctx)
        if questions:
            print("[MetaQuestioning] Generated", len(questions), "questions")
            answers = meta.ask(questions, state)
            passed = meta.evaluate(answers)
            if not passed:
                print("[MetaQuestioning] Self-questioning FAILED")
                state["meta_question_bias"] = True
                state["meta_questions"] = answers

    topology.state = state
    print()
    print("[Executor] Running topology...")
    executor = TopologyExecutor(topology, state)
    results = await executor.run()

    signals = []
    for role_id, result in results.items():
        if isinstance(result, dict) and "signal" in result:
            signals.append(result)
    state["all_signals"] = signals

    from agents.synthesis_agent import SynthesisAgent
    synth = SynthesisAgent()
    try:
        synth_result = await synth.run(state)
        if hasattr(synth_result, "to_dict"):
            synth_result = synth_result.to_dict()
    except Exception as e:
        print("[SynthesisAgent] Error:", e)
        synth_result = {"signal": "NEUTRAL", "confidence": 50, "reasoning": "Synthesis failed"}

    exec_summary = executor.get_execution_summary()
    final_output = {
        "session_id": session_id,
        "symbol": symbols[0],
        "timeframe": timeframe,
        "current_price": current_price,
        "query_type": route_output.query_type.value,
        "flows_run": {"mas_factory": True, "roles": [r.name for r in topology.roles]},
        "agent_count": len(results),
        "final_recommendation": synth_result,
        "final_report": synth_result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "topology": topology.to_dict(),
        "topology_hash": topology.hash,
        "execution_log": exec_summary["execution_log"],
        "meta_questions": meta_questions,
        "karl_enabled": True,
        "mas_factory_mode": True,
    }

    if persist:
        save_session(final_output)
        update_beliefs_from_session(final_output)
        if PG_AVAILABLE:
            try:
                init_db_if_needed()
                repo = DecisionRecordRepository()
                repo.save_decision_record(
                    session_id=session_id, symbol=symbols[0], price=current_price,
                    regime=state.get("regime", "NORMAL"),
                    final_action=synth_result.get("signal", "NEUTRAL"),
                    confidence=synth_result.get("confidence", 50),
                    q_star=state.get("q_star", 0.5),
                    uncertainty=state.get("uncertainty", {}),
                    trajectory_data=topology.to_dict(),
                    meta_questions=meta_questions,
                )
            except Exception as e:
                print("[DB] PostgreSQL save failed:", e)

    return final_output


async def _fetch_price(symbol: str) -> float:
    try:
        import requests
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        return float(data.get("price", 0))
    except Exception:
        return 0.0


if __name__ == "__main__":
    import sys
    sep = "=" * 60
    print(sep)
    print("ASTROFIN SENTINEL v5 -- MASFACTORY MODE")
    print(sep)
    
    query = sys.argv[2] if len(sys.argv) > 2 else "Analyze BTC"
    symbol = sys.argv[3] if len(sys.argv) > 3 else "BTCUSDT"
    timeframe = sys.argv[4] if len(sys.argv) > 4 else "SWING"
    
    result = asyncio.run(run_sentinel_v5_mas(user_query=query, symbol=symbol, timeframe=timeframe))
    
    sep = "=" * 60
    print()
    print(sep)
    sig = result["final_recommendation"].get("signal", "?")
    conf = result["final_recommendation"].get("confidence", 0)
    print("RESULT:", sig, "conf=", conf)
    print("Topology:", result["topology_hash"][:8])
    print("Roles:", len(result["flows_run"]["roles"]))
    print("Steps:", len(result["execution_log"]))
