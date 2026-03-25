"""Tests for Board of Directors."""

import pytest
from unittest.mock import patch


class TestRecommendation:
    """Tests for Recommendation enum."""

    def test_recommendation_values(self):
        """Test recommendation values."""
        from agents._impl.board import Recommendation
        
        assert Recommendation.BUY.value == "BUY"
        assert Recommendation.SELL.value == "SELL"
        assert Recommendation.HOLD.value == "HOLD"
        assert Recommendation.WAIT.value == "WAIT"
        assert Recommendation.NEUTRAL.value == "NEUTRAL"


class TestRiskLevel:
    """Tests for RiskLevel enum."""

    def test_risk_level_values(self):
        """Test risk level values."""
        from agents._impl.board import RiskLevel
        
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"


class TestAgentVote:
    """Tests for AgentVote dataclass."""

    def test_agent_vote_creation(self):
        """Test AgentVote creation."""
        from agents._impl.board import AgentVote, Recommendation
        
        vote = AgentVote(
            agent_name="Market_Analyst",
            recommendation=Recommendation.BUY,
            confidence=0.75,
            reasoning="Strong technical setup",
        )
        
        assert vote.agent_name == "Market_Analyst"
        assert vote.recommendation == Recommendation.BUY
        assert vote.confidence == 0.75
        assert vote.reasoning == "Strong technical setup"
        assert vote.timestamp is not None


class TestBoardVerdict:
    """Tests for BoardVerdict dataclass."""

    def test_board_verdict_creation(self):
        """Test BoardVerdict creation."""
        from agents._impl.board import BoardVerdict, AgentVote, Recommendation, RiskLevel
        
        votes = [
            AgentVote(
                agent_name="Analyst",
                recommendation=Recommendation.BUY,
                confidence=0.7,
                reasoning="Good setup",
            ),
        ]
        
        verdict = BoardVerdict(
            recommendation=Recommendation.BUY,
            confidence=0.7,
            time_horizon="Medium-term",
            thesis="Bullish based on analysis",
            risk_level=RiskLevel.MEDIUM,
            votes=votes,
            dissent=[],
            elapsed_seconds=5.5,
        )
        
        assert verdict.recommendation == Recommendation.BUY
        assert verdict.confidence == 0.7
        assert verdict.time_horizon == "Medium-term"
        assert verdict.risk_level == RiskLevel.MEDIUM
        assert len(verdict.votes) == 1

    def test_board_verdict_to_dict(self):
        """Test BoardVerdict serialization."""
        from agents._impl.board import BoardVerdict, AgentVote, Recommendation, RiskLevel
        
        votes = [
            AgentVote(
                agent_name="Analyst",
                recommendation=Recommendation.SELL,
                confidence=0.6,
                reasoning="Risk present",
            ),
        ]
        
        verdict = BoardVerdict(
            recommendation=Recommendation.SELL,
            confidence=0.6,
            time_horizon="Short-term",
            thesis="Bearish outlook",
            risk_level=RiskLevel.HIGH,
            votes=votes,
            dissent=["One member dissented"],
            elapsed_seconds=3.2,
        )
        
        d = verdict.to_dict()
        
        assert d["recommendation"] == "SELL"
        assert d["confidence"] == 0.6
        assert d["time_horizon"] == "Short-term"
        assert d["thesis"] == "Bearish outlook"
        assert d["risk_level"] == "HIGH"
        assert len(d["votes"]) == 1
        assert d["votes"][0]["agent"] == "Analyst"
        assert d["dissent"] == ["One member dissented"]
        assert d["elapsed_seconds"] == 3.2


class TestBoardOfDirectors:
    """Tests for BoardOfDirectors class."""

    def test_board_initialization(self):
        """Test Board initialization with mocked LLM."""
        from agents._impl.board import BoardOfDirectors
        
        with patch("agents._impl.board.get_llm_config") as mock_config:
            mock_config.return_value = {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-test",
                "temperature": 0.7,
            }
            
            board = BoardOfDirectors(
                provider="openai",
                mode="debate",
                include_astrology=True,
                include_risk_manager=True,
            )
            
            assert board.provider == "openai"
            assert board.mode == "debate"
            assert board.include_astrology is True
            assert board.include_risk_manager is True

    def test_parse_recommendation(self):
        """Test recommendation parsing."""
        from agents._impl.board import BoardOfDirectors, Recommendation
        
        with patch("agents._impl.board.get_llm_config") as mock_config:
            mock_config.return_value = {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-test",
            }
            
            board = BoardOfDirectors()
            
            assert board._parse_recommendation("RECOMMENDATION: BUY") == Recommendation.BUY
            assert board._parse_recommendation("RECOMMENDATION: SELL") == Recommendation.SELL
            assert board._parse_recommendation("RECOMMENDATION: HOLD") == Recommendation.HOLD
            assert board._parse_recommendation("should BUY now") == Recommendation.BUY
            assert board._parse_recommendation("should SELL") == Recommendation.SELL
            assert board._parse_recommendation("TIMING ASSESSMENT: FAVORABLE") == Recommendation.BUY
            assert board._parse_recommendation("TIMING ASSESSMENT: UNFAVORABLE") == Recommendation.SELL

    def test_parse_confidence(self):
        """Test confidence parsing."""
        from agents._impl.board import BoardOfDirectors
        
        with patch("agents._impl.board.get_llm_config") as mock_config:
            mock_config.return_value = {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-test",
            }
            
            board = BoardOfDirectors()
            
            assert board._parse_confidence("CONFIDENCE: 75%") == 0.75
            assert board._parse_confidence("CONFIDENCE: 80") == 0.8
            assert board._parse_confidence("no confidence here") == 0.5  # default


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
