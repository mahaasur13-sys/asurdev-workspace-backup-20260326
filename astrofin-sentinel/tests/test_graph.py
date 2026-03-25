"""Tests for AstroFin Sentinel graph."""
import pytest
from src.graph.state import create_initial_state, AgentState
from src.types import Symbol, TimeFrame


def test_create_initial_state():
    state = create_initial_state(Symbol.BTC, TimeFrame.HOUR_4, "What about BTC?")
    
    assert state["symbol"] == Symbol.BTC
    assert state["timeframe"] == TimeFrame.HOUR_4
    assert state["user_question"] == "What about BTC?"
    assert state["market_data"] is None
    assert state["astro_signal"] is None
    assert state["board_vote"] is None
    assert len(state["errors"]) == 0


def test_state_has_all_agent_fields():
    state = create_initial_state(Symbol.ETH, TimeFrame.DAY_1)
    
    assert state["market_analyst_opinion"] is None
    assert state["bull_opinion"] is None
    assert state["bear_opinion"] is None
    assert state["astro_opinion"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
