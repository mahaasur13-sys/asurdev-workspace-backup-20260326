"""
RAGKnowledgeAgent — Knowledge Retriever.
Загрузка и поиск по базе знаний (RAG).
"""
from __future__ import annotations
from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentResponse, Signal

class RAGKnowledgeAgent(BaseAgent):
    """RAGKnowledgeAgent — RAG knowledge retrieval. Вес: 0.06"""
    KNOWLEDGE_BASE = {
        "elective_principles.md": {
            "content": "Western electional astrology principles...",
            "tags": ["elective", "election", "western"],
        },
        "muhurta.md": {
            "content": "Vedic Muhurta principles...",
            "tags": ["muhurta", "vedic", "election"],
        },
        "nakshatras.md": {
            "content": "27 Nakshatras and their characteristics...",
            "tags": ["nakshatra", "vedic", "lunar"],
        },
        "choghadiya.md": {
            "content": "Choghadiya - 8 periods of day...",
            "tags": ["choghadiya", "vedic", "timing"],
        },
        "financial_astrology.md": {
            "content": "Financial astrology principles...",
            "tags": ["finance", "market", "trading"],
        },
        "western_astrology.md": {
            "content": "Western astrology principles...",
            "tags": ["western", "lilly", "dignities"],
        },
    }

    def __init__(self):
        super().__init__(
            name="RAGKnowledgeAgent",
            system_prompt="RAG Knowledge Retrieval"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        query = context.get("user_query", context.get("query", ""))
        
        if not query:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning="No query provided", sources=[],
            )

        results = self._search_knowledge(query)
        
        if not results:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.4,
                reasoning="No relevant knowledge found", sources=[],
            )

        return AgentResponse(
            agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.6,
            reasoning=f"Found {len(results)} relevant documents",
            sources=[r["source"] for r in results],
            metadata={"results": results, "query": query},
        )

    def _search_knowledge(self, query: str) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        for doc_name, doc_data in self.KNOWLEDGE_BASE.items():
            score = 0.0
            for tag in doc_data.get("tags", []):
                if tag in query_lower:
                    score += 0.5
            
            if score > 0:
                results.append({
                    "source": doc_name,
                    "score": score,
                    "preview": doc_data["content"][:200],
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:5]
