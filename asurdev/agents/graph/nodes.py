"""
LangGraph Node Definitions — Agent Execution Nodes
asurdev Sentinel v3.2
"""

from __future__ import annotations
import asyncio
from typing import Optional, Dict, Any, Literal

from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from ..types import AgentResponse, Signal
from ..state import SentinelState

# LangSmith tracing (optional)
LANGSMITH_AVAILABLE = False
try:
    from langsmith import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    def traceable(**kwargs):
        return lambda f: f  # No-op decorator


# =============================================================================
# AGENT NODE WRAPPER
# =============================================================================

class AgentNode:
    """
    Wraps sync/async agent as async LangGraph node.
    Handles timeout, error catching, and response normalization.
    """
    
    def __init__(self, agent, field_name: str):
        self.agent = agent
        self.field_name = field_name
    
    async def run(self, state: SentinelState) -> dict:
        try:
            context = {
                "symbol": state["symbol"],
                "action": state["action"],
                "market_data": {
                    "current_price": state.get("market_price", 67000),
                    "trend": state.get("market_trend", "NEUTRAL"),
                }
            }
            
            if asyncio.iscoroutinefunction(self.agent.analyze):
                response: AgentResponse = await asyncio.wait_for(
                    self.agent.analyze(context),
                    timeout=120
                )
            else:
                response = self.agent.analyze(context)
            
            return {self.field_name: response}
            
        except asyncio.TimeoutError:
            return {
                self.field_name: AgentResponse(
                    agent_name=self.field_name,
                    signal="ERROR",
                    confidence=0,
                    summary=f"{self.field_name} timed out"
                ),
                "errors": [f"{self.field_name}: Timeout"]
            }
        except Exception as e:
            return {
                self.field_name: AgentResponse(
                    agent_name=self.field_name,
                    signal="ERROR",
                    confidence=0,
                    summary=str(e)
                ),
                "errors": [f"{self.field_name}: {e}"]
            }


# =============================================================================
# MODULE-LEVEL MEMORY (set by orchestrator)
# =============================================================================

_memory_middleware = None


def _set_memory(memory) -> None:
    """Set module-level memory middleware for nodes to access."""
    global _memory_middleware
    _memory_middleware = memory


def _get_memory():
    """Get module-level memory middleware."""
    return _memory_middleware


# =============================================================================
# NODE FUNCTIONS
# =============================================================================

async def node_market(state: SentinelState) -> dict:
    """Technical market analysis node with memory integration."""
    from .._impl.market_analyst import MarketAnalyst
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = MarketAnalyst()
    memory = _get_memory()
    
    if memory:
        node = MemoryAwareAgentNode(agent, "market_response", memory=memory)
        result = await node.run(state)
    else:
        node = AgentNode(agent, "market_response")
        result = await node.run(state)
    
    market = result.get("market_response")
    if market:
        trend_map = {
            "BUY": "BULLISH", "STRONG_BUY": "BULLISH",
            "SELL": "BEARISH", "STRONG_SELL": "BEARISH",
        }
        result["market_trend"] = trend_map.get(market.signal, "NEUTRAL")
    
    return result


@traceable(name="asurdev:BullResearcher", tags=["bull"])
async def node_bull(state: SentinelState) -> dict:
    """Bullish fundamental research node with memory integration."""
    from .._impl.bull_researcher import BullResearcher
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = BullResearcher()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "bull_response", memory=memory).run(state)
    return await AgentNode(agent, "bull_response").run(state)


@traceable(name="asurdev:BearResearcher", tags=["bear"])
async def node_bear(state: SentinelState) -> dict:
    """Bearish fundamental research node with memory integration."""
    from .._impl.bear_researcher import BearResearcher
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = BearResearcher()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "bear_response", memory=memory).run(state)
    return await AgentNode(agent, "bear_response").run(state)


@traceable(name="asurdev:AstroCouncil", tags=["astro"])
async def node_astro(state: SentinelState) -> dict:
    """
    Astro Council node — coordinates Western + Vedic + Financial astrology.
    """
    from .._impl.astro_council.agent import AstroCouncilAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = AstroCouncilAgent(
        lat=state.get("lat", 28.6139),
        lon=state.get("lon", 77.2090),
        use_rag=True
    )
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "astro_response", memory=memory).run(state)
    return await AgentNode(agent, "astro_response").run(state)


