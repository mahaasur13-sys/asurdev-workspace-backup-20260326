"""
LangGraph Multi-Agent Supervisor Compiler.
Updated: 2026-03-24 — Technical Node + Adaptive RAG Router + Corrective RAG
"""

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import MemorySaver
from langgraph.store.memory import InMemoryStore
from typing import Literal, Annotated, Optional
from datetime import datetime
import os

from src.graph_v2.state import AgentState, TeamState
from src.graph_v2.tools.registry import get_all_tools
from src.graph_v2.tools.knowledge import retrieve_knowledge
from src.graph_v2.tools.astro import create_swiss_ephemeris_tool
from src.graph_v2.tools.technical_node import technical_analysis_node
from src.graph_v2.tools.technical_kb import (
    retrieve_similar_cases,
    evaluate_retrieval_relevance,
    reformulate_query,
    should_skip_rag,
    get_rag_strategy,
    build_adaptive_query,
)
from src.graph_v2.prompts import (
    SUPERVISOR_PROMPT,
    MARKET_ANALYST_PROMPT,
    BULL_RESEARCHER_PROMPT,
    BEAR_RESEARCHER_PROMPT,
    MUHURTA_SPECIALIST_PROMPT,
    SYNTHESIZER_PROMPT,
)

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0
)

checkpointer = MemorySaver()
in_memory_store = InMemoryStore()


# =============================================================================
# TECHNICAL NODE
# =============================================================================

def technical_node(state: AgentState) -> AgentState:
    """Wrapper for technical analysis + Adaptive RAG."""
    return technical_analysis_node(state)


# =============================================================================
# ADAPTIVE RAG PIPELINE NODES
# =============================================================================

def retrieve_similar_cases_node(state: AgentState) -> AgentState:
    """Retrieve similar historical cases from Chroma."""
    from src.graph_v2.tools.technical_kb import retrieve_similar_cases, build_feature_vector
    from src.graph_v2.state import RetrievalState
    
    technical_result = state.get("technical_result")
    if not technical_result or not technical_result.feature_vector:
        return state
    
    try:
        cases = retrieve_similar_cases(
            feature_vector=technical_result.feature_vector,
            n_results=5,
            symbol_filter=state.get("symbol")
        )
    except Exception as e:
        cases = []
    
    retrieval_state = state.get("retrieval_state")
    if retrieval_state and hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    elif not retrieval_state:
        retrieval_state = RetrievalState().model_dump()
    
    retrieval_state["retrieved_cases"] = cases
    
    return {
        "retrieval_state": retrieval_state,
        "retrieved_cases": cases,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": f"Retrieved {len(cases)} similar cases"}
        ]
    }


def self_critique_node(state: AgentState) -> AgentState:
    """Self-Critique: Evaluate if retrieved cases are relevant."""
    from src.graph_v2.tools.technical_kb import evaluate_retrieval_relevance
    
    technical_result = state.get("technical_result")
    retrieval_state = state.get("retrieval_state")
    
    if hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    if hasattr(technical_result, 'model_dump'):
        technical_result = technical_result.model_dump()
    
    cases = retrieval_state.get("retrieved_cases", [])
    
    critique = evaluate_retrieval_relevance(
        technical_result=technical_result,
        retrieved_cases=cases,
        llm=llm
    )
    
    retrieval_state["self_critique_score"] = critique["self_critique_score"]
    retrieval_state["self_critique_reasoning"] = critique["self_critique_reasoning"]
    retrieval_state["is_rag_relevant"] = critique["is_relevant"]
    
    if hasattr(state.get("technical_result"), 'confidence'):
        state["technical_result"].confidence = critique["adjusted_confidence"]
    
    # Append to retrieval_history for adaptive router's memory
    retrieval_history = state.get("retrieval_history", [])
    retrieval_history.append({
        "query": retrieval_state.get("adaptive_query", ""),
        "relevance_score": critique["self_critique_score"],
        "adjusted_confidence": critique["adjusted_confidence"],
        "cases_retrieved": len(cases),
        "strategy": retrieval_state.get("retrieval_strategy", "unknown")
    })
    
    return {
        "retrieval_state": retrieval_state,
        "retrieval_history": retrieval_history,
        "retrieval_relevance": critique["self_critique_score"],
        "adjusted_confidence": critique["adjusted_confidence"],
        "retrieved_cases": cases,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": f"Self-critique: score={critique['self_critique_score']:.2f}, relevant={critique['is_relevant']}"}
        ]
    }


