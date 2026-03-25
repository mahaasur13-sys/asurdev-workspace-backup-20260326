"""
LangGraph Orchestrator — Main Entry Point
asurdev Sentinel v3.2
==========================================

Refactored to use agents/graph/ and agents/memory/ modules.

For new projects, use MemoryEnabledOrchestrator for full RAG support.
"""

from __future__ import annotations
import asyncio
import os
from typing import Optional, Dict, Any

from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage

from .types import Signal, AgentResponse, TradingSignal
from .state import SentinelState
from .graph import build_graph
from .memory import MemoryMiddleware


# =============================================================================
# MODULE-LEVEL MEMORY (shared across nodes)
# =============================================================================

_module_memory: Optional[MemoryMiddleware] = None


def _set_module_memory(memory: Optional[MemoryMiddleware]) -> None:
    """Set module-level memory for graph nodes to access."""
    global _module_memory
    _module_memory = memory
    
    # Also set in graph nodes
    from .graph.nodes import _set_memory
    _set_memory(memory)


def _get_module_memory() -> Optional[MemoryMiddleware]:
    """Get module-level memory."""
    return _module_memory


# =============================================================================
# MEMORY-ENABLED ORCHESTRATOR
# =============================================================================

class MemoryEnabledOrchestrator:
    """
    LangGraph Orchestrator with full Memory Integration.
    
    Features:
    - Initializes MemoryMiddleware with ChromaDB
    - Starts session for each analysis
    - Injects memory context into all agents
    - Stores all agent responses to ChromaDB
    - Uses adaptive weights from FuzzyMemory for synthesis
    - Provides feedback and outcome tracking APIs
    
    Usage:
        orchestrator = MemoryEnabledOrchestrator()
        result = await orchestrator.analyze("BTC", action="hold")
        
        # Record feedback
        orchestrator.add_feedback(result, agent="astro", helpful=True, rating=5)
        
        # Record outcome (call later after price moves)
        orchestrator.add_outcome("BTC", prediction="BULLISH", actual="correct")
    """
    
    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        enable_rag: bool = True,
        enable_adaptive_weights: bool = True,
    ):
        # Initialize memory middleware
        self.memory = MemoryMiddleware(
            persist_dir=persist_dir,
            enable_rag=enable_rag,
            enable_adaptive_weights=enable_adaptive_weights,
        )
        
        # Set module-level memory for nodes
        _set_module_memory(self.memory)
        
        # Compile graph
        graph = build_graph()
        self.app = graph.compile(
            checkpointer=MemorySaver(),
            interrupt_before=[],
        )
        
        # Track current session
        self._current_session_id: Optional[str] = None
        self._current_symbol: Optional[str] = None
        self._analysis_ids: Dict[str, str] = {}  # agent_name -> doc_id
        
        print(f"[Memory] ✓ ChromaDB connected: {persist_dir}")
        print(f"[Memory] ✓ Adaptive weights: {enable_adaptive_weights}")
    
    @property
    def chroma_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self.memory.get_memory_stats()
    
    async def analyze(
        self,
        symbol: str,
        action: str = "hold",
        thread_id: Optional[str] = None,
        lat: float = 28.6139,
        lon: float = 77.2090,
    ) -> dict:
        """
        Run full analysis with memory integration.
        
        Args:
            symbol: BTC, ETH, etc.
            action: buy, sell, hold
            thread_id: Optional thread for checkpointing
            lat: Latitude for astrology
            lon: Longitude for astrology
            
        Returns:
            Final state dict with all agent responses and synthesis
        """
        # Start memory session
        thread_id = thread_id or f"{symbol}_{int(asyncio.get_event_loop().time())}"
        self._current_session_id = thread_id
        self._current_symbol = symbol.upper()
        self._analysis_ids = {}
        
        # Start session in memory
        self.memory.start_session(
            session_id=thread_id,
            symbol=symbol.upper(),
            action=action,
        )
        
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state: SentinelState = {
            "messages": [HumanMessage(content=f"Analyze {symbol} for {action}")],
            "symbol": symbol.upper(),
            "action": action,
            "market_price": 67000,
            "market_trend": "NEUTRAL",
            "lat": lat,
            "lon": lon,
            # All agent responses start as None
            "market_response": None,
            "bull_response": None,
            "bear_response": None,
            "astro_response": None,
            "cycle_response": None,
            "dow_response": None,
            "andrews_response": None,
            "gann_response": None,
            "merriman_response": None,
            "meridian_response": None,
            "synthesis": None,
            "final_verdict": Signal.NEUTRAL,
            "errors": [],
            "confidence_avg": 0,
        }
        
        # Run analysis
        final_state = await self.app.ainvoke(initial_state, config)
        
        # Store all agent responses to memory
        await self._store_responses(final_state)
        
        return final_state
    
    async def _store_responses(self, state: SentinelState):
        """Store all agent responses to ChromaDB."""
        symbol = state.get("symbol", "BTC")
        market_state = {
            "current_price": state.get("market_price", 67000),
            "trend": state.get("market_trend", "NEUTRAL"),
        }
        
        response_fields = [
            "market_response", "bull_response", "bear_response",
            "astro_response", "cycle_response", "dow_response",
            "andrews_response", "gann_response", "merriman_response",
            "meridian_response"
        ]
        
        for field in response_fields:
            response = state.get(field)
            if response and response.signal != "ERROR":
                agent_name = field.replace("_response", "")
                doc_id = await self.memory.store_agent_response(
                    agent_name=agent_name,
                    response=response,
                    symbol=symbol,
                    market_state=market_state,
                )
                if doc_id:
                    self._analysis_ids[agent_name] = doc_id
    
    def add_feedback(
        self,
        result: dict,
        agent: str,
        helpful: bool,
        rating: int,
        correction: Optional[str] = None,
    ):
        """
        Add user feedback for an agent's analysis.
        """
        analysis_id = self._analysis_ids.get(agent)
        if not analysis_id:
            print(f"[Memory] No analysis ID found for agent '{agent}'")
            return
        
        self.memory.add_feedback(
            analysis_id=analysis_id,
            agent=agent,
            helpful=helpful,
            rating=rating,
            correction=correction,
        )
        
        print(f"[Memory] ✓ Feedback recorded for {agent}: helpful={helpful}, rating={rating}")
    
    def add_outcome(
        self,
        symbol: str,
        agent: str,
        prediction: str,
        actual_direction: str,
        confidence: float,
        price_change: float,
    ):
        """
        Record actual outcome for learning.
        """
        self.memory.add_outcome(
            symbol=symbol,
            agent=agent,
            prediction=prediction,
            actual_direction=actual_direction,
            confidence=confidence,
            price_change=price_change,
        )
        
        outcome = "correct" if prediction == actual_direction else "incorrect"
        print(f"[Memory] ✓ Outcome recorded for {agent}: {outcome} (price_change={price_change}%)")
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get performance stats for a specific agent."""
        return self.memory.get_agent_stats(agent)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get overall memory statistics."""
        return self.memory.get_memory_stats()
    
    async def analyze_with_review(
        self,
        symbol: str,
        action: str = "hold",
    ) -> dict:
        """
        Analyze with human review before synthesis.
        Interrupts at synthesize node.
        """
        # Start memory session
        thread_id = f"{symbol}_review_{int(asyncio.get_event_loop().time())}"
        self._current_session_id = thread_id
        self._current_symbol = symbol.upper()
        
        self.memory.start_session(
            session_id=thread_id,
            symbol=symbol.upper(),
            action=action,
        )
        
        graph = build_graph()
        app = graph.compile(
            checkpointer=MemorySaver(),
            interrupt_before=["synthesize"],
        )
        
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state: SentinelState = {
            "messages": [HumanMessage(content=f"Analyze {symbol} for {action}")],
            "symbol": symbol.upper(),
            "action": action,
            "market_price": 67000,
            "market_trend": "NEUTRAL",
            "lat": 28.6139,
            "lon": 77.2090,
            "market_response": None,
            "bull_response": None,
            "bear_response": None,
            "astro_response": None,
            "cycle_response": None,
            "dow_response": None,
            "andrews_response": None,
            "gann_response": None,
            "merriman_response": None,
            "meridian_response": None,
            "synthesis": None,
            "final_verdict": Signal.NEUTRAL,
            "errors": [],
            "confidence_avg": 0,
        }
        
        # Run until interrupt
        state = await app.ainvoke(initial_state, config)
        
        # Store responses so far
        await self._store_responses(state)
        
        # Return state for human review
        return state
    
    def get_state(self, thread_id: str) -> Optional[dict]:
        """Get current state of a thread."""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)
        return state.configurable if state else None


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class LangGraphOrchestrator:
    """
    Original LangGraphOrchestrator (backward compatible).
    
    For new projects, use MemoryEnabledOrchestrator instead.
    """
    
    def __init__(
        self,
        checkpointer: Optional[MemorySaver] = None,
        interrupt_before: Optional[list] = None,
    ):
        checkpointer = checkpointer or MemorySaver()
        interrupt_before = interrupt_before or []
        
        # No module-level memory for backward compat
        _set_module_memory(None)
        
        graph = build_graph()
        self.app = graph.compile(
            checkpointer=checkpointer,
            interrupt_before=interrupt_before,
        )
    
    async def analyze(
        self,
        symbol: str,
        action: str = "hold",
        thread_id: Optional[str] = None,
        lat: float = 28.6139,
        lon: float = 77.2090,
    ) -> dict:
        """Run analysis (memory integration if module-level memory is set)."""
        thread_id = thread_id or f"{symbol}_{int(asyncio.get_event_loop().time())}"
        config = {"configurable": {"thread_id": thread_id}}
        
        initial_state: SentinelState = {
            "messages": [HumanMessage(content=f"Analyze {symbol} for {action}")],
            "symbol": symbol.upper(),
            "action": action,
            "market_price": 67000,
            "market_trend": "NEUTRAL",
            "lat": lat,
            "lon": lon,
            "market_response": None,
            "bull_response": None,
            "bear_response": None,
            "astro_response": None,
            "cycle_response": None,
            "dow_response": None,
            "andrews_response": None,
            "gann_response": None,
            "merriman_response": None,
            "meridian_response": None,
            "synthesis": None,
            "final_verdict": Signal.NEUTRAL,
            "errors": [],
            "confidence_avg": 0,
        }
        
        final_state = await self.app.ainvoke(initial_state, config)
        return final_state
    
    async def analyze_with_review(
        self,
        symbol: str,
        action: str = "hold",
    ) -> dict:
        """Analyze with human review."""
        orchestrator = LangGraphOrchestrator(interrupt_before=["synthesize"])
        
        config = {"configurable": {"thread_id": f"{symbol}_review"}}
        
        initial_state = {
            "messages": [HumanMessage(content=f"Analyze {symbol} for {action}")],
            "symbol": symbol.upper(),
            "action": action,
            "market_price": 67000,
            "market_trend": "NEUTRAL",
            "lat": 28.6139,
            "lon": 77.2090,
            "market_response": None,
            "bull_response": None,
            "bear_response": None,
            "astro_response": None,
            "cycle_response": None,
            "dow_response": None,
            "andrews_response": None,
            "gann_response": None,
            "merriman_response": None,
            "meridian_response": None,
            "synthesis": None,
            "final_verdict": Signal.NEUTRAL,
            "errors": [],
            "confidence_avg": 0,
        }
        
        state = await orchestrator.app.ainvoke(initial_state, config)
        final_state = await orchestrator.app.ainvoke(None, config)
        return final_state
    
    def get_state(self, thread_id: str) -> Optional[dict]:
        """Get current state."""
        config = {"configurable": {"thread_id": thread_id}}
        state = self.app.get_state(config)
        return state.configurable if state else None


