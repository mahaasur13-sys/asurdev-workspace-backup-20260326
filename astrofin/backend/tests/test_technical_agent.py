"""Tests for TechnicalAgent."""

import pytest
from backend.agents.technical.technical_agent import TechnicalAgent
from backend.agents.base_agent import Signal


class TestTechnicalAgent:
    """Test TechnicalAgent."""

    @pytest.fixture
    def agent(self):
        return TechnicalAgent()

    @pytest.mark.asyncio
    async def test_technical_agent_init(self, agent):
        assert agent.name == "TechnicalAgent"

    @pytest.mark.asyncio
    async def test_technical_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "TechnicalAgent"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_technical_agent_metadata(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "rsi" in metadata or "bollinger" in metadata

    @pytest.mark.asyncio
    async def test_technical_agent_analyze(self, agent):
        result = await agent.analyze({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "TechnicalAgent"
