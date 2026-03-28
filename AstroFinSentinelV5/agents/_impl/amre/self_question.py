"""amre/self_question.py — Self-Questioning Engine"""
from dataclasses import dataclass
from typing import List, Any, Optional

@dataclass
class SQResult:
    question: str
    answer: Optional[str]
    passed: bool
    confidence_adjustment: int

class SelfQuestioningEngine:
    def __init__(self):
        self.questions = [
            "Is this decision consistent with previous high-confidence signals?",
            "Am I acting on new information or reinforcing my bias?",
            "Is my confidence justified by the evidence?",
            "Could I be wrong, and how would I know?",
        ]
    def ask(self, signals: List[Any], state: Any = None) -> SQResult:
        high_conf = [s for s in signals if (s.get("confidence", 50) if isinstance(s, dict) else getattr(s, "confidence", 50)) > 75]
        if len(high_conf) > 3:
            return SQResult(question=self.questions[0], answer="Multiple high-confidence signals detected", passed=True, confidence_adjustment=0)
        low_agr = len(set(s.get("signal", "") for s in signals if isinstance(s, dict))) > 3
        if low_agr:
            return SQResult(question=self.questions[1], answer="Low agreement among agents", passed=True, confidence_adjustment=-5)
        return SQResult(question=self.questions[2], answer="Confidence appears justified", passed=True, confidence_adjustment=0)
