"""Tests for specialized Astro Agents."""
import pytest
from backend.agents.elective import ElectivePredictorAgent
from backend.agents.muhurta import MuhurtaPredictorAgent
from backend.agents.transit import TransitSentinelAgent
from backend.agents.natal import NatalChartAgent
from backend.agents.aspect import AspectAnalyzerAgent
from backend.agents.financial_astro import FinancialAstroAgent
from backend.agents.health_astro import HealthAstroAgent
from backend.agents.horary import HoraryAgent
from backend.agents.weather_astro import WeatherAstroAgent
from backend.agents.event_timing import EventTimingAgent
from backend.agents.rag_knowledge import RAGKnowledgeAgent
from backend.agents.voc_moon import VoidOfCourseMoonAgent
from backend.agents.planetary_hour import PlanetaryHourAgent
from backend.agents.dignity import DignityScorerAgent
from backend.agents.formatter import ResponseFormatterAgent
from backend.agents.relocation import RelocationAgent
from backend.agents.base_agent import Signal


class TestElectivePredictorAgent:
    """Test ElectivePredictorAgent."""
    
    @pytest.fixture
    def agent(self):
        return ElectivePredictorAgent()
    
    @pytest.mark.asyncio
    async def test_elective_agent_init(self, agent):
        assert agent.name == "ElectivePredictorAgent"
        assert hasattr(agent, "weights")
    
    @pytest.mark.asyncio
    async def test_elective_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "user_query": "BTC investment"})
        assert result.agent_name == "ElectivePredictorAgent"
        assert result.signal in Signal
        assert 0 <= result.confidence <= 1


class TestMuhurtaPredictorAgent:
    """Test MuhurtaPredictorAgent."""
    
    @pytest.fixture
    def agent(self):
        return MuhurtaPredictorAgent()
    
    @pytest.mark.asyncio
    async def test_muhurta_agent_init(self, agent):
        assert agent.name == "MuhurtaPredictorAgent"
        assert hasattr(agent, "GOOD_NAKSHATRAS")
    
    @pytest.mark.asyncio
    async def test_muhurta_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC", "user_query": "Muhurta for trading"})
        assert result.agent_name == "MuhurtaPredictorAgent"
        assert result.signal in Signal


class TestTransitSentinelAgent:
    """Test TransitSentinelAgent."""
    
    @pytest.fixture
    def agent(self):
        return TransitSentinelAgent()
    
    @pytest.mark.asyncio
    async def test_transit_agent_init(self, agent):
        assert agent.name == "TransitSentinelAgent"
        assert hasattr(agent, "TRANSIT_IMPACT")
    
    @pytest.mark.asyncio
    async def test_transit_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC"})
        assert result.agent_name == "TransitSentinelAgent"
        assert result.signal in Signal
        assert "transits" in result.metadata


class TestNatalChartAgent:
    """Test NatalChartAgent."""
    
    @pytest.fixture
    def agent(self):
        return NatalChartAgent()
    
    @pytest.mark.asyncio
    async def test_natal_agent_init(self, agent):
        assert agent.name == "NatalChartAgent"
    
    @pytest.mark.asyncio
    async def test_natal_agent_run(self, agent):
        result = await agent.run({"birth_date": "1990-01-01", "birth_time": "12:00:00"})
        assert result.agent_name == "NatalChartAgent"
        assert "planets" in result.metadata


class TestAspectAnalyzerAgent:
    """Test AspectAnalyzerAgent."""
    
    @pytest.fixture
    def agent(self):
        return AspectAnalyzerAgent()
    
    @pytest.mark.asyncio
    async def test_aspect_agent_init(self, agent):
        assert agent.name == "AspectAnalyzerAgent"
        assert hasattr(agent, "ASPECTS")
    
    @pytest.mark.asyncio
    async def test_aspect_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC"})
        assert result.agent_name == "AspectAnalyzerAgent"
        assert result.signal in Signal
        assert "aspects" in result.metadata


class TestFinancialAstroAgent:
    """Test FinancialAstroAgent."""
    
    @pytest.fixture
    def agent(self):
        return FinancialAstroAgent()
    
    @pytest.mark.asyncio
    async def test_financial_agent_init(self, agent):
        assert agent.name == "FinancialAstroAgent"
        assert hasattr(agent, "BULLISH_SIGNS")
    
    @pytest.mark.asyncio
    async def test_financial_agent_run(self, agent):
        result = await agent.run({"symbol": "BTC"})
        assert result.agent_name == "FinancialAstroAgent"
        assert result.signal in Signal


class TestHealthAstroAgent:
    """Test HealthAstroAgent."""
    
    @pytest.fixture
    def agent(self):
        return HealthAstroAgent()
    
    @pytest.mark.asyncio
    async def test_health_agent_init(self, agent):
        assert agent.name == "HealthAstroAgent"
    
    @pytest.mark.asyncio
    async def test_health_agent_run(self, agent):
        result = await agent.run({})
        assert result.agent_name == "HealthAstroAgent"
        assert result.signal in Signal