@traceable(name="asurdev:Cycle", tags=["cycle"])
async def node_cycle(state: SentinelState) -> dict:
    """Cycle analysis node with memory integration."""
    from .._impl.cycle_agent import CycleAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = CycleAgent()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "cycle_response", memory=memory).run(state)
    return await AgentNode(agent, "cycle_response").run(state)


@traceable(name="asurdev:Dow", tags=["dow"])
async def node_dow(state: SentinelState) -> dict:
    """Dow Theory node with memory integration."""
    from .._impl.dow_agent import DowTheoryAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = DowTheoryAgent()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "dow_response", memory=memory).run(state)
    return await AgentNode(agent, "dow_response").run(state)


@traceable(name="asurdev:Andrews", tags=["andrews"])
async def node_andrews(state: SentinelState) -> dict:
    """Andrews Pitchfork node with memory integration."""
    from .._impl.andrews_agent import AndrewsAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = AndrewsAgent()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "andrews_response", memory=memory).run(state)
    return await AgentNode(agent, "andrews_response").run(state)


@traceable(name="asurdev:Gann", tags=["gann"])
async def node_gann(state: SentinelState) -> dict:
    """Gann analysis node with memory integration."""
    from .._impl.gann_agent import GannAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = GannAgent()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "gann_response", memory=memory).run(state)
    return await AgentNode(agent, "gann_response").run(state)


@traceable(name="asurdev:Meridian", tags=["meridian"])
async def node_meridian(state: SentinelState) -> dict:
    """Meridian analysis node with memory integration."""
    from .._impl.meridian_agent import MeridianAgent
    from ..memory.integration import MemoryAwareAgentNode
    
    agent = MeridianAgent()
    memory = _get_memory()
    
    if memory:
        return await MemoryAwareAgentNode(agent, "meridian_response", memory=memory).run(state)
    return await AgentNode(agent, "meridian_response").run(state)


async def node_synthesize(state: SentinelState) -> dict:
    """
    Final synthesis node — creates TradingSignal.
    Uses adaptive weights from FuzzyMemory if available.
    """
    from .._impl.synthesizer import Synthesizer
    from ..memory.integration import get_memory_weighted_synthesis
    from ..memory.fuzzy import FuzzyMemory
    
    agent = Synthesizer()
    memory = _get_memory()
    
    try:
        synthesis: AgentResponse = await asyncio.wait_for(
            agent.synthesize(
                market=state.get("market_response"),
                bull=state.get("bull_response"),
                bear=state.get("bear_response"),
                astro=state.get("astro_response"),
                cycle=state.get("cycle_response"),
            ),
            timeout=120
        )
        
        # Map to unified Signal enum
        verdict = Signal.from_string(synthesis.signal)
        
        # Collect all responses for weighted synthesis
        response_fields = [
            "market_response", "bull_response", "bear_response",
            "astro_response", "cycle_response", "dow_response",
            "andrews_response", "gann_response", "merriman_response",
            "meridian_response"
        ]
        responses = {
            field: state.get(field) 
            for field in response_fields 
            if state.get(field) is not None
        }
        
        # Get adaptive weights if memory is available
        adaptive_weights = None
        if memory:
            adaptive_weights = memory.get_adaptive_weights(
                symbol=state.get("symbol", "BTC"),
                market_condition=state.get("market_trend"),
            )
        
        # Calculate weighted synthesis
        if adaptive_weights and responses:
            weighted_result = get_memory_weighted_synthesis(responses, adaptive_weights)
            verdict = Signal.from_string(weighted_result["signal"])
            synthesis.details = synthesis.details or {}
            synthesis.details["weighted_synthesis"] = weighted_result
            synthesis.details["adaptive_weights_used"] = adaptive_weights
        
        # Calculate average confidence from all responses
        valid = [r.confidence for r in responses.values() if r and r.confidence > 0]
        avg_conf = sum(valid) / len(valid) if valid else 0
        
        return {
            "synthesis": synthesis,
            "final_verdict": verdict,
            "confidence_avg": avg_conf,
        }
        
    except Exception as e:
        return {
            "synthesis": AgentResponse(
                agent_name="synthesizer",
                signal="ERROR",
                confidence=0,
                summary=str(e)
            ),
            "errors": [f"synthesize: {e}"]
        }