def corrective_rag_node(state: AgentState) -> AgentState:
    """Corrective RAG: Reformulate query and retry retrieval."""
    from src.graph_v2.tools.technical_kb import retrieve_similar_cases, evaluate_retrieval_relevance, reformulate_query
    
    technical_result = state.get("technical_result")
    retrieval_state = state.get("retrieval_state")
    
    if hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    if hasattr(technical_result, 'model_dump'):
        technical_result = technical_result.model_dump()
    
    current_iter = retrieval_state.get("corrective_rag_iterations", 0)
    max_iter = retrieval_state.get("max_corrective_rag", 2)
    
    if current_iter >= max_iter:
        retrieval_state["final_confidence"] = technical_result.get("confidence", 0.5) * 0.7
        retrieval_state["is_rag_relevant"] = False
        return {
            "retrieval_state": retrieval_state,
            "adjusted_confidence": retrieval_state["final_confidence"],
            "correction_count": current_iter
        }
    
    reformulated = reformulate_query(
        original_query=f"{state.get('symbol')} {state.get('timeframe')} technical",
        technical_result=technical_result,
        failed_retrieval_reason=retrieval_state.get("self_critique_reasoning", ""),
        llm=llm
    )
    
    try:
        new_cases = retrieve_similar_cases(
            feature_vector=technical_result.get("feature_vector", []),
            n_results=5,
            symbol_filter=state.get("symbol")
        )
    except:
        new_cases = []
    
    retrieval_state["retrieved_cases"] = new_cases
    retrieval_state["corrective_rag_iterations"] = current_iter + 1
    
    critique = evaluate_retrieval_relevance(
        technical_result=technical_result,
        retrieved_cases=new_cases,
        llm=llm
    )
    
    retrieval_state["self_critique_score"] = critique["self_critique_score"]
    retrieval_state["self_critique_reasoning"] = critique["self_critique_reasoning"]
    retrieval_state["is_rag_relevant"] = critique["is_relevant"]
    
    current_count = state.get("correction_count", 0)
    
    if critique["is_relevant"]:
        retrieval_state["final_confidence"] = critique["adjusted_confidence"]
    
    return {
        "retrieval_state": retrieval_state,
        "correction_count": current_count + 1,
        "adjusted_confidence": critique["adjusted_confidence"],
        "retrieval_relevance": critique["self_critique_score"],
        "retrieved_cases": new_cases,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": f"Corrective RAG iter {current_iter + 1}"}
        ]
    }


# =============================================================================
# ROUTERS
# =============================================================================

def adaptive_router_node(state: AgentState) -> Literal["direct", "retrieve_similar_cases"]:
    """ADAPTIVE ROUTER: Decide whether to use RAG or go directly to specialists.
    
    Decision Logic (from should_skip_rag):
        1. High confidence (>= 0.82) → SKIP RAG, go direct
        2. Low confidence (<= 0.35) → SKIP RAG, go direct
        3. Rare pattern detected → USE RAG
        4. Past RAG was impactful → USE RAG
        5. Default → SKIP RAG
    """
    from src.graph_v2.tools.technical_kb import should_skip_rag
    
    technical_result = state.get("technical_result")
    
    if not technical_result:
        return "direct"
    
    # Convert to dict if Pydantic model
    if hasattr(technical_result, 'model_dump'):
        tech_dict = technical_result.model_dump()
    else:
        tech_dict = technical_result
    
    # Get retrieval history from state (if available)
    retrieval_history = state.get("retrieval_history", [])
    
    # Use should_skip_rag to decide
    skip_rag, reason = should_skip_rag(tech_dict, retrieval_history)
    
    print(f"[AdaptiveRouter] skip_rag={skip_rag}, reason={reason}")
    
    if skip_rag:
        return "direct"
    else:
        return "retrieve_similar_cases"


