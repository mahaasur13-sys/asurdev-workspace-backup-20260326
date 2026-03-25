"""
LangGraph Orchestrator — Linear Adaptive Router + Corrective RAG
Updated: 2026-03-24
"""

from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal
from datetime import datetime
import os

from src.graph_v2.state import AgentState, RetrievalState
from src.graph_v2.prompts import (
    BULL_RESEARCHER_PROMPT,
    BEAR_RESEARCHER_PROMPT,
    SYNTHESIZER_PROMPT,
)

llm = None  # Lazy init

def _get_llm():
    global llm
    if llm is None:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0.0)
    return llm

checkpointer = MemorySaver()


# =============================================================================
# ROUTER FUNCTIONS
# =============================================================================

def should_retrieve(state: AgentState) -> Literal["retrieve", "bull", "bear"]:
    """
    Conditional edge after technical analysis.
    - confidence < 0.8 OR rare_pattern detected → "retrieve"
    - confidence >= 0.8 AND bullish bias → "bull"
    - confidence >= 0.8 AND bearish bias → "bear"
    """
    tech_result = state.get("technical_result")
    if not tech_result:
        return "bull"

    if hasattr(tech_result, "model_dump"):
        tech_dict = tech_result.model_dump()
    else:
        tech_dict = tech_result or {}

    confidence = tech_dict.get("confidence", 0.5)
    rare_patterns = tech_dict.get("patterns", {}).get("rare_patterns", [])
    signal = tech_dict.get("patterns", {}).get("signal", "neutral")

    if confidence < 0.8 or rare_patterns:
        return "retrieve"

    if signal == "bullish":
        return "bull"
    elif signal == "bearish":
        return "bear"
    return "retrieve"


def after_critique(state: AgentState) -> Literal["corrective", "bull", "bear"]:
    """Conditional edge after self_critique."""
    rs = state.get("retrieval_state", {})
    if hasattr(rs, "model_dump"):
        rs = rs.model_dump()

    relevance = rs.get("self_critique_score", 0.5)
    corrections = rs.get("corrective_rag_iterations", 0)
    adjusted_conf = rs.get("adjusted_confidence", 0.5)

    if relevance < 0.5 and corrections < 2:
        return "corrective"

    return "bull" if adjusted_conf > 0.6 else "bear"


def after_corrective(state: AgentState) -> Literal["retrieve", "bull", "bear"]:
    """Conditional edge after corrective RAG."""
    rs = state.get("retrieval_state", {})
    if hasattr(rs, "model_dump"):
        rs = rs.model_dump()

    corrections = rs.get("corrective_rag_iterations", 0)
    max_corr = rs.get("max_corrective_rag", 2)
    relevance = rs.get("self_critique_score", 0.5)

    if corrections < max_corr and relevance < 0.5:
        return "retrieve"

    adjusted_conf = rs.get("adjusted_confidence", 0.5)
    return "bull" if adjusted_conf > 0.6 else "bear"


# =============================================================================
# NODES
# =============================================================================

def technical_node(state: AgentState) -> AgentState:
    from src.graph_v2.tools.technical_node import technical_analysis_node
    return technical_analysis_node(state)


def retrieve_node(state: AgentState) -> AgentState:
    from src.graph_v2.tools.technical_kb import (
        retrieve_similar_cases, get_rag_strategy,
        build_adaptive_query, build_feature_vector,
    )

    tech_result = state.get("technical_result")
    tech_dict = (tech_result.model_dump() if hasattr(tech_result, "model_dump") else tech_result) or {}

    strategy = get_rag_strategy(tech_dict)
    query = build_adaptive_query(tech_dict, strategy)
    fv = tech_dict.get("feature_vector") or build_feature_vector(tech_dict)

    try:
        cases = retrieve_similar_cases(feature_vector=fv, n_results=5, symbol_filter=state.get("symbol"))
    except Exception as e:
        cases = []
        print(f"[Retrieve] error: {e}")

    rs = state.get("retrieval_state")
    rs = (rs.model_dump() if hasattr(rs, "model_dump") else rs) or RetrievalState().model_dump()
    rs["retrieved_cases"] = cases
    rs["retrieval_strategy"] = strategy
    rs["adaptive_query"] = query

    return {
        "retrieval_state": rs,
        "messages": state.get("messages", []) + [{"role": "system", "content": f"[Retrieve] strategy={strategy}, cases={len(cases)}"}],
    }


