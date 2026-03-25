"""Tests for unified types (Signal, AgentResponse, TradingSignal)."""

import pytest
from agents.types import Signal, AgentResponse, TradingSignal


class TestSignal:
    """Tests for Signal enum."""

    def test_signal_values(self):
        """Test signal enum values."""
        assert Signal.STRONG_BUY.value == "STRONG_BUY"
        assert Signal.BUY.value == "BUY"
        assert Signal.NEUTRAL.value == "NEUTRAL"
        assert Signal.HOLD.value == "HOLD"
        assert Signal.SELL.value == "SELL"
        assert Signal.STRONG_SELL.value == "STRONG_SELL"

    def test_signal_from_string(self):
        """Test Signal.from_string conversion."""
        assert Signal.from_string("BUY") == Signal.BUY
        assert Signal.from_string("STRONG_BUY") == Signal.STRONG_BUY
        assert Signal.from_string("BULLISH") == Signal.BUY
        assert Signal.from_string("BEARISH") == Signal.SELL
        assert Signal.from_string("unknown") == Signal.NEUTRAL

    def test_signal_score(self):
        """Test signal numeric scores."""
        assert Signal.STRONG_BUY.score == 100
        assert Signal.BUY.score == 70
        assert Signal.NEUTRAL.score == 50
        assert Signal.HOLD.score == 50
        assert Signal.SELL.score == 30
        assert Signal.STRONG_SELL.score == 0

    def test_signal_properties(self):
        """Test signal bullish/bearish/neutral properties."""
        assert Signal.STRONG_BUY.is_bullish is True
        assert Signal.BUY.is_bullish is True
        assert Signal.NEUTRAL.is_neutral is True
        assert Signal.HOLD.is_neutral is True
        assert Signal.SELL.is_bearish is True
        assert Signal.STRONG_SELL.is_bearish is True


class TestAgentResponse:
    """Tests for AgentResponse dataclass."""

    def test_agent_response_creation(self):
        """Test AgentResponse creation."""
        response = AgentResponse(
            agent_name="MarketAnalyst",
            signal="BUY",
            confidence=75,
            summary="Price above MA200",
            details={"rsi": 45, "macd": "bullish"},
        )
        
        assert response.agent_name == "MarketAnalyst"
        assert response.signal == "BUY"
        assert response.confidence == 75
        assert response.summary == "Price above MA200"
        assert response.details["rsi"] == 45
        assert response.errors == []

    def test_agent_response_to_dict(self):
        """Test AgentResponse.to_dict serialization."""
        response = AgentResponse(
            agent_name="Test",
            signal="SELL",
            confidence=60,
            summary="Test summary",
        )
        
        d = response.to_dict()
        assert d["agent_name"] == "Test"
        assert d["signal"] == "SELL"
        assert d["confidence"] == 60
        assert "timestamp" in d

    def test_agent_response_signal_enum(self):
        """Test signal_enum property."""
        response = AgentResponse(
            agent_name="Test",
            signal="BULLISH",
            confidence=70,
            summary="",
        )
        assert response.signal_enum == Signal.BUY


class TestTradingSignal:
    """Tests for TradingSignal."""

    def test_trading_signal_from_agents(self):
        """Test TradingSignal.from_agents factory."""
        responses = [
            AgentResponse(
                agent_name="Market",
                signal="BUY",
                confidence=75,
                summary="",
            ),
            AgentResponse(
                agent_name="Bull",
                signal="STRONG_BUY",
                confidence=80,
                summary="",
            ),
            AgentResponse(
                agent_name="Bear",
                signal="SELL",
                confidence=60,
                summary="",
            ),
        ]
        
        signal = TradingSignal.from_agents(
            symbol="BTC",
            responses=responses,
            entry_price=67000.0,
        )
        
        assert signal.symbol == "BTC"
        assert signal.entry == 67000.0
        assert signal.stop_loss is not None
        assert signal.take_profit is not None
        assert signal.risk_reward > 0

    def test_trading_signal_to_dict(self):
        """Test TradingSignal.to_dict serialization."""
        responses = [
            AgentResponse(
                agent_name="Test",
                signal="NEUTRAL",
                confidence=50,
                summary="",
            )
        ]
        
        signal = TradingSignal.from_agents(
            symbol="ETH",
            responses=responses,
            entry_price=3500.0,
        )
        
        d = signal.to_dict()
        assert d["symbol"] == "ETH"
        assert "signal" in d
        assert "entry" in d
        assert "stop_loss" in d
        assert "take_profit" in d
        assert "risk_reward" in d
        assert len(d["agents"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
