from langgraph.graph import StateGraph, START, END
from src.graph.state import AgentState, create_initial_state
from src.graph.nodes import (
    fetch_market_data, fetch_astro,
    run_market_analyst, run_bull_researcher, run_bear_researcher,
    run_astrologer, run_synthesizer
)
from src.types import Symbol, TimeFrame


def create_sentinel_graph():
    """Build and compile the AstroFin Sentinel agent graph."""
    
    workflow = StateGraph(AgentState)
    
    # Data fetching nodes
    workflow.add_node("fetch_market_data", fetch_market_data)
    workflow.add_node("fetch_astro", fetch_astro)
    
    # Agent nodes
    workflow.add_node("market_analyst", run_market_analyst)
    workflow.add_node("bull_researcher", run_bull_researcher)
    workflow.add_node("bear_researcher", run_bear_researcher)
    workflow.add_node("astrologer", run_astrologer)
    workflow.add_node("synthesizer", run_synthesizer)
    
    # Edges
    workflow.add_edge(START, "fetch_market_data")
    workflow.add_edge("fetch_market_data", "fetch_astro")
    
    # Agents run in parallel after data is fetched
    workflow.add_edge("fetch_astro", "market_analyst")
    workflow.add_edge("fetch_astro", "bull_researcher")
    workflow.add_edge("fetch_astro", "bear_researcher")
    workflow.add_edge("fetch_astro", "astrologer")
    
    # After all agents complete, synthesizer
    workflow.add_edge("market_analyst", "synthesizer")
    workflow.add_edge("bull_researcher", "synthesizer")
    workflow.add_edge("bear_researcher", "synthesizer")
    workflow.add_edge("astrologer", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()


# Singleton graph instance
_sentinel_graph = None


def get_sentinel_graph():
    global _sentinel_graph
    if _sentinel_graph is None:
        _sentinel_graph = create_sentinel_graph()
    return _sentinel_graph


def run_analysis(symbol: Symbol, timeframe: TimeFrame = TimeFrame.HOUR_4, question: str = "") -> dict:
    """Main entry point to run a full analysis."""
    graph = get_sentinel_graph()
    initial_state = create_initial_state(symbol, timeframe, question)
    
    result = graph.invoke(initial_state)
    return result["board_vote"]
