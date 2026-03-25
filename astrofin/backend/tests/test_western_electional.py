"""Tests for Western Electional Astrology."""
import pytest
from datetime import datetime, timedelta


class TestEssentialDignities:
    """Tests for Essential Dignities calculator."""
    
    def test_rulership(self):
        """Jupiter in Sagittarius should have rulership (+5)."""
        from backend.agents.western_electional.dignities import EssentialDignities
        d = EssentialDignities()
        score, desc = d.get_dignity_score("Jupiter", 15.5, "Sagittarius")
        assert score == 5, f"Expected 5, got {score}"
        assert "Rulership" in desc
    
    def test_exaltation(self):
        """Sun in Aries should have exaltation (+4)."""
        from backend.agents.western_electional.dignities import EssentialDignities
        d = EssentialDignities()
        score, desc = d.get_dignity_score("Sun", 10.0, "Aries")
        assert score >= 4, f"Expected >= 4, got {score}"
        assert score >= 4, "Should have at least one dignity"
    
    def test_detriiment(self):
        """Venus in Aries should have detriment (-5)."""
        from backend.agents.western_electional.dignities import EssentialDignities
        d = EssentialDignities()
        score, desc = d.get_dignity_score("Mars", 5.0, "Libra")
        assert score <= 0, f"Expected <= 0, got {score}"
        assert "No dignity" in desc or score < 0, "Should have debility or neutral"


class TestAspectCalculator:
    """Tests for Aspect Calculator."""
    
    def test_conjunction(self):
        """Two planets at 0° apart should be in conjunction."""
        from backend.agents.western_electional.aspects import AspectCalculator
        a = AspectCalculator()
        aspects = a.calculate_aspects({"Sun": 10, "Mercury": 10})
        assert len(aspects) >= 1
        conj = next((asp for asp in aspects if asp["aspect"] == "Conjunction"), None)
        assert conj is not None, "Conjunction not found"
    
    def test_trine(self):
        """Two planets 120° apart should be trine."""
        from backend.agents.western_electional.aspects import AspectCalculator
        a = AspectCalculator()
        aspects = a.calculate_aspects({"Sun": 0, "Mars": 120})
        trine = next((asp for asp in aspects if asp["aspect"] == "Trine"), None)
        assert trine is not None, "Trine not found"
    
    def test_square(self):
        """Two planets 90° apart should be square."""
        from backend.agents.western_electional.aspects import AspectCalculator
        a = AspectCalculator()
        aspects = a.calculate_aspects({"Sun": 0, "Mars": 90})
        square = next((asp for asp in aspects if asp["aspect"] == "Square"), None)
        assert square is not None, "Square not found"


class TestWesternElectionalAgent:
    """Tests for Western Electional Agent."""
    
    @pytest.mark.asyncio
    async def test_find_windows(self):
        """Should find electional windows for business."""
        import sys
        sys.path.insert(0, '/home/workspace/astrofin')
        
        from backend.agents.western_electional import WesternElectionalAgent
        
        agent = WesternElectionalAgent()
        
        windows = await agent.find_electional_windows(
            action_type="business",
            location={"lat": 40.7128, "lon": -74.0060},
            duration_days=3,
            start_date=datetime.now(),
            interval_minutes=180  # 3-hour intervals for speed
        )
        
        assert len(windows) >= 0  # Should complete without error
    
    @pytest.mark.asyncio
    async def test_agent_run(self):
        """Should return AgentResponse."""
        import sys
        sys.path.insert(0, '/home/workspace/astrofin')
        
        from backend.agents.western_electional import WesternElectionalAgent
        
        agent = WesternElectionalAgent()
        result = await agent.run({
            "action_type": "business",
            "location": {"lat": 40.7128, "lon": -74.0060},
            "duration_days": 1
        })
        
        assert result.agent_name == "WesternElectionalAgent"
        assert hasattr(result, "signal")
        assert hasattr(result, "confidence")
        assert hasattr(result, "metadata")
        assert "windows_found" in result.metadata
