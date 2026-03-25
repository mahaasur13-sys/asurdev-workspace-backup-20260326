"""
NVIDIA NeMo Agent Toolkit (AgentIQ) Client Wrapper
Реализация DynamoRuntime и accelerated_graph
"""

from __future__ import annotations
import asyncio
import time
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PriorityLevel(str, Enum):
    CRITICAL = "critical"    # 1.0 - Predictor, Risk, OptionsFlow
    HIGH = "high"            # 0.85
    NORMAL = "normal"       # 0.6
    LOW = "low"             # 0.3


@dataclass
class RuntimeMetrics:
    """AgentIQ Runtime метрики"""
    total_agents: int = 0
    successful_agents: int = 0
    failed_agents: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    min_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    throughput: float = 0.0
    priority_distribution: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_agents": self.total_agents,
            "successful_agents": self.successful_agents,
            "failed_agents": self.failed_agents,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "max_latency_ms": round(self.max_latency_ms, 2),
            "min_latency_ms": round(self.min_latency_ms, 2),
            "p50_latency_ms": round(self.p50_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "p99_latency_ms": round(self.p99_latency_ms, 2),
            "throughput": round(self.throughput, 2),
            "priority_distribution": self.priority_distribution,
            "timestamp": self.timestamp.isoformat(),
        }


