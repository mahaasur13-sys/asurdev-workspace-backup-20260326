"""
AgentIQ Compatibility Layer.
Provides stubs for AgentIQ when not available.
"""
from typing import Any, Dict, Optional
import asyncio


class DynamoRuntime:
    """Stub for DynamoRuntime."""
    def __init__(self, max_concurrency: int = 10, latency_target_ms: int = 1000, priority_levels: Optional[Dict] = None):
        self.max_concurrency = max_concurrency
        self.latency_target_ms = latency_target_ms
        self.priority_levels = priority_levels or {}


class AgentIQ:
    """
    AgentIQ stub — real implementation would use NVIDIA AIQ toolkit.
    Currently runs agents directly without optimization.
    """
    def __init__(self, runtime: Optional[DynamoRuntime] = None):
        self.runtime = runtime
        self._agents: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__) if False else None

    def register_agent(self, name: str, agent: Any):
        self._agents[name] = agent

    async def run(self, agent: str, input: Dict, priority: str = "normal") -> Any:
        """Run registered agent directly."""
        agent_instance = self._agents.get(agent)
        if agent_instance is None:
            raise ValueError(f"Agent {agent} not registered")
        
        # Direct execution (no optimization)
        if hasattr(agent_instance, "analyze"):
            return await agent_instance.analyze(input)
        elif hasattr(agent_instance, "run"):
            return await agent_instance.run(input)
        else:
            return await agent_instance(input)


# AgentIQ primitives (stubs)
def accelerated_graph(func):
    """Stub for accelerated_graph decorator."""
    return func


def monte_carlo_primitive(n_simulations: int = 10000, **kwargs):
    """Stub for monte_carlo_primitive."""
    def decorator(func):
        return func
    return decorator


def attention_primitive(hidden_size: int = 64, num_heads: int = 4, **kwargs):
    """Stub for attention_primitive."""
    def decorator(func):
        return func
    return decorator


# LangSmith stubs
class LangSmithClient:
    """Stub for LangSmith tracing."""
    pass


def traceable(run_type: str = "chain", **kwargs):
    """Stub for traceable decorator."""
    def decorator(func):
        return func
    return decorator