def self_critique_node(state: AgentState) -> AgentState:
    from src.graph_v2.tools.technical_kb import evaluate_retrieval_relevance

    tech_result = state.get("technical_result")
    tech_dict = (tech_result.model_dump() if hasattr(tech_result, "model_dump") else tech_result) or {}

    rs = state.get("retrieval_state")
    rs = (rs.model_dump() if hasattr(rs, "model_dump") else rs) or {}

    critique = evaluate_retrieval_relevance(
        technical_result=tech_dict,
        retrieved_cases=rs.get("retrieved_cases", []),
        llm=_get_llm(),
    )

    rs["self_critique_score"] = critique["self_critique_score"]
    rs["self_critique_reasoning"] = critique["self_critique_reasoning"]
    rs["is_relevant"] = critique["is_relevant"]
    rs["adjusted_confidence"] = critique["adjusted_confidence"]

    return {
        "retrieval_state": rs,
        "messages": state.get("messages", []) + [{"role": "system", "content": f"[SelfCritique] score={critique['self_critique_score']:.2f}, relevant={critique['is_relevant']}"}],
    }


def corrective_node(state: AgentState) -> AgentState:
    from src.graph_v2.tools.technical_kb import (
        retrieve_similar_cases, evaluate_retrieval_relevance,
        reformulate_query, build_feature_vector,
    )

    tech_result = state.get("technical_result")
    tech_dict = (tech_result.model_dump() if hasattr(tech_result, "model_dump") else tech_result) or {}

    rs = state.get("retrieval_state")
    rs = (rs.model_dump() if hasattr(rs, "model_dump") else rs) or {}

    current_iter = rs.get("corrective_rag_iterations", 0)
    rs["adaptive_query"] = reformulate_query(
        original_query=f"{state.get('symbol')} {state.get('timeframe')} technical",
        technical_result=tech_dict,
        failed_retrieval_reason=rs.get("self_critique_reasoning", ""),
        llm=_get_llm(),
    )

    fv = tech_dict.get("feature_vector") or build_feature_vector(tech_dict)
    try:
        cases = retrieve_similar_cases(feature_vector=fv, n_results=5, symbol_filter=state.get("symbol"))
    except:
        cases = []

    rs["retrieved_cases"] = cases
    rs["corrective_rag_iterations"] = current_iter + 1

    critique = evaluate_retrieval_relevance(technical_result=tech_dict, retrieved_cases=cases, llm=_get_llm())
    rs["self_critique_score"] = critique["self_critique_score"]
    rs["is_relevant"] = critique["is_relevant"]
    rs["adjusted_confidence"] = critique["adjusted_confidence"]

    return {
        "retrieval_state": rs,
        "messages": state.get("messages", []) + [{"role": "system", "content": f"[Corrective] iter={current_iter + 1}, score={critique['self_critique_score']:.2f}"}],
    }


def _run_specialist(state: AgentState, agent_name: str, system_prompt: str) -> AgentState:
    from langchain_core.messages import HumanMessage
    from src.graph_v2.tools.knowledge import retrieve_knowledge

    tech_result = state.get("technical_result")
    if hasattr(tech_result, "summary"):
        tech_summary = tech_result.summary
    elif hasattr(tech_result, "model_dump"):
        tech_summary = str(tech_result.model_dump())
    else:
        tech_summary = str(tech_result or "N/A")

    rs = state.get("retrieval_state", {})
    rs = rs.model_dump() if hasattr(rs, "model_dump") else rs

    context = f"""Symbol: {state.get('symbol', 'BTC')}
Timeframe: {state.get('timeframe', '4h')}
User Question: {state.get('user_question', 'Analyze this')}

Technical Result: {tech_summary}

Retrieval Strategy: {rs.get('retrieval_strategy', 'N/A')}
Retrieved Cases: {len(rs.get('retrieved_cases', []))}
Adjusted Confidence: {rs.get('adjusted_confidence', 'N/A')}

Astro Data: {state.get('astro_data', 'N/A')}
"""

    knowledge = retrieve_knowledge(
        query=f"{state.get('user_question', '')} {state.get('symbol', 'BTC')}",
        agent_role=agent_name.replace("_", " ").title(),
        jd_ut=state.get("jd_ut"),
    )

    result = _get_llm().invoke([HumanMessage(content=f"{system_prompt}\n\nContext:\n{context}\n\nRetrieved Knowledge:\n{knowledge}")])
    opinion = _parse_opinion(agent_name, result.content)

    return {f"{agent_name}_opinion": opinion, "messages": state.get("messages", []) + [result]}


