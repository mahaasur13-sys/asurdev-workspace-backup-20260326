"""amre/uncertainty.py — Uncertainty quantification"""
from typing import List, Any, Dict

def estimate_uncertainty(signals: List[Any]) -> Dict[str, float]:
    if not signals:
        return {"aleatoric": 0.5, "epistemic": 0.5, "total": 0.5, "n_signals": 0}
    confidences = [s.get("confidence", 50) if isinstance(s, dict) else getattr(s, "confidence", 50) for s in signals]
    avg_conf = sum(confidences) / len(confidences)
    variance = sum((c - avg_conf) ** 2 for c in confidences) / len(confidences) if len(confidences) > 1 else 0
    signal_ents = [s.get("signal", "") for s in signals]
    unique_signals = len(set(signal_ents))
    aleatoric = max(0, 1 - avg_conf / 100)
    epistemic = min(1, variance / 1000 + (1 - unique_signals / max(len(signals), 1)) * 0.3)
    return {"aleatoric": round(aleatoric, 4), "epistemic": round(epistemic, 4), "total": round((aleatoric + epistemic) / 2, 4), "n_signals": len(signals)}
