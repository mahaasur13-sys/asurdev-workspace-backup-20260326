"""
Memory Integration Layer — Injects RAG Context into Agents
asurdev Sentinel v3.2
"""

from __future__ import annotations
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from .manager import MemoryManager, SessionMemory
from .fuzzy import FuzzyMemory
from ..types import AgentResponse


@dataclass
class AgentMemoryContext:
    """Context passed to agent with RAG-enhanced memory."""
    session_id: str
    symbol: str
    agent_name: str
    previous_analyses: List[Dict] = field(default_factory=list)
    similar_outcomes: List[Dict] = field(default_factory=list)
    learned_patterns: List[Dict] = field(default_factory=list)
    adaptive_weight: float = 1.0
    memory_summary: str = ""


class MemoryMiddleware:
    """
    Memory integration for LangGraph agents.
    
    Responsibilities:
    1. Build RAG context before agent runs
    2. Store responses after agent completes
    3. Track adaptive weights for synthesis
    
    Usage:
        mm = MemoryMiddleware()
        orchestrator = LangGraphOrchestrator(memory=mm)
    """
    
    def __init__(
        self,
        persist_dir: str = "./data/chroma_db",
        enable_rag: bool = True,
        enable_adaptive_weights: bool = True,
    ):
        self.memory = MemoryManager(persist_dir=persist_dir, enable_rag=enable_rag)
        self.enable_adaptive_weights = enable_adaptive_weights
        self._current_session: Optional[SessionMemory] = None
    
    @property
    def chroma(self):
        return self.memory.chroma
    
    @property
    def fuzzy(self):
        return self.memory.fuzzy
    
    def start_session(self, session_id: str, symbol: str, action: str) -> SessionMemory:
        """Start a new analysis session."""
        self._current_session = self.memory.start_session(session_id, symbol, action)
        return self._current_session
    
    def get_context_for_agent(
        self,
        agent_name: str,
        symbol: str,
        n_similar: int = 3,
    ) -> AgentMemoryContext:
        """
        Build memory context for a specific agent.
        
        Args:
            agent_name: Which agent will receive context
            symbol: Trading symbol (BTC, ETH, etc.)
            n_similar: Number of similar past analyses to retrieve
            
        Returns:
            AgentMemoryContext with RAG data
        """
        if not self._current_session:
            return AgentMemoryContext(
                session_id="no_session",
                symbol=symbol,
                agent_name=agent_name,
            )
        
        session = self._current_session
        
        # 1. Get similar past analyses for this agent + symbol
        similar = self.memory.recall_similar(
            query=f"{symbol} {agent_name}",
            agent=agent_name,
            n=n_similar,
        )
        
        # 2. Get past outcomes for this agent + symbol
        outcomes = []
        if self.chroma:
            outcomes = self.chroma.recall_agent_history(
                agent=agent_name,
                symbol=symbol,
                n=5,
            )
        
        # 3. Get learned patterns
        patterns = []
        if self.chroma:
            patterns = self.chroma.recall_patterns(
                pattern_type=agent_name,
                n=3,
            )
        
        # 4. Get adaptive weight
        weight = 1.0
        if self.enable_adaptive_weights and self.fuzzy:
            rec = self.fuzzy.get_recommendation(
                agent=agent_name,
                symbol=symbol,
            )
            weight = rec.get("weight", 1.0)
        
        # 5. Build summary string
        summary_parts = [f"[Memory Context for {agent_name}]"]
        
        if similar:
            summary_parts.append(f"\nLast {len(similar)} analyses for {symbol}:")
            for i, s in enumerate(similar[:3], 1):
                data = s.get("data", {})
                sig = data.get("signal", "N/A")
                conf = data.get("confidence", 0)
                summary_parts.append(f"  {i}. {sig} ({conf}%)")
        
        if patterns:
            summary_parts.append(f"\nLearned patterns:")
            for p in patterns[:2]:
                pt = p.get("pattern_type", "unknown")
                desc = p.get("description", "")[:80]
                summary_parts.append(f"  - {pt}: {desc}...")
        
        if outcomes:
            correct = sum(
                1 for o in outcomes 
                if o.get("metadata", {}).get("actual_direction") == o.get("metadata", {}).get("prediction")
            )
            summary_parts.append(f"\nHistorical accuracy: {correct}/{len(outcomes)}")
        
        return AgentMemoryContext(
            session_id=session.session_id,
            symbol=symbol,
            agent_name=agent_name,
            previous_analyses=similar,
            similar_outcomes=outcomes,
            learned_patterns=patterns,
            adaptive_weight=weight,
            memory_summary="\n".join(summary_parts),
        )
    
    def format_memory_context(
        self,
        ctx: AgentMemoryContext,
        max_length: int = 1500,
    ) -> str:
        """
        Format memory context as a string for LLM prompt injection.
        
        Args:
            ctx: AgentMemoryContext
            max_length: Maximum characters to return
            
        Returns:
            Formatted string for prompt injection
        """
        if not ctx.memory_summary:
            return ""
        
        # Truncate if needed
        summary = ctx.memory_summary
        if len(summary) > max_length:
            summary = summary[:max_length] + "\n... (truncated)"
        
        # Add instruction
        return f"""{summary}

[IMPORTANT] Use the context above to inform your analysis. If similar past 
analyses exist, consider whether current conditions match those patterns.
Your adaptive weight for final synthesis: {ctx.adaptive_weight:.2f}"""
    
    async def store_agent_response(
        self,
        agent_name: str,
        response: AgentResponse,
        symbol: str,
        market_state: Dict[str, Any],
    ) -> Optional[str]:
        """
        Store agent response to ChromaDB for future RAG retrieval.
        """
        if not self.memory or not self._current_session:
            return None
        
        try:
            doc_id = self.memory.store_analysis(
                symbol=symbol,
                agent=agent_name,
                signal=response.signal,
                confidence=response.confidence,
                reasoning=response.summary,
                market_state=market_state,
            )
            
            # Also add to session memory
            self._current_session.add(
                agent=agent_name,
                content=f"{response.signal} ({response.confidence}%) - {response.summary[:100]}",
                metadata={
                    "signal": response.signal,
                    "confidence": response.confidence,
                },
            )
            
            return doc_id
            
        except Exception as e:
            print(f"[Memory] Failed to store {agent_name} response: {e}")
            return None
    
    def add_feedback(
        self,
        analysis_id: str,
        agent: str,
        helpful: bool,
        rating: int,
        correction: Optional[str] = None,
    ):
        """Record user feedback for an analysis."""
        if self.memory:
            self.memory.add_feedback(analysis_id, agent, helpful, rating, correction)
    
    def add_outcome(
        self,
        symbol: str,
        agent: str,
        prediction: str,
        actual_direction: str,
        confidence: float,
        price_change: float,
    ):
        """Record actual outcome for learning."""
        if self.memory:
            outcome = "correct" if prediction == actual_direction else "incorrect"
            self.memory.add_outcome(
                symbol=symbol,
                agent=agent,
                prediction=prediction,
                outcome=outcome,
                confidence=confidence,
                price_change=price_change,
            )
    
    def get_adaptive_weights(
        self,
        symbol: str,
        market_condition: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get adaptive weights for all agents."""
        if not self.enable_adaptive_weights or not self.fuzzy:
            return FuzzyMemory.DEFAULT_WEIGHTS
        
        return self.memory.get_agent_weights(symbol, market_condition)
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get performance stats for an agent."""
        if self.chroma:
            return self.chroma.get_agent_stats(agent)
        return {"agent": agent, "status": "no_data"}
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get overall memory statistics."""
        return self.memory.get_memory_stats()
    
    def learn_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence: float,
        evidence: List[str],
        agent: Optional[str] = None,
    ) -> str:
        """Learn a new pattern from analysis."""
        if self.chroma:
            return self.chroma.learn_pattern(pattern_type, description, confidence, evidence, agent)
        return ""


class MemoryAwareAgentNode:
    """
    LangGraph node wrapper that injects memory context and stores results.
    
    Usage:
        node = MemoryAwareAgentNode(
            agent=MarketAnalyst(),
            field_name="market_response",
            memory=middleware,
        )
    """
    
    def __init__(
        self,
        agent,
        field_name: str,
        memory: Optional[MemoryMiddleware] = None,
        inject_context: bool = True,
    ):
        self.agent = agent
        self.field_name = field_name
        self.memory = memory
        self.inject_context = inject_context
        
        # Get agent name
        self.agent_name = getattr(agent, "name", field_name.replace("_response", ""))
    
    def _build_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Build context dict for agent.analyze()."""
        context = {
            "symbol": state.get("symbol", "BTC"),
            "action": state.get("action", "hold"),
            "market_data": {
                "current_price": state.get("market_price", 67000),
                "trend": state.get("market_trend", "NEUTRAL"),
            }
        }
        
        # Inject memory context if enabled and available
        if self.inject_context and self.memory:
            mem_ctx = self.memory.get_context_for_agent(
                agent_name=self.agent_name,
                symbol=context["symbol"],
                n_similar=3,
            )
            context["memory"] = mem_ctx
            context["memory_summary"] = self.memory.format_memory_context(mem_ctx)
        
        return context
    
    async def run(self, state: Dict[str, Any]) -> dict:
        """
        Run agent with memory integration.
        
        1. Build context with RAG memory
        2. Run agent.analyze()
        3. Store response to ChromaDB
        4. Return response in state dict
        """
        symbol = state.get("symbol", "BTC")
        response = None
        
        try:
            # Build context
            context = self._build_context(state)
            
            # Run agent
            if asyncio.iscoroutinefunction(self.agent.analyze):
                response = await asyncio.wait_for(
                    self.agent.analyze(context),
                    timeout=120,
                )
            else:
                response = self.agent.analyze(context)
            
            # Store to memory
            if self.memory:
                await self.memory.store_agent_response(
                    agent_name=self.agent_name,
                    response=response,
                    symbol=symbol,
                    market_state=context.get("market_data", {}),
                )
            
            return {self.field_name: response}
            
        except asyncio.TimeoutError:
            return {
                self.field_name: AgentResponse(
                    agent_name=self.agent_name,
                    signal="ERROR",
                    confidence=0,
                    summary=f"{self.agent_name} timed out after 120s",
                ),
                "errors": [f"{self.agent_name}: Timeout after 120s"],
            }
        except Exception as e:
            error_response = response if response else AgentResponse(
                agent_name=self.agent_name,
                signal="ERROR",
                confidence=0,
                summary=str(e),
            )
            return {
                self.field_name: error_response,
                "errors": [f"{self.agent_name}: {e}"],
            }


def get_agent_field_mapping() -> Dict[str, str]:
    """
    Map agent names to their response field names in SentinelState.
    """
    return {
        "market": "market_response",
        "bull": "bull_response",
        "bear": "bear_response",
        "astro": "astro_response",
        "cycle": "cycle_response",
        "dow": "dow_response",
        "andrews": "andrews_response",
        "gann": "gann_response",
        "meridian": "meridian_response",
    }


def get_memory_weighted_synthesis(
    responses: Dict[str, Any],
    weights: Dict[str, float],
) -> Dict[str, Any]:
    """
    Perform weighted synthesis of agent responses.
    
    Unlike simple voting, this multiplies each agent's confidence
    by its adaptive weight to produce a more intelligent verdict.
    
    Args:
        responses: Dict of field_name -> AgentResponse
        weights: Dict of agent_name -> weight (from FuzzyMemory)
        
    Returns:
        Dict with signal, confidence, weighted_signals
    """
    weighted_signals = {"BULLISH": 0.0, "BEARISH": 0.0, "NEUTRAL": 0.0}
    agent_scores = {}
    
    for field_name, response in responses.items():
        if response is None:
            continue
        
        # Extract agent name from field (e.g., "market_response" -> "market")
        agent_name = field_name.replace("_response", "")
        
        # Get weight (default 0.1)
        weight = weights.get(agent_name, 0.1)
        
        signal = response.signal
        confidence = response.confidence
        
        if signal in weighted_signals:
            # Weighted contribution
            weighted_signals[signal] += confidence * weight
            agent_scores[agent_name] = {
                "signal": signal,
                "confidence": confidence,
                "weight": weight,
                "weighted_contribution": confidence * weight,
            }
    
    # Determine final signal
    max_signal = max(weighted_signals, key=weighted_signals.get)
    total_weighted = sum(weighted_signals.values())
    
    # Calculate final confidence
    if total_weighted > 0:
        final_confidence = total_weighted / sum(weights.get(a, 0.1) for a in agent_scores.keys())
    else:
        final_confidence = 50
    
    return {
        "signal": max_signal,
        "confidence": min(100, max(0, final_confidence)),
        "weighted_signals": weighted_signals,
        "agent_scores": agent_scores,
        "weights_used": weights,
    }
