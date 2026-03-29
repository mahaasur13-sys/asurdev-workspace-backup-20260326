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
        agent = self.registry.get_role(role.agent_type)
        if not agent:
            self._log(f"Role {role.name}: No agent found, skipping")
            return
        self._log(f"Executing {role.name} (weight={role.weight})")
        t0 = time.time()
        try:
            result = await agent(self.state)
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