def bull_node(state: AgentState) -> AgentState:
    return _run_specialist(state, "bull_researcher", BULL_RESEARCHER_PROMPT)


def bear_node(state: AgentState) -> AgentState:
    return _run_specialist(state, "bear_researcher", BEAR_RESEARCHER_PROMPT)


def synthesizer_node(state: AgentState) -> AgentState:
    from langchain_core.messages import HumanMessage

    prompt = SYNTHESIZER_PROMPT.format(
        symbol=state.get("symbol", "BTC"),
        timeframe=state.get("timeframe", "4h"),
        bull_researcher=state.get("bull_researcher_opinion", {}).get("content", "No opinion"),
        bear_researcher=state.get("bear_researcher_opinion", {}).get("content", "No opinion"),
        astro_data=state.get("astro_data", {}),
    )

    result = _get_llm().invoke([HumanMessage(content=prompt)])
    return {
        "synthesizer_opinion": {"agent_name": "synthesizer", "content": result.content, "decision": "NEUTRAL", "confidence": 0.7, "timestamp": datetime.utcnow().isoformat()},
        "messages": state.get("messages", []) + [result],
    }


def _parse_opinion(agent_name: str, content: str) -> dict:
    import re
    content_upper = content.upper()

    if "STRONG_BUY" in content_upper:
        decision = "STRONG_BUY"
    elif "BUY" in content_upper:
        decision = "BUY"
    elif "STRONG_SELL" in content_upper:
        decision = "STRONG_SELL"
    elif "SELL" in content_upper:
        decision = "SELL"
    else:
        decision = "NEUTRAL"

    confidence = 0.5
    for line in content.split("\n"):
        if "confidence" in line.lower():
            m = re.search(r"0\.\d+", line)
            if m:
                confidence = float(m.group())

    return {"agent_name": agent_name, "content": content, "decision": decision, "confidence": confidence, "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# BUILD GRAPH
# =============================================================================

def create_orchestrator_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("technical", technical_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("self_critique", self_critique_node)
    workflow.add_node("corrective", corrective_node)
    workflow.add_node("bull", bull_node)
    workflow.add_node("bear", bear_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "technical")

    workflow.add_conditional_edges(
        "technical",
        should_retrieve,
        {"retrieve": "retrieve", "bull": "bull", "bear": "bear"},
    )

    workflow.add_edge("retrieve", "self_critique")

    workflow.add_conditional_edges(
        "self_critique",
        after_critique,
        {"corrective": "corrective", "bull": "bull", "bear": "bear"},
    )

    workflow.add_conditional_edges(
        "corrective",
        after_corrective,
        {"retrieve": "retrieve", "bull": "bull", "bear": "bear"},
    )

    workflow.add_edge("bull", "synthesizer")
    workflow.add_edge("bear", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow.compile(checkpointer=checkpointer)


_orchestrator_graph = None

def get_orchestrator_graph():
    global _orchestrator_graph
    if _orchestrator_graph is None:
        _orchestrator_graph = create_orchestrator_graph()
    return _orchestrator_graph


def run_analysis(symbol: str, timeframe: str = "4h", user_question: str = "") -> dict:
    from src.graph_v2.tools.astro import create_swiss_ephemeris_tool

    swiss = create_swiss_ephemeris_tool()
    astro_result = swiss.invoke({})
    jd_ut = astro_result.get("jd_ut") if isinstance(astro_result, dict) else None

    graph = get_orchestrator_graph()
    initial_state = {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "user_question": user_question,
        "jd_ut": jd_ut,
        "market_data": None,
        "astro_data": {"raw": astro_result, "fetched_at": datetime.utcnow().isoformat()},
        "technical_result": None,
        "retrieval_state": None,
        "retrieval_history": [],
        "knowledge_context": None,
        "market_analyst_opinion": None,
        "bull_researcher_opinion": None,
        "bear_researcher_opinion": None,
        "muhurta_specialist_opinion": None,
        "synthesizer_opinion": None,
        "final_vote": None,
        "messages": [],
        "errors": [],
    }

    result = graph.invoke(initial_state)
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "final_vote": result.get("final_vote"),
        "technical_result": result.get("technical_result"),
        "retrieval_state": result.get("retrieval_state"),
        "agent_opinions": {
            "bull_researcher": result.get("bull_researcher_opinion"),
            "bear_researcher": result.get("bear_researcher_opinion"),
        },
        "astro_data": result.get("astro_data"),
        "jd_ut": result.get("jd_ut"),
        "messages": result.get("messages", []),
    }
