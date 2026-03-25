"""Tests for MacroAgent."""

import pytest
from backend.agents.macro.macro_agent import MacroAgent
from backend.agents.base_agent import Signal


class TestMacroAgent:
    """Test MacroAgent."""

    @pytest.fixture
    def agent(self):
        return MacroAgent()

    @pytest.mark.asyncio
    async def test_macro_agent_init(self, agent):
        assert agent.name == "MacroAgent"

    @pytest.mark.asyncio
    async def test_macro_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "MacroAgent"
        assert result.signal in [Signal.LONG, Signal.SHORT, Signal.NEUTRAL, Signal.AVOID]
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning != ""

    @pytest.mark.asyncio
    async def test_macro_agent_metadata(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "vix" in metadata or "fear_greed" in metadata or "dxy" in metadata

    @pytest.mark.asyncio
    async def test_macro_agent_analyze(self, agent):
        result = await agent.analyze({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "MacroAgent"
