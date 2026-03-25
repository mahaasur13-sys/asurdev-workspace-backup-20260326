"""
Tools registry for multi-agent system.
Updated: 2026-03-24 — jd_ut caching support
"""

from src.graph_v2.tools.knowledge import retrieve_knowledge, get_retriever
from src.graph_v2.tools.astro import create_swiss_ephemeris_tool


def get_all_tools():
    """
    Get all tools available to agents.
    
    Returns list of LangChain tools:
    - retrieve_knowledge: RAG tool with metadata filtering + jd_ut caching
    - swiss_ephemeris: Vedic astrology calculations
    """
    return [
        create_retrieve_knowledge_tool(),
        create_swiss_ephemeris_tool(),
    ]


def get_tools_for_agent(agent_name: str):
    """
    Get tools specific to an agent type.
    
    2026: All agents get knowledge + astro tools.
    Each agent must call retrieve_knowledge FIRST with their agent_role.
    """
    retrieve = create_retrieve_knowledge_tool()
    swiss = create_swiss_ephemeris_tool()
    
    # All agents get knowledge + astro tools
    return [retrieve, swiss]


def create_retrieve_knowledge_tool():
    """
    Create the retrieve_knowledge tool with proper schema.
    
    Tool: retrieve_knowledge
    Args:
        query: str - Natural language query
        agent_role: str - Which agent is calling (MarketAnalyst, BullResearcher, etc.)
        topic: Optional[str] - Metadata filter (panchanga, technical_analysis, etc.)
        jd_ut: Optional[float] - Julian Day UT for astro-stable caching
    """
    from langchain_core.tools import tool
    
    @tool
    def retrieve_knowledge(
        query: str,
        agent_role: str,
        topic: str = None,
        jd_ut: float = None,
    ) -> str:
        """
        Retrieve knowledge from vectorstore with caching.
        
        This tool MUST be called FIRST by every agent before providing analysis.
        
        Args:
            query: Precise query describing what knowledge you need
            agent_role: Your role (MarketAnalyst, BullResearcher, BearResearcher, 
                       MuhurtaSpecialist, Synthesizer, Supervisor)
            topic: Optional filter (panchanga, technical_analysis, bullish_catalysts, 
                  risk_factors, muhurta, timing, synthesis)
            jd_ut: Julian Day UT - if provided, results cached by astro state
        
        Returns:
            Relevant knowledge chunks from the vectorstore
            
        Example:
            retrieve_knowledge(
                query="Pushya nakshatra trading rules",
                agent_role="MuhurtaSpecialist",
                topic="panchanga",
                jd_ut=2460104.5
            )
        """
        retriever = get_retriever()
        return retriever.retrieve(
            query=query,
            agent_role=agent_role,
            topic=topic,
            jd_ut=jd_ut,
        )
    
    return retrieve_knowledge
