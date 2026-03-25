"""Tests for SentimentAgent."""

import pytest
from backend.agents.sentiment.sentiment_agent import SentimentAgent
from backend.agents.base_agent import Signal


class TestSentimentAgent:
    """Test SentimentAgent."""

    @pytest.fixture
    def agent(self):
        return SentimentAgent()

    @pytest.mark.asyncio
    async def test_sentiment_agent_init(self, agent):
        assert agent.name == "SentimentAgent"

    @pytest.mark.asyncio
    async def test_sentiment_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "SentimentAgent"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_sentiment_agent_metadata(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        metadata = result.metadata
        assert "fear_greed" in metadata or "market_sentiment" in metadata


class TestPredictorAgent:
    """Test PredictorAgent."""

    @pytest.fixture
    def agent(self):
        from backend.agents.predictor.predictor_agent import PredictorAgent
        return PredictorAgent()

    @pytest.mark.asyncio
    async def test_predictor_agent_init(self, agent):
        assert agent.name == "PredictorAgent"

    @pytest.mark.asyncio
    async def test_predictor_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "price": 68250.0})
        assert result.agent_name == "PredictorAgent"
        assert result.signal in Signal
        assert 0.0 <= result.confidence <= 1.0
