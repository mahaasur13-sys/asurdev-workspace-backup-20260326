"""Tests for OptionsFlowAgent."""

import pytest
from backend.agents.options_flow.options_flow_agent import OptionsFlowAgent
from backend.agents.base_agent import Signal


class TestOptionsFlowAgent:
    """Test OptionsFlowAgent."""

    @pytest.fixture
    def agent(self):
        return OptionsFlowAgent()

    @pytest.mark.asyncio
    async def test_options_flow_agent_init(self, agent):
        assert agent.name == "OptionsFlowAgent"

    @pytest.mark.asyncio
    async def test_options_flow_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "OptionsFlowAgent"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_options_flow_agent_metadata(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "gamma_exposure" in metadata or "unusual_volume" in metadata

    @pytest.mark.asyncio
    async def test_options_flow_agent_analyze(self, agent):
        result = await agent.analyze({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "OptionsFlowAgent"
