"""Tests for AstroCouncilAgent."""

import pytest
from backend.agents.astro_council.agent import AstroCouncilAgent
from backend.agents.base_agent import Signal
from datetime import datetime


class TestAstroCouncilAgent:
    """Test AstroCouncilAgent."""

    @pytest.fixture
    def agent(self):
        return AstroCouncilAgent()

    @pytest.mark.asyncio
    async def test_astro_council_init(self, agent):
        assert agent.name == "AstroCouncil"
        assert hasattr(agent, "aiq")
        assert hasattr(agent, "memory_bank")

    @pytest.mark.asyncio
    async def test_astro_council_run(self, agent):
        result = await agent.run({
            "symbol": "BTC",
            "price": 68250.0,
            "datetime": datetime.now(),
        })
        assert result.agent_name == "AstroCouncil"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_astro_council_analyze(self, agent):
        result = await agent.analyze({
            "symbol": "BTC",
            "price": 68250.0,
            "datetime": datetime.now(),
        })
        assert result.agent_name == "AstroCouncil"
        assert result.signal in Signal

    @pytest.mark.asyncio
    async def test_astro_council_metadata(self, agent):
        result = await agent.analyze({
            "symbol": "BTC",
            "price": 68250.0,
        })
        assert "ephemeris_summary" in result.metadata
        assert "sub_agents_executed" in result.metadata

    @pytest.mark.asyncio
    async def test_astro_council_weights(self, agent):
        assert hasattr(agent, "WEIGHTS")
        assert len(agent.WEIGHTS) > 0
        total = sum(agent.WEIGHTS.values())
        assert 0.95 <= total <= 1.05  # Allow small rounding errors

    @pytest.mark.asyncio
    async def test_astro_council_eth(self, agent):
        result = await agent.analyze({
            "symbol": "ETH",
            "price": 3500.0,
        })
        assert result.agent_name == "AstroCouncil"
        assert result.signal in Signal

    def test_get_metrics(self, agent):
        metrics = agent.get_metrics()
        assert "active_agents" in metrics
        assert "aiq_metrics" in metrics
        assert "memory_stats" in metrics


class TestAstroCouncilIntegration:
    """Integration tests for AstroCouncilAgent with real data."""

    @pytest.mark.asyncio
    async def test_full_analysis(self):
        """Test full analysis with all agents."""
        agent = AstroCouncilAgent()
        result = await agent.analyze({
            "symbol": "BTC",
            "price": 68250.0,
            "datetime": datetime.now(),
            "timeframe": "SWING",
        })
        assert result.signal in Signal
        assert result.confidence > 0
        assert result.reasoning != ""

    @pytest.mark.asyncio
    async def test_multiple_symbols(self):
        """Test analysis for multiple symbols."""
        agent = AstroCouncilAgent()
        symbols = ["BTC", "ETH", "SOL"]
        for symbol in symbols:
            result = await agent.analyze({
                "symbol": symbol,
                "price": 100.0,
            })
            assert result.signal in Signal