# =============================================================================
# CLI TEST
# =============================================================================

async def main():
    """Test run."""
    print("🔮 asurdev Sentinel v3.2 (Refactored)")
    print("=" * 50)
    
    orchestrator = MemoryEnabledOrchestrator()
    
    print("\n📊 Running full analysis...")
    result = await orchestrator.analyze("BTC", action="hold")
    
    print(f"\n{'='*50}")
    print(f"📊 Final Verdict: {result['final_verdict'].value}")
    print(f"📈 Avg Confidence: {result['confidence_avg']:.1f}%")
    
    print("\n📋 Agent Signals:")
    agent_keys = [
        "market", "bull", "bear", "astro", "cycle",
        "dow", "andrews", "gann", "meridian"
    ]
    for key in agent_keys:
        resp = result.get(f"{key}_response")
        if resp:
            print(f"  {key:12}: {resp.signal} ({resp.confidence}%)")
    
    if result.get("synthesis"):
        print(f"\n💬 Synthesis: {result['synthesis'].summary[:300]}...")
    
    # Show AstroCouncil specifically
    if result.get("astro_response"):
        astro = result["astro_response"]
        print(f"\n🌙 AstroCouncil Details:")
        if astro.details:
            for k, v in list(astro.details.items())[:5]:
                print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
