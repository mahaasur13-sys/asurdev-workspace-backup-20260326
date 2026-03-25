"""Tests for FundamentalAgent."""

import pytest
from backend.agents.fundamental.fundamental_agent import FundamentalAgent
from backend.agents.base_agent import Signal


class TestFundamentalAgent:
    """Test FundamentalAgent."""

    @pytest.fixture
    def agent(self):
        return FundamentalAgent()

    @pytest.mark.asyncio
    async def test_fundamental_agent_init(self, agent):
        assert agent.name == "FundamentalAgent"
        assert "fundamental" in agent.system_prompt.lower()

    @pytest.mark.asyncio
    async def test_fundamental_agent_run_btc(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "FundamentalAgent"
        assert result.signal in [Signal.LONG, Signal.SHORT, Signal.NEUTRAL, Signal.AVOID]
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning != ""

    @pytest.mark.asyncio
    async def test_fundamental_agent_run_eth(self, agent):
        result = await agent.run({"symbol": "ETH", "price": 3500.0})
        assert result.agent_name == "FundamentalAgent"
        assert result.signal in Signal

    @pytest.mark.asyncio
    async def test_fundamental_agent_context_price(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "symbol" in metadata or "fear_greed" in metadata or "fundamentals" in metadata

    @pytest.mark.asyncio
    async def test_fundamental_agent_analyze(self, agent):
        result = await agent.analyze({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "FundamentalAgent"
        assert result.signal in Signal

    @pytest.mark.asyncio
    async def test_fundamental_agent_to_dict(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        d = result.to_dict()
        assert "agent_name" in d
        assert "signal" in d
        assert "confidence" in d
        assert "reasoning" in d
