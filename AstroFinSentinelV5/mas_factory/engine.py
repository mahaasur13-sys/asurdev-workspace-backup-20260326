""""mas_factory/engine.py - ATOM-R-025: TopologyExecutor with Switch Nodes + Meta-Questioning"""
import asyncio
import json
import time
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import asdict
from datetime import datetime
from mas_factory.topology import Topology, Role, Connection, SwitchNode, Message
from mas_factory.registry import get_registry
class TopologyExecutor:
    def __init__(self, topology: Topology, state: dict):
        self.topology = topology
        self.state = state
        self.results: Dict[str, Any] = {}
        self.messages: List[Message] = []
        self._execution_log = []
        self.registry = get_registry()
    def _log(self, msg: str):
        ts = datetime.now().isoformat()
        entry = f"[{ts}] {msg}"
        self._execution_log.append(entry)
        print(f"  [Executor] {msg}")
    async def run(self) -> Dict[str, Any]:
        self._log(f"Starting topology: {self.topology.hash[:8]} ({len(self.topology.roles)} roles)")
        for node in self.topology.switch_nodes:
            self._evaluate_switch(node)
        for role in self.topology.roles:
            await self._execute_role(role)
        for conn in self.topology.connections:
            await self._transfer(conn)
        self._log(f"Completed: {len(self.results)} results")
        return self.results
    def _evaluate_switch(self, switch: SwitchNode):
        ctx = self.state
        if switch.condition == "uncertainty_threshold":
            unc = ctx.get("uncertainty", {}).get("total", 0.5)
            result = unc > 0.6
            self._log(f"Switch [{switch.id}]: {switch.condition} {unc:.3f} > {0.6} = {result}")
            if result:
                for action in switch.then_actions:
                    self._apply_action(action)
        elif switch.condition == "oos_fail_threshold":
            oos = ctx.get("oos_fail_rate", 0.0)
            result = oos > 0.6
            self._log(f"Switch [{switch.id}]: {switch.condition} {oos:.3f} > {0.6} = {result}")
            if result:
                for action in switch.then_actions:
                    self._apply_action(action)
        elif switch.condition == "bias_detected":
            bias = ctx.get("meta_question_bias", False)
            if bias:
                self._log(f"Switch [{switch.id}]: bias_detected = True")
                for action in switch.then_actions:
                    self._apply_action(action)
    def _apply_action(self, action: Dict[str, Any]):
        if action["type"] == "add_role":
            role = Role(name=action["role_id"], weight=action.get("weight", 0.1))
            if not any(r.id == role.name for r in self.topology.roles):
                self.topology.roles.append(role)
                self._log(f"  Action: Added role {role.name} (weight={role.weight})")
        elif action["type"] == "set_weight":
            for role in self.topology.roles:
                if role.name == action["role_id"]:
                    role.weight = action["weight"]
                    self._log(f"  Action: Set {role.name} weight = {role.weight}")
    async def _execute_role(self, role: Role):
        runner = get_agent_runner(role.agent_type)
        if not runner:
            self._log(f"Role {role.name}: No runner for {role.agent_type}, skipping")
            return
        self._log(f"Executing {role.name} ({role.agent_type})")
        t0 = time.time()
        try:
            if isinstance(runner, type):
                instance = runner()
                if hasattr(instance, 'run'):
                    result = instance.run(self.state) if asyncio.iscoroutinefunction(instance.run) else await instance.run(self.state)
                else:
                    result = {"error": "No run method"}
            elif hasattr(runner, 'run'):
                result = runner.run(self.state) if asyncio.iscoroutinefunction(runner.run) else await runner.run(self.state)
            elif asyncio.iscoroutinefunction(runner):
                result = await runner(self.state)
            else:
                result = runner(self.state)
            elapsed = time.time() - t0
            self.results[role.name] = result
            self._log(f"  {role.name} done in {elapsed:.3f}s -> {result.get('signal', '?') if isinstance(result, dict) else 'OK'}")
        except Exception as e:
            self._log(f"  {role.name} ERROR: {e}")
            self.results[role.name] = {"error": str(e)}
    async def _transfer(self, conn: Connection):
        src = conn.from_node
        dst = conn.to_node
        if src in self.results:
            msg = Message(from_node=src, to_node=dst, payload=self.results[src], timestamp=datetime.now().isoformat())
            self.messages.append(msg)
            self._log(f"Transfer: {src} -> {dst}")
    def get_execution_log(self) -> List[str]:
        return self._execution_log
    def get_execution_summary(self) -> Dict[str, Any]:
        return {
            "topology_hash": self.topology.hash[:8],
            "roles_executed": len(self.results),
            "messages_exchanged": len(self.messages),
            "execution_log": self._execution_log,
        }


# Agent runner lookup (standalone function)
def get_agent_runner(agent_type: str):
    """Get the actual agent runner function for this agent_type."""
    import importlib
    AGENT_RUNNERS = {
        "FundamentalAgent": ("agents._impl.fundamental_agent", "run_fundamental_agent"),
        "TechnicalAgent": ("agents._impl.market_analyst", "run_market_analyst"),
        "MacroAgent": ("agents._impl.macro_agent", "run_macro_agent"),
        "QuantAgent": ("agents._impl.quant_agent", "run_quant_agent"),
        "SentimentAgent": ("agents._impl.sentiment_agent", "run_sentiment_agent"),
        "OptionsFlowAgent": ("agents._impl.options_flow_agent", "run_options_flow_agent"),
        "BullResearcher": ("agents._impl.bull_researcher", "run_bull_researcher"),
        "BearResearcher": ("agents._impl.bear_researcher", "run_bear_researcher"),
        "AstroCouncilAgent": ("agents.astro_council_agent", "run_astro_council"),
        "ElectoralAgent": ("agents._impl.electoral_agent", "run_electoral_agent"),
        "SynthesisAgent": ("agents._impl.synthesis_agent", "SynthesisAgent"),
    }
    entry = AGENT_RUNNERS.get(agent_type)
    if not entry:
        return None
    module_name, func_name = entry
    try:
        module = importlib.import_module(module_name)
        return getattr(module, func_name)
    except (ImportError, AttributeError):
        return None