def adaptive_retrieval_node(state: AgentState) -> AgentState:
    """Adaptive retrieval with strategy-based query building."""
    from src.graph_v2.tools.technical_kb import (
        retrieve_similar_cases, 
        get_rag_strategy, 
        build_adaptive_query,
        build_feature_vector
    )
    from src.graph_v2.state import RetrievalState
    
    technical_result = state.get("technical_result")
    
    if hasattr(technical_result, 'model_dump'):
        tech_dict = technical_result.model_dump()
    else:
        tech_dict = technical_result
    
    # Determine strategy
    strategy = get_rag_strategy(tech_dict)
    print(f"[AdaptiveRetrieval] strategy={strategy}")
    
    # Build optimized query based on strategy
    query = build_adaptive_query(tech_dict, strategy)
    
    # Get feature vector
    feature_vector = tech_dict.get("feature_vector", build_feature_vector(tech_dict))
    
    # Retrieve with adaptive query
    try:
        cases = retrieve_similar_cases(
            feature_vector=feature_vector,
            n_results=5,
            symbol_filter=state.get("symbol")
        )
    except Exception as e:
        cases = []
        print(f"[AdaptiveRetrieval] retrieval error: {e}")
    
    retrieval_state = state.get("retrieval_state")
    if retrieval_state and hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    elif not retrieval_state:
        retrieval_state = RetrievalState().model_dump()
    
    retrieval_state["retrieved_cases"] = cases
    retrieval_state["retrieval_strategy"] = strategy
    retrieval_state["adaptive_query"] = query
    
    return {
        "retrieval_state": retrieval_state,
        "retrieved_cases": cases,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": f"Adaptive retrieval: strategy={strategy}, cases={len(cases)}, query={query}"}
        ]
    }


def rag_relevance_router(state: AgentState) -> Literal["specialists", "corrective_rag"]:
    """Router after Self-Critique."""
    retrieval_state = state.get("retrieval_state", {})
    if hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    
    is_relevant = retrieval_state.get("is_rag_relevant", False)
    retrieval_relevance = retrieval_state.get("self_critique_score", 0.0)
    return {"next": "specialists" if is_relevant else "corrective_rag", "retrieval_relevance": retrieval_relevance}


def corrective_rag_router(state: AgentState) -> Literal["self_critique", "specialists"]:
    """Router after Corrective RAG."""
    retrieval_state = state.get("retrieval_state", {})
    if hasattr(retrieval_state, 'model_dump'):
        retrieval_state = retrieval_state.model_dump()
    
    current_iter = retrieval_state.get("corrective_rag_iterations", 0)
    max_iter = retrieval_state.get("max_corrective_rag", 2)
    
    if current_iter >= max_iter:
        return {"next": "specialists"}
    else:
        return {"next": "self_critique"}


# =============================================================================
# SUPERVISOR LOGIC
# =============================================================================

def supervisor_node(state: AgentState) -> AgentState:
    """Supervisor decides next step in workflow."""
    if not state.get("astro_data"):
        return {"next": "fetch_astro"}
    elif not state.get("market_data"):
        return {"next": "fetch_market"}
    elif not state.get("technical_result"):
        return {"next": "technical"}
    elif not state.get("retrieval_state"):
        return {"next": "adaptive_retrieval"}
    elif not state.get("retrieval_relevance") and state.get("retrieval_relevance") != 0.0:
        return {"next": "self_critique"}
    elif not state.get("bull_researcher_opinion"):
        return {"next": "specialists"}
    elif not state.get("synthesizer_opinion"):
        return {"next": "synthesize"}
    else:
        return {"next": "END"}


