"""mas_factory/engine.py - ATOM-R-028: Dynamic Topology Executor with SwitchNodes
Integrates TopologyUpdater for dynamic graph adaptation during execution.
"""
import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

from mas_factory.topology import (
    Topology, Role, Connection, SwitchNode, Message,
    TopologyUpdater, TopologyChange, SwitchAction,
    UncertaintySwitch, BiasSwitch, RegimeSwitch, OOSFailSwitch, LowConfidenceSwitch,
    ConditionEvaluator
)
from mas_factory.registry import get_registry

# ─── Meta-Questioning Integration ────────────────────────────────────────────
class MetaQuestioningIntegrator:
    """ATOM-R-028: Integrates MetaQuestioning with topology changes."""
    
    def __init__(self):
        self.questions: List[str] = []
        self.biases: List[str] = []
        self.topology_modifications: List[Dict] = []
    
    def generate_questions(self, context: Dict[str, Any]) -> List[str]:
        """Generate self-questioning questions based on context."""
        self.questions = []
        
        confidence = context.get("confidence", context.get("confidence_final", 50))
        uncertainty = context.get("uncertainty_total", 0.5)
        oos_fail = context.get("oos_fail_rate", 0.0)
        
        if confidence > 75:
            self.questions.append("Is this high-confidence decision justified by evidence?")
        if uncertainty > 0.6:
            self.questions.append("Should we add grounding before proceeding?")
        if oos_fail > 0.4:
            self.questions.append("Are we in an overfitting regime? Tighten policy?")
        
        return self.questions
    
    def analyze_bias(self, signals: List[Dict]) -> bool:
        """Detect if agents show correlated bias."""
        if len(signals) < 2:
            return False
        signal_counts = {}
        for s in signals:
            sig = s.get("signal", "NEUTRAL")
            signal_counts[sig] = signal_counts.get(sig, 0) + 1
        # Bias if >70% agents agree
        total = len(signals)
        for count in signal_counts.values():
            if count / total > 0.7:
                self.biases.append(f"High agreement: {count}/{total} agents")
                return True
        return False
    
    def get_topology_modifications(self, context: Dict[str, Any]) -> List[Dict]:
        """Return recommended topology changes based on analysis."""
        mods = []
        
        unc = context.get("uncertainty_total", 0)
        if unc > 0.6:
            mods.append({
                "action": SwitchAction.ADD_LOOP.value,
                "target": "GroundingLoop",
                "reason": f"Uncertainty {unc:.3f} > 0.6"
            })
        
        bias = context.get("bias_detected", False)
        if bias:
            mods.append({
                "action": SwitchAction.ADD_ROLE.value,
                "target": "Critic",
                "reason": "Bias detected in agent signals"
            })
        
        oos = context.get("oos_fail_rate", 0)
        if oos > 0.4:
            mods.append({
                "action": SwitchAction.TIGHTEN_POLICY.value,
                "target": "all",
                "reason": f"OOS fail {oos:.3f} > 0.4",
                "factor": 0.5
            })
        
        regime = context.get("regime", "NORMAL")
        if regime in ["HIGH", "EXTREME"]:
            mods.append({
                "action": SwitchAction.REORDER_ROLES.value,
                "target": "priority",
                "reason": f"Regime {regime} - prioritizing stability",
                "order": ["HighVolatilityAgent", "RiskManager", "FundamentalAgent"]
            })
        
        return mods

