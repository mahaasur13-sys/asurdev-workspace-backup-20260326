"""amre/uncertainty.py — ATOM-KARL Uncertainty (disagreement + epistemic via Q-variance)"""
from dataclasses import dataclass
import numpy as np

@dataclass
class DisagreementUncertainty:
    value: float
    sources: list

@dataclass
class EpisodicUncertainty:
    value: float
    q_variance: float

class UncertaintyEngine:
    def __init__(self):
        self.history = []

    def compute(self, signals: list) -> EpisodicUncertainty:
        if not signals:
            return EpisodicUncertainty(value=0.5, q_variance=0.5)
        dirs = [s.get("signal", "NEUTRAL") for s in signals]
        unique_dirs = set(dirs)
        disagreement = 1 - (len(unique_dirs) - 1) / 2.0 if len(unique_dirs) <= 3 else 1.0
        qs = [s.get("confidence", 50) / 100.0 for s in signals]
        q_variance = float(np.std(qs)) if len(qs) > 1 else 0.5
        value = 0.5 * disagreement + 0.5 * q_variance
        return EpisodicUncertainty(value=round(value, 4), q_variance=round(q_variance, 4))

def compute_uncertainty(signals: list) -> EpisodicUncertainty:
    engine = UncertaintyEngine()
    return engine.compute(signals)