def fetch_astro_node(state: AgentState) -> AgentState:
    """Fetch astrological data and store jd_ut for caching."""
    swiss = create_swiss_ephemeris_tool()
    astro_result = swiss.invoke({})
    
    jd_ut = None
    if isinstance(astro_result, dict):
        jd_ut = astro_result.get("jd_ut")
    elif isinstance(astro_result, str):
        import re
        match = re.search(r'jd_ut[\s:]+([0-9.]+)', astro_result)
        if match:
            jd_ut = float(match.group(1))
    
    return {
        "astro_data": {"raw": astro_result, "fetched_at": datetime.utcnow().isoformat()},
        "jd_ut": jd_ut,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": f"Astro fetched, jd_ut={jd_ut}"}
        ]
    }


def fetch_market_node(state: AgentState) -> AgentState:
    """Fetch market data."""
    market_data = {
        "symbol": state.get("symbol", "BTC"),
        "fetched_at": datetime.utcnow().isoformat(),
        "note": "Market data placeholder"
    }
    
    return {
        "market_data": market_data,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": "Market data placeholder"}
        ]
    }
# =============================================================================
# SPECIALIST NODES
# =============================================================================

def create_specialist_node(agent_name: str, system_prompt: str):
    """Factory to create a specialist agent node."""
    from langchain_core.messages import HumanMessage
    
    role_map = {
        "market_analyst": "MarketAnalyst",
        "bull_researcher": "BullResearcher",
        "bear_researcher": "BearResearcher",
        "muhurta_specialist": "MuhurtaSpecialist",
        "synthesizer": "Synthesizer"
    }
    agent_role = role_map.get(agent_name, agent_name)
    
    def node(state: AgentState) -> AgentState:
        tech_result = state.get("technical_result")
        tech_summary = tech_result.summary if tech_result and hasattr(tech_result, 'summary') else str(tech_result)
        
        context = f"""Symbol: {state.get('symbol', 'BTC')}
Timeframe: {state.get('timeframe', '4h')}
User Question: {state.get('user_question', 'Analyze this')}

Market Data: {state.get('market_data', 'N/A')}
Technical Result: {tech_summary}
Retrieval: {state.get('retrieval_state', 'N/A')}
Astro Data: {state.get('astro_data', 'N/A')}
"""
        
        jd_ut = state.get("jd_ut")
        knowledge = retrieve_knowledge(
            query=f"{state.get('user_question', '')} {state.get('symbol', '')}",
            agent_role=agent_role,
            jd_ut=jd_ut
        )
        
        messages = [
            HumanMessage(content=f"{system_prompt}\n\nContext:\n{context}\n\nRetrieved Knowledge:\n{knowledge}"),
        ]
        
        result = llm.invoke(messages)
        opinion = _parse_opinion(agent_name, result.content, state)
        opinion["knowledge_sources"] = [f"retrieve_knowledge:{agent_role}"]
        
        state_key = f"{agent_name}_opinion"
        return {
            state_key: opinion,
            "messages": state.get("messages", []) + [result]
        }
    
    return node


def run_specialists(state: AgentState) -> list[dict]:
    """Fan-out to specialists in parallel using Send API."""
    specialists = ["bull_researcher", "bear_researcher", "muhurta_specialist"]
    
    partial_state = {
        "symbol": state.get("symbol", "BTC"),
        "timeframe": state.get("timeframe", "4h"),
        "user_question": state.get("user_question", ""),
        "market_data": state.get("market_data"),
        "astro_data": state.get("astro_data"),
        "technical_result": state.get("technical_result"),
        "retrieval_state": state.get("retrieval_state"),
        "jd_ut": state.get("jd_ut"),
    }
    
    return [Send(s, partial_state) for s in specialists]


