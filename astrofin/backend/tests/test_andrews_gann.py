"""Tests for Andrews Pitchfork and Gann Agents."""
import pytest
from backend.agents.technical.andrews_agent import AndrewsAgent, TrendlineAgent
from backend.agents.technical.gann_agent import GannAgent


class TestAndrewsAgent:
    @pytest.fixture
    def agent(self):
        return AndrewsAgent()
    
    @pytest.mark.asyncio
    async def test_andrews_basic(self, agent):
        result = await agent.run({"symbol": "BTCUSDT", "current_price": 50000})
        assert result.agent_name == "AndrewsAgent"
        assert result.signal.value in ["LONG", "SHORT", "NEUTRAL", "AVOID"]
        assert 0 <= result.confidence <= 1
        assert "Andrews" in result.reasoning
        assert result.metadata["weight"] == 0.06


class TestTrendlineAgent:
    @pytest.fixture
    def agent(self):
        return TrendlineAgent()
    
    @pytest.mark.asyncio
    async def test_trendline_basic(self, agent):
        result = await agent.run({"symbol": "ETHUSDT"})
        assert result.agent_name == "TrendlineAgent"
        assert result.metadata["weight"] == 0.03


class TestGannAgent:
    @pytest.fixture
    def agent(self):
        return GannAgent()
    
    @pytest.mark.asyncio
    async def test_gann_levels(self, agent):
        result = await agent.run({"symbol": "BTCUSDT", "current_price": 50000})
        assert result.agent_name == "GannAgent"
        assert result.signal.value in ["LONG", "SHORT", "NEUTRAL", "AVOID"]
        assert 0 <= result.confidence <= 1
        assert "Gann" in result.reasoning
        assert "levels" in result.metadata
        assert result.metadata["weight"] == 0.05
    
    def test_gann_levels_calculation(self, agent):
        levels = agent._calculate_gann_levels(50000)
        assert "S1" in levels
        assert "R1" in levels
        assert levels["S1"] < 50000
        assert levels["R1"] > 50000
    
    def test_find_level(self, agent):
        levels = {"S1": 48000, "S2": 46000, "R1": 52000, "R2": 54000}
        result = agent._find_current_level(49000, levels)
        assert result in ["S1", "S2"]
