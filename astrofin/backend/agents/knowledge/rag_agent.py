"""
RAG Knowledge Agent.
Использует Obsidian vault как базу знаний для ответов на вопросы.
"""
from typing import Dict, List, Any, Optional
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from knowledge.rag.obsidian_loader import get_obsidian_loader, ObsidianLoader


class RAGKnowledgeAgent(BaseAgent):
    """
    RAG Knowledge Agent — ищет ответы в Obsidian vault.
    
    Вес: 8%
    Использует loaded documents для точных ответов.
    """
    
    def __init__(self):
        super().__init__(
            name="RAGKnowledge",
            system_prompt="RAG Knowledge Agent — отвечает на вопросы используя базу знаний Obsidian"
        )
        self.loader = get_obsidian_loader()
        self._load_stats()
    
    def _load_stats(self):
        """Загружает статистику при инициализации."""
        self.stats = self.loader.get_stats()
    
    @require_ephemeris
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        """Выполняет RAG поиск по запросу."""
        query = context.get("query", context.get("question", ""))
        domain = context.get("domain", None)
        limit = context.get("limit", 5)
        
        if not query:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=0.3,
                reasoning="No query provided"
            )
        
        # Search
        docs = self.loader.search(query, limit=limit)
        
        # Filter by domain if specified
        if domain:
            docs = [d for d in docs if d.domain == domain]
        
        if not docs:
            # Try loading all first
            self.loader.load_all()
            docs = self.loader.search(query, limit=limit)
        
        # Build response
        if docs:
            top = docs[0]
            
            # Detect sentiment from content
            content_lower = top.content.lower()
            bullish = any(w in content_lower for w in ["благоприятн", "рост", "успех", "прибыль", "long", "bullish", "покупка"])
            bearish = any(w in content_lower for w in ["неблагоприятн", "падение", "убыток", "short", "bearish", "продажа"])
            
            if bullish and not bearish:
                signal = Signal.LONG
                confidence = 0.7
            elif bearish and not bullish:
                signal = Signal.SHORT
                confidence = 0.7
            else:
                signal = Signal.NEUTRAL
                confidence = 0.5
            
            reasoning = f"Found {len(docs)} relevant docs. Top: {top.title}"
            
            return AgentResponse(
                agent_name=self.name,
                signal=signal,
                confidence=confidence,
                reasoning=reasoning,
                sources=[d.source for d in docs],
                metadata={
                    "query": query,
                    "results_count": len(docs),
                    "top_document": top.title,
                    "top_domain": top.domain,
                    "all_domains": list(set(d.domain for d in docs)),
                    "weight": 0.08,
                }
            )
        else:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=0.3,
                reasoning=f"No relevant documents found for: {query}",
                metadata={"query": query, "results_count": 0}
            )


async def run_rag_agent(context: Dict[str, Any]) -> Dict[str, Any]:
    """Runner for orchestrator."""
    agent = RAGKnowledgeAgent()
    result = await agent.run(context)
    return {"rag_signal": result.to_dict()}