def run_synthesizer(state: AgentState) -> AgentState:
    """Run synthesizer to produce final weighted vote."""
    synthesizer_prompt = SYNTHESIZER_PROMPT.format(
        symbol=state.get("symbol", "BTC"),
        timeframe=state.get("timeframe", "4h"),
        market_analyst=state.get("market_analyst_opinion", {}).get("content", "No opinion"),
        bull_researcher=state.get("bull_researcher_opinion", {}).get("content", "No opinion"),
        bear_researcher=state.get("bear_researcher_opinion", {}).get("content", "No opinion"),
        muhurta_specialist=state.get("muhurta_specialist_opinion", {}).get("content", "No opinion"),
        astro_data=state.get("astro_data", {})
    )
    
    messages = [{"role": "system", "content": synthesizer_prompt}]
    result = llm.invoke(messages)
    
    return {
        "synthesizer_opinion": {
            "agent_name": "synthesizer",
            "content": result.content,
            "decision": "NEUTRAL",
            "confidence": 0.7,
            "timestamp": datetime.utcnow().isoformat()
        },
        "final_vote": _calculate_final_vote(state),
        "messages": state.get("messages", []) + [result]
    }


def _parse_opinion(agent_name: str, content: str, state: AgentState) -> dict:
    """Parse LLM response into structured opinion."""
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
    for line in content.split('\n'):
        if 'confidence' in line.lower():
            match = re.search(r'0\.\d+', line)
            if match:
                confidence = float(match.group())
    
    return {
        "agent_name": agent_name,
        "content": content,
        "decision": decision,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat()
    }


def _calculate_final_vote(state: AgentState) -> dict:
    """Calculate weighted final vote from all opinions."""
    opinions = [
        state.get("market_analyst_opinion", {}),
        state.get("bull_researcher_opinion", {}),
        state.get("bear_researcher_opinion", {}),
        state.get("muhurta_specialist_opinion", {}),
    ]
    
    weights = {
        "market_analyst": 1.0,
        "bull_researcher": 0.8,
        "bear_researcher": 0.8,
        "muhurta_specialist": 0.5,
    }
    
    decision_scores = {
        "STRONG_BUY": 1.0, "BUY": 0.75, "NEUTRAL": 0.5, "SELL": 0.25, "STRONG_SELL": 0.0
    }
    
    total_weight = 0
    weighted_sum = 0
    
    for opinion in opinions:
        if opinion and opinion.get("agent_name"):
            agent = opinion["agent_name"]
            weight = weights.get(agent, 0.5)
            score = decision_scores.get(opinion.get("decision", "NEUTRAL"), 0.5)
            conf = opinion.get("confidence", 0.5)
            
            weighted_sum += weight * score * conf
            total_weight += weight
    
    final_score = weighted_sum / total_weight if total_weight > 0 else 0.5
    
    if final_score > 0.75:
        final_decision = "STRONG_BUY"
    elif final_score > 0.55:
        final_decision = "BUY"
    elif final_score > 0.45:
        final_decision = "NEUTRAL"
    elif final_score > 0.25:
        final_decision = "SELL"
    else:
        final_decision = "STRONG_SELL"
    
    return {
        "final_decision": final_decision,
        "final_score": round(final_score, 2),
        "final_confidence": round(sum(o.get("confidence", 0.5) for o in opinions if o) / max(1, len([o for o in opinions if o])), 2),
        "jd_ut": state.get("jd_ut"),
        "all_opinions": opinions
    }


# =============================================================================
# BUILD GRAPH
# =============================================================================

