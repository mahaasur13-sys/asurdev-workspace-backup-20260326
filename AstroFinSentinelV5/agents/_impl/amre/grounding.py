"""amre/grounding.py — Domain grounding validation"""
from typing import List, Any, Dict

def validate_with_grounding(state: Any, signals: List[Any]) -> Dict[str, Any]:
    if not signals:
        return {"passed": True, "confidence_adjustment": 0, "issues": []}
    issues = []
    for s in signals:
        sig = s.get("signal", "") if isinstance(s, dict) else getattr(s, "signal", "")
        conf = s.get("confidence", 50) if isinstance(s, dict) else getattr(s, "confidence", 50)
        if conf > 85 and sig in ("NEUTRAL", "neutral"):
            issues.append(f"High confidence ({conf}) but NEUTRAL signal")
        if conf < 25 and sig not in ("NEUTRAL", "neutral", "AVOID"):
            issues.append(f"Low confidence ({conf}) but directional signal: {sig}")
    failed_count = sum(1 for i in issues if "but" in i and "signal" in i)
    adjustment = -failed_count * 5 if failed_count > 0 else 0
    return {"passed": len(issues) < 2, "confidence_adjustment": adjustment, "issues": issues[:3]}