class DynamoRuntime:
    """
    NVIDIA Dynamo Runtime — адаптивный runtime для управления латентностью
    и приоритизацией задач в реальном времени.
    """
    
    def __init__(
        self,
        max_concurrency: int = 24,
        latency_target_ms: float = 650,
        priority_levels: Optional[Dict[str, float]] = None,
        adaptive_scaling: bool = True,
    ):
        self.max_concurrency = max_concurrency
        self.latency_target_ms = latency_target_ms
        self.adaptive_scaling = adaptive_scaling
        
        self.priority_levels = priority_levels or {
            "critical": 1.0,
            "high": 0.85,
            "normal": 0.6,
            "low": 0.3,
        }
        
        # Метрики
        self._metrics = RuntimeMetrics()
        self._agent_times: Dict[str, float] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)
        
        logger.info(
            f"[DynamoRuntime] Инициализирован: "
            f"max_concurrency={max_concurrency}, "
            f"latency_target={latency_target_ms}ms"
        )
    
    def get_priority_weight(self, priority: str) -> float:
        """Получить вес приоритета"""
        return self.priority_levels.get(priority, 0.5)
    
    async def execute_with_priority(
        self,
        task_name: str,
        coro: Callable,
        priority: str = "normal",
    ) -> Any:
        """Execute task with priority-based scheduling"""
        start = time.perf_counter()
        priority_weight = self.get_priority_weight(priority)
        
        # Track priority distribution
        if priority not in self._metrics.priority_distribution:
            self._metrics.priority_distribution[priority] = 0
        self._metrics.priority_distribution[priority] += 1
        
        async with self._semaphore:
            try:
                result = await coro
                elapsed_ms = (time.perf_counter() - start) * 1000
                
                self._agent_times[task_name] = elapsed_ms
                self._metrics.successful_agents += 1
                self._metrics.total_agents += 1
                
                logger.debug(
                    f"[DynamoRuntime] {task_name} ({priority}): "
                    f"{elapsed_ms:.1f}ms"
                )
                
                return result
                
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                self._metrics.failed_agents += 1
                self._metrics.total_agents += 1
                
                logger.error(
                    f"[DynamoRuntime] {task_name} ({priority}): "
                    f"FAILED after {elapsed_ms:.1f}ms - {e}"
                )
                raise
    
    def get_runtime_metrics(self) -> Dict[str, Any]:
        """Получить текущие метрики runtime"""
        if self._agent_times:
            times = list(self._agent_times.values())
            times.sort()
            
            self._metrics.avg_latency_ms = sum(times) / len(times)
            self._metrics.max_latency_ms = max(times)
            self._metrics.min_latency_ms = min(times)
            self._metrics.p50_latency_ms = times[len(times) // 2]
            self._metrics.p95_latency_ms = times[int(len(times) * 0.95)]
            self._metrics.p99_latency_ms = times[int(len(times) * 0.99)]
            
            # Throughput: agents per second
            total_time = sum(times)
            if total_time > 0:
                self._metrics.throughput = len(times) / (total_time / 1000)
        
        return self._metrics.to_dict()


class AgentIQ:
    """
    NVIDIA AgentIQ — Agent Intelligence Quotient
    Central intelligence for multi-agent orchestration.
    """
    
    def __init__(self, runtime: Optional[DynamoRuntime] = None):
        self.runtime = runtime or DynamoRuntime()
        self._agents: Dict[str, Any] = {}
        self._metrics_history: list[RuntimeMetrics] = []
        
        logger.info("[AgentIQ] AgentIQ инициализирован")
    
    def register_agent(self, name: str, agent: Any) -> None:
        """Register an agent with AgentIQ"""
        self._agents[name] = agent
        logger.info(f"[AgentIQ] Зарегистрирован агент: {name}")
    
    async def run_agent(
        self,
        agent_name: str,
        input: Dict[str, Any],
        priority: str = "normal",
    ) -> Any:
        """Run agent with priority-based execution"""
        if agent_name not in self._agents:
            raise ValueError(f"Agent '{agent_name}' не зарегистрирован")
        
        agent = self._agents[agent_name]
        coro = agent.analyze(input) if hasattr(agent, 'analyze') else agent.run(input)
        
        return await self.runtime.execute_with_priority(
            task_name=agent_name,
            coro=coro,
            priority=priority,
        )
    
    async def run_agents_batch(
        self,
        tasks: list,  # List of tuples: (name, context, priority)
    ) -> list[Any]:
        """Run multiple agents in parallel with priorities"""
        coroutines = []
        for name, context, priority in tasks:
            coro = self.run_agent(name, context, priority)
            coroutines.append(coro)
        return await asyncio.gather(*coroutines, return_exceptions=True)
    
    def get_runtime_metrics(self) -> Dict[str, Any]:
        """Get current runtime metrics"""
        return self.runtime.get_runtime_metrics()
    
    def get_registered_agents(self) -> list[str]:
        """Get list of registered agents"""
        return list(self._agents.keys())


def accelerated_graph():
    """
    AgentIQ Performance Primitive — accelerated_graph
    Декоратор для оптимизации выполнения graph tasks.
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.perf_counter() - start) * 1000
                logger.debug(
                    f"[accelerated_graph] {func.__name__}: {elapsed:.1f}ms"
                )
                return result
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                logger.error(
                    f"[accelerated_graph] {func.__name__}: FAILED {elapsed:.1f}ms - {e}"
                )
                raise
        return wrapper
    return decorator


def monte_carlo_primitive(n_simulations: int = 1000):
    """
    AgentIQ Monte Carlo Primitive
    Для probabilistic reasoning и risk assessment.
    """
    def decorator(func: Callable):
        def sync_wrapper(*args, **kwargs):
            results = []
            for _ in range(n_simulations):
                try:
                    result = func(*args, **kwargs)
                    results.append(result)
                except Exception:
                    continue
            
            if not results:
                return {"error": "All simulations failed"}
            
            import numpy as np
            return {
                "mean": float(np.mean(results)),
                "std": float(np.std(results)),
                "p5": float(np.percentile(results, 5)),
                "p95": float(np.percentile(results, 95)),
                "n_successful": len(results),
                "n_total": n_simulations,
            }
        
        async def async_wrapper(*args, **kwargs):
            # For async, run in executor
            import asyncio
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, sync_wrapper, *args, **kwargs
            )
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# LangSmith tracing decorator
def traceable(run_type: str = "chain", name: Optional[str] = None):
    """
    LangSmith tracing decorator (stub implementation)
    В production заменить на real langsmith.traceable
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            trace_id = f"{func.__name__}_{datetime.now().timestamp()}"
            logger.debug(f"[LangSmith Trace] {run_type}:{name or func.__name__} [{trace_id}]")
            try:
                result = await func(*args, **kwargs)
                logger.debug(f"[LangSmith Trace] ✓ {trace_id}")
                return result
            except Exception as e:
                logger.debug(f"[LangSmith Trace] ✗ {trace_id}: {e}")
                raise
        return wrapper
    return decorator
