from typing import Literal
from src.graph.state import AgentState


def should_continue(state: AgentState) -> Literal["fetch_market_data", "fetch_astro", "agents"]:
    """Decide which branch to run based on state."""
    # First run: fetch data
    if state["market_data"] is None:
        return "fetch_market_data"
    if state["astro_signal"] is None:
        return "fetch_astro"
    return "agents"


def should_fetch_astro(state: AgentState) -> Literal["fetch_astro", "agents"]:
    """After market data, decide if we need astro."""
    if state["astro_signal"] is None:
        return "fetch_astro"
    return "agents"


def route_to_agents(state: AgentState) -> Literal["market_analyst", "bull_researcher", "bear_researcher", "astrologer", "synthesizer"]:
    """Route to agents - in parallel we run all, but this is for sequential fallback."""
    # For parallel execution, agents run independently
    # This is mainly for the conditional edge
    return "synthesizer"  # After all agents, go to synthesizer
