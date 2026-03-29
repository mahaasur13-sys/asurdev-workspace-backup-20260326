"""mas_factory/engine.py - TopologyExecutor: runs agents from declarative blueprint"""
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from mas_factory.topology import Topology, Role, Connection, SwitchNode, Adapter

# Import all agent runners
# This replaces hard-coded flow runners in sentinel_v5.py

AGENT_RUNNERS: Dict[str, Callable] = {}


def _load_runners():
    """Lazy load agent runners"""
    global AGENT_RUNNERS
    if AGENT_RUNNERS:
        return
    
    try:
        from agents._impl.fundamental_agent import run_fundamental_agent
        from agents._impl.macro_agent import run_macro_agent
        from agents._impl.quant_agent import run_quant_agent
        from agents._impl.options_flow_agent import run_options_flow_agent
        from agents._impl.sentiment_agent import run_sentiment_agent
        from agents._impl.market_analyst import run_market_analyst
        from agents._impl.bull_researcher import run_bull_researcher
        from agents._impl.bear_researcher import run_bear_researcher
        from agents._impl.electoral_agent import run_electoral_agent
        from agents.astro_council_agent import run_astro_council
        
        AGENT_RUNNERS.update({
            "FundamentalAgent": run_fundamental_agent,
            "MacroAgent": run_macro_agent,
            "QuantAgent": run_quant_agent,
            "OptionsFlowAgent": run_options_flow_agent,
            "SentimentAgent": run_sentiment_agent,
            "MarketAnalyst": run_market_analyst,
            "BullResearcher": run_bull_researcher,
            "BearResearcher": run_bear_researcher,
            "ElectoralAgent": run_electoral_agent,
            "AstroCouncil": run_astro_council,
        })
    except ImportError as e:
        print(f"[MASFactory] Warning: Some agents not available: {e}")


@dataclass
class ExecutionNode:
    """Runtime state of a node during execution"""
    role: Role
    status: str = "pending"  # pending | running | completed | failed
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TopologyExecutor:
    """
    Executes agents from declarative Topology blueprint.
    
    This replaces hard-coded flow runners in sentinel_v5.py:
        OLD: run_technical_flow() { if "MarketAnalyst": ... }
        NEW: executor.execute(topology) → reads connections → runs agents dynamically
    
    Flow:
        1. Build execution graph from topology
        2. Execute entry point
        3. Traverse connections, running agents via adapters
        4. Collect results at exit point
    """
    
    def __init__(self, topology: Topology):
        self.topology = topology
        self.nodes: Dict[str, ExecutionNode] = {}
        self.context: Dict[str, Any] = {}
        self.execution_log: List[Dict] = []
        
        # Initialize nodes
        for role in topology.roles:
            self.nodes[role.name] = ExecutionNode(role=role)
    
    async def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute topology with initial context.
        
        Args:
            initial_context: {symbol, timeframe, user_query, price, ...}
        
        Returns:
            Dict with final_signal, confidence, breakdown, metadata
        """
        _load_runners()
        
        self.context = initial_context.copy()
        self.context["all_signals"] = []
        
        # Execute from entry point
        try:
            result = await self._execute_node(self.topology.entry_point)
            
            # Final synthesis
            if "synthesis" in self.nodes:
                synthesis_result = await self._run_synthesis()
                return synthesis_result
            
            return result
        except Exception as e:
            return {
                "signal": "NEUTRAL",
                "confidence": 30,
                "reasoning": f"Execution error: {str(e)[:200]}",
                "error": str(e),
            }
    
    def run_sync(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for testing"""
        return asyncio.run(self.execute(initial_context))
    
    async def _execute_node(self, node_id: str) -> Any:
        """Execute a single node"""
        if node_id not in self.nodes:
            return None
        
        node = self.nodes[node_id]
        
        # Check if already executed
        if node.status == "completed":
            return node.output
        
        # Execute based on type
        if node_id in self.topology.switch_nodes:
            return await self._execute_switch(node_id)
        elif node_id == "router":
            return await self._execute_router()
        elif node_id == "synthesis":
            return await self._run_synthesis()
        elif node_id == "end":
            return self.context.get("final_signal", {})
        else:
            return await self._run_agent(node.role)
    
    async def _execute_switch(self, switch_id: str) -> Any:
        """Execute switch/router node"""
        switch = next((s for s in self.topology.switch_nodes if s.id == switch_id), None)
        if not switch:
            return None
        
        # Decide which agents to run
        selected = switch.decide(self.context)
        
        results = []
        for agent_name in selected:
            if agent_name in self.nodes:
                result = await self._execute_node(agent_name)
                results.append(result)
        
        return results
    
    async def _execute_router(self) -> Any:
        """Execute router - route to appropriate agents"""
        # Use switch node logic
        return await self._execute_switch("router")
    
    async def _run_agent(self, role: Role) -> Dict[str, Any]:
        """Run a single agent from registry"""
        runner = AGENT_RUNNERS.get(role.agent_type)
        
        if not runner:
            return {
                "agent_name": role.name,
                "signal": "NEUTRAL",
                "confidence": 30,
                "reasoning": f"No runner for {role.agent_type}",
            }
        
        # Prepare context for this agent
        agent_context = {
            "symbol": self.context.get("symbol", "BTCUSDT"),
            "timeframe_requested": self.context.get("timeframe", "SWING"),
            "current_price": self.context.get("current_price", 50000),
            "birth_data": self.context.get("birth_data"),
            "user_query": self.context.get("user_query", ""),
            "session_id": self.context.get("session_id", "unknown"),
        }
        
        # Run with timeout
        try:
            if asyncio.iscoroutinefunction(runner):
                result = await asyncio.wait_for(
                    runner(agent_context),
                    timeout=role.timeout_ms / 1000
                )
            else:
                result = runner(agent_context)
            
            # Extract signal
            if isinstance(result, dict):
                signal = result.get("signal", {}) or {}
                if hasattr(signal, "to_dict"):
                    signal = signal.to_dict()
                
                # Add to all_signals
                self.context["all_signals"].append(signal)
                return signal
            
            return result
        except asyncio.TimeoutError:
            return {
                "agent_name": role.name,
                "signal": "NEUTRAL",
                "confidence": 20,
                "reasoning": f"Timeout after {role.timeout_ms}ms",
            }
        except Exception as e:
            return {
                "agent_name": role.name,
                "signal": "NEUTRAL",
                "confidence": 20,
                "reasoning": f"Agent error: {str(e)[:100]}",
            }
    
    async def _run_synthesis(self) -> Dict[str, Any]:
        """Run synthesis agent with all collected signals"""
        from agents.synthesis_agent import SynthesisAgent
        
        # Prepare synthesis state
        synthesis_state = {
            **self.context,
            "all_signals": self.context.get("all_signals", []),
        }
        
        try:
            agent = SynthesisAgent()
            result = await agent.run(synthesis_state)
            
            if hasattr(result, "to_dict"):
                return result.to_dict()
            return result
        except Exception as e:
            return {
                "signal": "NEUTRAL",
                "confidence": 30,
                "reasoning": f"Synthesis error: {str(e)[:200]}",
                "metadata": {
                    "all_signals": self.context.get("all_signals", []),
                },
            }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get execution summary for debugging"""
        return {
            "topology_hash": self.topology.compute_hash(),
            "nodes_executed": sum(1 for n in self.nodes.values() if n.status == "completed"),
            "nodes_failed": sum(1 for n in self.nodes.values() if n.status == "failed"),
            "signals_collected": len(self.context.get("all_signals", [])),
            "execution_log": self.execution_log,
        }