class TestHoraryAgent:
    """Test HoraryAgent."""
    
    @pytest.fixture
    def agent(self):
        return HoraryAgent()
    
    @pytest.mark.asyncio
    async def test_horary_agent_init(self, agent):
        assert agent.name == "HoraryAgent"
    
    @pytest.mark.asyncio
    async def test_horary_agent_run(self, agent):
        result = await agent.run({"question": "Is BTC going up?"})
        assert result.agent_name == "HoraryAgent"
        assert "category" in result.metadata


class TestWeatherAstroAgent:
    """Test WeatherAstroAgent."""
    
    @pytest.fixture
    def agent(self):
        return WeatherAstroAgent()
    
    @pytest.mark.asyncio
    async def test_weather_agent_init(self, agent):
        assert agent.name == "WeatherAstroAgent"
    
    @pytest.mark.asyncio
    async def test_weather_agent_run(self, agent):
        result = await agent.run({})
        assert result.agent_name == "WeatherAstroAgent"
        assert "weather_prediction" in result.metadata


class TestEventTimingAgent:
    """Test EventTimingAgent."""
    
    @pytest.fixture
    def agent(self):
        return EventTimingAgent()
    
    @pytest.mark.asyncio
    async def test_event_timing_init(self, agent):
        assert agent.name == "EventTimingAgent"
    
    @pytest.mark.asyncio
    async def test_event_timing_run(self, agent):
        result = await agent.run({"event_type": "meeting"})
        assert result.agent_name == "EventTimingAgent"
        assert result.signal in Signal


class TestRAGKnowledgeAgent:
    """Test RAGKnowledgeAgent."""
    
    @pytest.fixture
    def agent(self):
        return RAGKnowledgeAgent()
    
    @pytest.mark.asyncio
    async def test_rag_agent_init(self, agent):
        assert agent.name == "RAGKnowledgeAgent"
        assert hasattr(agent, "KNOWLEDGE_BASE")
    
    @pytest.mark.asyncio
    async def test_rag_agent_search(self, agent):
        result = await agent.run({"query": "elective astrology"})
        assert result.agent_name == "RAGKnowledgeAgent"
        assert "results" in result.metadata


class TestVoidOfCourseMoonAgent:
    """Test VoidOfCourseMoonAgent."""
    
    @pytest.fixture
    def agent(self):
        return VoidOfCourseMoonAgent()
    
    @pytest.mark.asyncio
    async def test_voc_agent_init(self, agent):
        assert agent.name == "VoidOfCourseMoonAgent"
    
    @pytest.mark.asyncio
    async def test_voc_agent_run(self, agent):
        result = await agent.run({})
        assert result.agent_name == "VoidOfCourseMoonAgent"
        assert "is_voc" in result.metadata


class TestPlanetaryHourAgent:
    """Test PlanetaryHourAgent."""
    
    @pytest.fixture
    def agent(self):
        return PlanetaryHourAgent()
    
    @pytest.mark.asyncio
    async def test_planetary_hour_init(self, agent):
        assert agent.name == "PlanetaryHourAgent"
    
    @pytest.mark.asyncio
    async def test_planetary_hour_run(self, agent):
        result = await agent.run({"activity": "meeting"})
        assert result.agent_name == "PlanetaryHourAgent"
        assert "current_planet" in result.metadata


class TestDignityScorerAgent:
    """Test DignityScorerAgent."""
    
    @pytest.fixture
    def agent(self):
        return DignityScorerAgent()
    
    @pytest.mark.asyncio
    async def test_dignity_agent_init(self, agent):
        assert agent.name == "DignityScorerAgent"
        assert hasattr(agent, "DIGNITIES")
    
    @pytest.mark.asyncio
    async def test_dignity_agent_run(self, agent):
        result = await agent.run({})
        assert result.agent_name == "DignityScorerAgent"
        assert "dignities" in result.metadata


class TestResponseFormatterAgent:
    """Test ResponseFormatterAgent."""
    
    @pytest.fixture
    def agent(self):
        return ResponseFormatterAgent()
    
    @pytest.mark.asyncio
    async def test_formatter_agent_init(self, agent):
        assert agent.name == "ResponseFormatterAgent"
    
    @pytest.mark.asyncio
    async def test_formatter_agent_run(self, agent):
        from backend.agents.base_agent import AgentResponse
        response = AgentResponse(
            agent_name="TestAgent",
            signal=Signal.LONG,
            confidence=0.8,
            reasoning="Test"
        )
        result = await agent.run({"all_responses": [response], "symbol": "BTC"})
        assert result.agent_name == "ResponseFormatterAgent"
        assert "formatted_report" in result.metadata


class TestRelocationAgent:
    """Test RelocationAgent."""
    
    @pytest.fixture
    def agent(self):
        return RelocationAgent()
    
    @pytest.mark.asyncio
    async def test_relocation_agent_init(self, agent):
        assert agent.name == "RelocationAgent"
    
    @pytest.mark.asyncio
    async def test_relocation_agent_run(self, agent):
        result = await agent.run({"target_lat": 48.8566, "target_lon": 2.3522})
        assert result.agent_name == "RelocationAgent"
        assert "target_lat" in result.metadata
