"""Tests for base agent classes and types."""

import pytest
from backend.agents.base_agent import Signal, AgentResponse, TradingSignal, BaseAgent


class TestSignal:
    """Test Signal enum."""

    def test_signal_values(self):
        assert Signal.LONG.value == "LONG"
        assert Signal.SHORT.value == "SHORT"
        assert Signal.NEUTRAL.value == "NEUTRAL"
        assert Signal.AVOID.value == "AVOID"

    def test_signal_from_string(self):
        assert Signal("LONG") == Signal.LONG
        assert Signal("NEUTRAL") == Signal.NEUTRAL


class TestAgentResponse:
    """Test AgentResponse dataclass."""

    def test_agent_response_creation(self):
        response = AgentResponse(
            agent_name="TestAgent",
            signal=Signal.LONG,
            confidence=0.85,
            reasoning="Test reasoning",
            sources=["source1.md"],
        )
        assert response.agent_name == "TestAgent"
        assert response.signal == Signal.LONG
        assert response.confidence == 0.85
        assert response.reasoning == "Test reasoning"
        assert response.sources == ["source1.md"]
        assert response.timestamp is not None

    def test_agent_response_to_dict(self):
        response = AgentResponse(
            agent_name="TestAgent",
            signal=Signal.LONG,
            confidence=0.85,
            reasoning="Test reasoning",
        )
        d = response.to_dict()
        assert d["agent_name"] == "TestAgent"
        assert d["signal"] == "LONG"
        assert d["confidence"] == 0.85
        assert d["reasoning"] == "Test reasoning"


class TestTradingSignal:
    """Test TradingSignal dataclass."""

    def test_trading_signal_creation(self):
        signal = TradingSignal(
            signal=Signal.LONG,
            confidence=0.75,
            reasoning="Test reasoning",
            entry_price=68250.0,
            stop_loss_pct=0.05,
            targets=[70000, 72000, 75000],
            position_size_pct=0.05,
        )
        assert signal.signal == Signal.LONG
        assert signal.confidence == 0.75
        assert signal.entry_price == 68250.0
        assert signal.stop_loss_pct == 0.05

    def test_trading_signal_from_agents_single_long(self, mock_ephemeris):
        """Test weighted voting with single LONG agent."""
        responses = [
            AgentResponse(
                agent_name="AstroCouncil",
                signal=Signal.LONG,
                confidence=0.80,
                reasoning="Bullish alignment",
            ),
        ]
        ts = TradingSignal.from_agents("BTC", responses, 68250.0)
        assert ts.signal == Signal.LONG
        assert 0.8 < ts.confidence < 0.85  # confidence * weight

    def test_trading_signal_from_agents_mixed(self, mock_ephemeris):
        """Test weighted voting with mixed signals."""
        responses = [
            AgentResponse(agent_name="AstroCouncil", signal=Signal.LONG, confidence=0.80, reasoning="Bullish"),
            AgentResponse(agent_name="FundamentalAgent", signal=Signal.LONG, confidence=0.70, reasoning="Good fundamentals"),
            AgentResponse(agent_name="MacroAgent", signal=Signal.NEUTRAL, confidence=0.50, reasoning="Unclear macro"),
        ]
        ts = TradingSignal.from_agents("BTC", responses, 68250.0)
        assert ts.signal == Signal.LONG
        assert 0.7 < ts.confidence < 0.8  # Weighted average

    def test_trading_signal_from_agents_avoid(self, mock_ephemeris):
        """Test AVOID signal when high risk."""
        responses = [
            AgentResponse(agent_name="AstroCouncil", signal=Signal.AVOID, confidence=0.90, reasoning="Bad yoga"),
            AgentResponse(agent_name="RiskAgent", signal=Signal.AVOID, confidence=0.85, reasoning="High volatility"),
        ]
        ts = TradingSignal.from_agents("BTC", responses, 68250.0)
        assert ts.signal == Signal.NEUTRAL  # AVOID → NEUTRAL


class DummyAgent(BaseAgent):
    """Dummy agent for testing BaseAgent."""

    async def run(self, context):
        return AgentResponse(
            agent_name=self.name,
            signal=Signal.LONG,
            confidence=0.75,
            reasoning="Test",
        )


class TestBaseAgent:
    """Test BaseAgent abstract class."""

    def test_base_agent_init(self):
        agent = DummyAgent(name="TestAgent", system_prompt="Test prompt")
        assert agent.name == "TestAgent"
        assert agent.system_prompt == "Test prompt"

    @pytest.mark.asyncio
    async def test_base_agent_run(self):
        agent = DummyAgent(name="TestAgent")
        result = await agent.run({})
        assert result.agent_name == "TestAgent"
        assert result.signal == Signal.LONG

    @pytest.mark.asyncio
    async def test_base_agent_analyze(self):
        agent = DummyAgent(name="TestAgent")
        result = await agent.analyze({})
        assert result.agent_name == "TestAgent"

    def test_base_agent_repr(self):
        agent = DummyAgent(name="TestAgent")
        assert "TestAgent" in repr(agent)
