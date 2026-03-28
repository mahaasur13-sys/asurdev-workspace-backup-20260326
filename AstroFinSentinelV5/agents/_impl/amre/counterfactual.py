"""amre/counterfactual.py — ATOM-KARL-006 Counterfactual Testing Engine"""
from dataclasses import dataclass
from typing import Optional
import random

@dataclass
class CounterfactualResult:
    passed: bool
    original_sharpe: float
    perturbed_sharpe: float
    delta: float
    penalty: float
    verdict: str

class CounterfactualEngine:
    def __init__(self, epsilon: float = 0.05, penalty_strength: float = 1.5):
        self.epsilon = epsilon
        self.penalty_strength = penalty_strength

    def _perturb_astro(self, trajectory) -> dict:
        """Modify astro component of trajectory to test robustness."""
        m = trajectory.metadata or {}
        # Perturb astro signals
        perturbed = dict(m)
        if "astro_score" in perturbed:
            noise = random.uniform(-0.1, 0.1)
            perturbed["astro_score"] = perturbed["astro_score"] + noise
        if "astro_weight" in perturbed:
            perturbed["astro_weight"] = max(0, perturbed["astro_weight"] - 0.05)
        return perturbed

    def _evaluate(self, trajectory, perturbed_astro: dict) -> float:
        """Evaluate trajectory with perturbed astro signals."""
        if trajectory.metrics is None:
            return 0.0
        original_sharpe = trajectory.metrics.sharpe
        # If astro_weight was reduced, recalculate sharpe impact
        astro_weight = perturbed_astro.get("astro_weight", trajectory.metadata.get("astro_weight", 0.3))
        # Simplified: sharpe decreases proportionally to astro_weight reduction
        sharpe_reduction = (trajectory.metadata.get("astro_weight", 0.3) - astro_weight) * original_sharpe * 0.5
        return max(original_sharpe - sharpe_reduction, 0.0)

    def evaluate(self, trajectory) -> CounterfactualResult:
        """Run counterfactual test: does signal depend on astro?"""
        if trajectory.metrics is None:
            return CounterfactualResult(
                passed=False, original_sharpe=0, perturbed_sharpe=0,
                delta=0, penalty=0, verdict="NO_DATA"
            )
        original_sharpe = trajectory.metrics.sharpe
        perturbed = self._perturb_astro(trajectory)
        perturbed_sharpe = self._evaluate(trajectory, perturbed)
        delta = abs(original_sharpe - perturbed_sharpe)
        passed = delta >= self.epsilon
        penalty = 0 if passed else self.penalty_strength
        verdict = "ACCEPT" if passed else "REJECT"
        return CounterfactualResult(
            passed=passed,
            original_sharpe=round(original_sharpe, 4),
            perturbed_sharpe=round(perturbed_sharpe, 4),
            delta=round(delta, 4),
            penalty=penalty,
            verdict=verdict,
        )
