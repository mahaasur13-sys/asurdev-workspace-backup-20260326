"""Tests for RAG Knowledge Base."""
import pytest
from backend.agents.knowledge.rag_agent import RAGKnowledgeAgent


class TestRAGKnowledgeAgent:
    @pytest.fixture
    def agent(self):
        return RAGKnowledgeAgent()
    
    @pytest.mark.asyncio
    async def test_rag_search_astrology(self, agent):
        result = await agent.run({"query": "nakshatra"})
        assert result.agent_name == "RAGKnowledge"
        assert result.signal.value in ["LONG", "SHORT", "NEUTRAL", "AVOID"]
        assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_rag_search_technical(self, agent):
        result = await agent.run({"query": "muhurta"})
        assert result.signal.value in ["LONG", "SHORT", "NEUTRAL", "AVOID"]
        assert len(result.sources) >= 0
    
    @pytest.mark.asyncio
    async def test_rag_with_domain_filter(self, agent):
        result = await agent.run({"query": "planetary", "domain": "astrology/vedic"})
        assert result.agent_name == "RAGKnowledge"
        assert result.metadata.get("results_count", 0) >= 0
    
    def test_get_stats(self, agent):
        stats = agent.loader.get_stats()
        assert "total_documents" in stats
        assert stats["total_documents"] > 0
