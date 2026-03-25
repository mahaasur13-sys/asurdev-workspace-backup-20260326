"""LangSmith integration for asurdev Sentinel observability."""

import os
from typing import Optional
from langsmith import traceable
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tracers.context import collect_runs

# LangSmith configuration
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGSMITH_PROJECT", "asurdev-sentinel")

# Environment check
if LANGCHAIN_API_KEY:
    os.environ["LANGSMITH_API_KEY"] = LANGCHAIN_API_KEY
    print(f"✓ LangSmith enabled: project={LANGCHAIN_PROJECT}")
else:
    print("⚠️  LANGSMITH_API_KEY not set — tracing disabled")


def get_tracer_config():
    """Get LangSmith tracer configuration."""
    if not LANGCHAIN_API_KEY:
        return None
    return {
        "project_name": LANGCHAIN_PROJECT,
        "example_id": None,
    }


class SentinelTracer:
    """Context manager for tracing agent runs."""

    def __init__(self, project: str = "asurdev-sentinel"):
        self.project = project

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    async def trace_agent(self, agent_name: str, func, *args, **kwargs):
        """Trace an agent function."""
        return await traceable(
            name=f"asurdev:{agent_name}",
            tags=[agent_name, "asurdev"],
            metadata={"project": self.project}
        )(func)(*args, **kwargs)

    def trace_sync(self, agent_name: str, func, *args, **kwargs):
        """Trace a synchronous agent function."""
        return traceable(
            name=f"asurdev:{agent_name}",
            tags=[agent_name, "asurdev"],
            metadata={"project": self.project}
        )(func)(*args, **kwargs)


# Decorator for tracing agent methods
def trace_agent(agent_name: str = None):
    """Decorator to trace agent methods in LangSmith."""
    def decorator(func):
        return traceable(
            name=agent_name or f"asurdev:{func.__name__}",
            tags=["agent", agent_name] if agent_name else ["agent"],
        )(func)
    return decorator


async def run_with_tracing(agent_name: str, func, *args, **kwargs):
    """Run agent with LangSmith tracing."""
    async with collect_runs() as runs:
        result = await func(*args, **kwargs)
        return result


def log_agent_call(agent_name: str, input_data: dict, output_data: dict):
    """Log agent call to console (fallback when LangSmith unavailable)."""
    print(f"\n{'='*60}")
    print(f"🤖 {agent_name}")
    print(f"{'='*60}")
    print(f"Input: {input_data}")
    print(f"Output: {output_data}")
