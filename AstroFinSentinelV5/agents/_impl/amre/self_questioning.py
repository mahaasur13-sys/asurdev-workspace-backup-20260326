"""amre/self_questioning.py — ATOM-KARL Self-Questioning Engine"""
from dataclasses import dataclass

@dataclass
class SQResult:
    passed: bool
    questions_raised: int
    challenges: list
    final_verdict: str
    confidence_adjustment: int

class SelfQuestioningEngine:
    def __init__(self, min_questions: int = 3):
        self.min_questions = min_questions

    def evaluate(self, trajectory, grounding_result=None) -> SQResult:
        challenges = []
        confidence_adj = 0

        # Challenge 1: single source
        if len(trajectory.metadata.get("sources", [])) < 2:
            challenges.append("single_source_dependency")
            confidence_adj -= 3

        # Challenge 2: uncertainty mismatch
        unc = trajectory.metadata.get("uncertainty", {})
        disagreement = unc.get("disagreement", 0)
        if disagreement > 0.4:
            challenges.append(f"high_disagreement_{disagreement:.2f}")
            confidence_adj -= 5

        # Challenge 3: trajectory stability
        if trajectory.metrics and trajectory.metrics.trade_count < 3:
            challenges.append("insufficient_trade_history")
            confidence_adj -= 2

        # Challenge 4: contradictory signals
        agents = trajectory.metadata.get("agents", [])
        dirs = [a.get("signal") for a in agents]
        if dirs and len(set(dirs)) > 2:
            challenges.append("contradictory_agent_signals")
            confidence_adj -= 4

        passed = len(challenges) == 0 or all(
            "high_disagreement" not in c for c in challenges
        )
        verdict = "ACCEPT" if passed else "REVIEW"
        if confidence_adj < -10:
            verdict = "REJECT"

        return SQResult(
            passed=passed,
            questions_raised=len(challenges),
            challenges=challenges,
            final_verdict=verdict,
            confidence_adjustment=confidence_adj,
        )