# ─── OAP Integration ─────────────────────────────────────────────────────────
class OAPIntegrator:
    """ATOM-R-028: Integrates OAP recommendations with topology changes."""
    
    def __init__(self):
        self.current_ttc_depth = 3
        self.oos_fail_rate = 0.0
        self.entropy_avg = 0.5
    
    def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze OAP metrics and suggest topology changes."""
        suggestions = []
        
        # Extract metrics from context
        self.current_ttc_depth = context.get("current_ttc_depth", 3)
        self.oos_fail_rate = context.get("oos_fail_rate", 0.0)
        self.entropy_avg = context.get("entropy_avg", 0.5)
        
        # High OOS fail → tighten
        if self.oos_fail_rate > 0.4:
            suggestions.append({
                "action": SwitchAction.TIGHTEN_POLICY.value,
                "target": "all",
                "reason": f"OOS fail {self.oos_fail_rate:.3f} exceeds threshold",
                "factor": 0.5
            })
        
        # High entropy → reduce complexity
        if self.entropy_avg > 0.7:
            suggestions.append({
                "action": SwitchAction.TIGHTEN_POLICY.value,
                "target": "all",
                "reason": f"High entropy {self.entropy_avg:.3f} - reducing exploration",
                "factor": 0.7
            })
        
        return {
            "suggestions": suggestions,
            "metrics": {
                "oos_fail_rate": self.oos_fail_rate,
                "entropy_avg": self.entropy_avg,
                "ttc_depth": self.current_ttc_depth
            }
        }
    
    def suggest_topology_change(self, context: Dict[str, Any]) -> Optional[TopologyChange]:
        """OAPOptimizer.suggest_topology_change() - main entry point."""
        analysis = self.analyze(context)
        
        if not analysis["suggestions"]:
            return None
        
        suggestion = analysis["suggestions"][0]
        action = SwitchAction(suggestion["action"])
        
        return TopologyChange.create(
            action=action,
            target=suggestion.get("target", "unknown"),
            before={"roles": [{"n": r.name, "w": r.weight} for r in context.get("_roles", [])]},
            after=suggestion,
            reason=suggestion.get("reason", "OAP recommendation"),
            triggered_by="OAPIntegrator"
        )

# ─── Dynamic Topology Executor ─────────────────────────────────────────────────
class TopologyExecutor:
    """ATOM-R-028: Executes topology with dynamic SwitchNode evaluation.
    
    After each step, evaluates switch conditions and applies topology changes
    through TopologyUpdater. Full versioning and rollback support.
    """
    
    def __init__(self, topology: Topology):
        self.topology = topology
        self.updater = TopologyUpdater(topology)
        self.meta_integrator = MetaQuestioningIntegrator()
        self.oap_integrator = OAPIntegrator()
        self.execution_log: List[Dict] = []
        self.change_count = 0
    
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Async execution with dynamic topology updates."""
        self.execution_log = []
        self.change_count = 0
        
        # Step 1: Meta-Questioning
        questions = self.meta_integrator.generate_questions(context)
        context["_meta_questions"] = questions
        
        if self.meta_integrator.analyze_bias(context.get("signals", [])):
            context["bias_detected"] = True
            self._log_step("bias_detection", {"detected": True, "biases": self.meta_integrator.biases})
        
        # Step 2: OAP Analysis
        oap_analysis = self.oap_integrator.analyze(context)
        context.update(oap_analysis["metrics"])
        
        # Step 3: Evaluate SwitchNodes and apply changes
        for switch in self.topology.switch_nodes:
            if switch.action and switch.condition:
                if ConditionEvaluator.evaluate(switch.condition, context):
                    change = self._create_change_from_switch(switch, context)
                    if change:
                        self.topology = self.updater.apply_change(change)
                        self.change_count += 1
                        self._log_step("switch_applied", {
                            "switch_id": switch.id,
                            "condition": switch.condition,
                            "action": switch.action.value,
                            "new_topology_hash": self.topology.hash
                        })
        
        # Step 4: Apply Meta-Questioning modifications
        mods = self.meta_integrator.get_topology_modifications(context)
        for mod in mods:
            change = TopologyChange.create(
                action=SwitchAction(mod["action"]),
                target=mod["target"],
                before={"roles": [r.name for r in self.topology.roles]},
                after=mod,
                reason=mod.get("reason", "Meta-Questioning"),
                triggered_by="MetaQuestioning"
            )
            self.topology = self.updater.apply_change(change)
            self.change_count += 1
            self._log_step("meta_modification", mod)
        
        # Step 5: Execute topology (simplified)
        results = await self._execute_topology(context)
        
        return {
            "results": results,
            "topology_hash": self.topology.hash,
            "changes_applied": self.change_count,
            "execution_log": self.execution_log,
            "change_summary": self.updater.get_change_summary()
        }
    
    def _create_change_from_switch(self, switch: SwitchNode, context: Dict) -> Optional[TopologyChange]:
        """Create TopologyChange from SwitchNode evaluation."""
        action = switch.action or SwitchAction.ADD_LOOP
        target = switch.true_branch[0] if switch.true_branch else "unknown"
        
        return TopologyChange.create(
            action=action,
            target=target,
            before={"roles": [{"n": r.name, "w": r.weight} for r in self.topology.roles]},
            after={"added_branch": target, "metadata": switch.metadata},
            reason=f"Switch {switch.id}: {switch.condition} = True",
            triggered_by=switch.id
        )
    
    async def _execute_topology(self, context: Dict) -> Dict:
        """Execute the (possibly modified) topology."""
        results = {}
        registry = get_registry()
        
        for role in self.topology.roles:
            agent = registry.get_agent(role.agent_type)
            if agent:
                try:
                    if asyncio.iscoroutinefunction(agent.run):
                        result = await agent.run(context)
                    else:
                        result = agent.run(context)
                    results[role.name] = result
                except Exception as e:
                    results[role.name] = {"error": str(e)}
        
        return results
    
    def _log_step(self, event: str, data: Dict):
        """Log execution step."""
        self.execution_log.append({
            "event": event,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })
    
    def get_change_history(self) -> List[Dict]:
        """Return full change history."""
        return [
            {
                "change_id": c.change_id,
                "timestamp": c.timestamp,
                "action": c.action.value,
                "reason": c.reason,
                "triggered_by": c.triggered_by
            }
            for c in self.updater.change_history
        ]


    def run_sync(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for testing."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.run(context))