def create_multi_agent_graph():
    """Build the multi-agent supervisor graph with Adaptive RAG."""
    
    workflow = StateGraph(AgentState)
    
    # Add core nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("fetch_astro", fetch_astro_node)
    workflow.add_node("fetch_market", fetch_market_node)
    workflow.add_node("technical", technical_node)
    workflow.add_node("run_specialists", run_specialists)
    workflow.add_node("synthesizer", run_synthesizer)
    
    # Add Adaptive RAG nodes
    workflow.add_node("adaptive_retrieval", adaptive_retrieval_node)
    workflow.add_node("self_critique", self_critique_node)
    workflow.add_node("corrective_rag", corrective_rag_node)
    
    # Add specialist nodes
    specialist_prompts = {
        "market_analyst": MARKET_ANALYST_PROMPT,
        "bull_researcher": BULL_RESEARCHER_PROMPT,
        "bear_researcher": BEAR_RESEARCHER_PROMPT,
        "muhurta_specialist": MUHURTA_SPECIALIST_PROMPT,
    }
    
    for name, prompt in specialist_prompts.items():
        workflow.add_node(name, create_specialist_node(name, prompt))
    
    # Edges
    workflow.add_edge(START, "supervisor")
    
    # Supervisor routing
    workflow.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next", "supervisor"),
        {
            "fetch_astro": "fetch_astro",
            "fetch_market": "fetch_market",
            "technical": "technical",
            "specialists": "run_specialists",
            "synthesize": "synthesizer",
            "END": END
        }
    )
    
    workflow.add_edge("fetch_astro", "supervisor")
    workflow.add_edge("fetch_market", "supervisor")
    
    # Technical → Adaptive Router
    workflow.add_conditional_edges(
        "technical",
        adaptive_router_node,
        {
            "direct": "run_specialists",
            "retrieve_similar_cases": "adaptive_retrieval"
        }
    )
    
    # RAG pipeline
    workflow.add_edge("adaptive_retrieval", "self_critique")
    
    workflow.add_conditional_edges(
        "self_critique",
        rag_relevance_router,
        {
            "specialists": "run_specialists",
            "corrective_rag": "corrective_rag"
        }
    )
    
    workflow.add_conditional_edges(
        "corrective_rag",
        corrective_rag_router,
        {
            "self_critique": "self_critique",
            "specialists": "run_specialists"
        }
    )
    
    # Specialists fan-out (Send API returns list of partial states)
    workflow.add_edge("run_specialists", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile(
        checkpointer=checkpointer,
        store=in_memory_store
    )


_multi_agent_graph = None


def get_multi_agent_graph():
    global _multi_agent_graph
    if _multi_agent_graph is None:
        _multi_agent_graph = create_multi_agent_graph()
    return _multi_agent_graph


def run_analysis(symbol: str, timeframe: str = "4h", user_question: str = "") -> dict:
    """Run a full multi-agent analysis."""
    graph = get_multi_agent_graph()
    
    initial_state = AgentState(
        symbol=symbol.upper(),
        timeframe=timeframe,
        user_question=user_question,
        jd_ut=None,
        market_data=None,
        astro_data=None,
        technical_result=None,
        retrieval_state=None,
        retrieval_history=[],  # Track past RAG attempts for adaptive routing
        knowledge_context=None,
        market_analyst_opinion=None,
        bull_researcher_opinion=None,
        bear_researcher_opinion=None,
        muhurta_specialist_opinion=None,
        synthesizer_opinion=None,
        final_vote=None,
        messages=[],
        errors=[]
    )
    
    result = graph.invoke(initial_state)
    
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "final_vote": result.get("final_vote"),
        "technical_result": result.get("technical_result"),
        "retrieval_state": result.get("retrieval_state"),
        "agent_opinions": {
            "market_analyst": result.get("market_analyst_opinion"),
            "bull_researcher": result.get("bull_researcher_opinion"),
            "bear_researcher": result.get("bear_researcher_opinion"),
            "muhurta_specialist": result.get("muhurta_specialist_opinion"),
        },
        "astro_data": result.get("astro_data"),
        "jd_ut": result.get("jd_ut"),
        "messages": result.get("messages", [])
    }
