"""Tests for QuantAgent."""

import pytest
from backend.agents.quant.quant_agent import QuantAgent
from backend.agents.base_agent import Signal


class TestQuantAgent:
    """Test QuantAgent."""

    @pytest.fixture
    def agent(self):
        return QuantAgent()

    @pytest.mark.asyncio
    async def test_quant_agent_init(self, agent):
        assert agent.name == "QuantAgent"

    @pytest.mark.asyncio
    async def test_quant_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "QuantAgent"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_quant_agent_metadata(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "momentum" in metadata or "symbol" in metadata

    @pytest.mark.asyncio
    async def test_quant_agent_analyze(self, agent):
        result = await agent.analyze({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "QuantAgent"
