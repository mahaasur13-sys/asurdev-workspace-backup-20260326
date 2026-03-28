"""amre/self_question.py — Self-Questioning Engine + Meta-Questioning (ATOM-016)
Self-questioning: agent asks itself hard questions before committing to a decision.
Meta-questioning: agent reflects on whether its own questions are good enough.
"""
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
from datetime import datetime

# ─── Question Outcome Tracking ──────────────────────────────────────────────────

@dataclass
class QuestionOutcome:
    """Tracks whether a question's answer correctly predicted outcome."""
    question: str
    predicted_answer: str
    actual_outcome: str  # "correct" | "incorrect"
    was_hard: bool  # confidence was near threshold
    timestamp: str


@dataclass
class SQResult:
    """Result of self-questioning pass."""
    question: str
    answer: Optional[str]
    passed: bool
    confidence_adjustment: int
    meta_question: Optional[str] = None  # ATOM-016: meta-level reflection
    meta_confidence: Optional[int] = None  # How confident we are in our own questions


class SelfQuestioningEngine:
    """
    Self-questioning engine for preventing overconfident decisions.
    
    Keeps evolving question bank that adapts based on past outcomes.
    Each question tracks its historical accuracy — bad questions get weighted down.
    """

    # ── Dynamic question bank ───────────────────────────────────────────────

    CORE_QUESTIONS = [
        "Is this decision consistent with previous high-conf signals?",
        "Am I acting on new information or reinforcing my bias?",
        "Is my confidence justified by the evidence?",
        "Could I be wrong, and how would I know?",
        "Is the regime stable enough to act on this signal?",
        "Do all agent categories agree, or am I cherry-picking?",
        "Is my position size appropriate for this uncertainty?",
    ]

    META_QUESTIONS = [
        "Are my questions good enough to catch my mistakes?",
        "Do I keep asking the same question in different words?",
        "Am I using questions to justify rather than to doubt?",
    ]

    def __init__(self):
        self.questions = list(self.CORE_QUESTIONS)
        self.meta_questions = list(self.META_QUESTIONS)
        self.question_history: List[QuestionOutcome] = []
        self.question_scores: Dict[str, float] = {q: 1.0 for q in self.CORE_QUESTIONS}
        self.total_asked = 0

    def ask(
        self, signals: List[Any], state: Any = None
    ) -> SQResult:
        """
        Ask the most relevant question based on current context.
        Returns SQResult with self-question + meta-question (ATOM-016).
        """
        # Select question with highest expected value (accuracy-weighted)
        q = self._select_question(signals, state)
        
        # Answer the question
        answer, adjustment = self._answer(q, signals, state)
        
        # Meta-question: is this whole process trustworthy?
        meta_q, meta_adjustment = self._meta_question(signals, state)
        
        passed = adjustment >= -10  # Not too harshly penalized
        
        return SQResult(
            question=q,
            answer=answer,
            passed=passed,
            confidence_adjustment=adjustment,
            meta_question=meta_q,
            meta_confidence=meta_adjustment,
        )

    def _select_question(self, signals: List[Any], state: Any) -> str:
        """Select the question with best historical accuracy."""
        if not self.question_history:
            return self.questions[self.total_asked % len(self.questions)]
        
        # Add small random factor to avoid getting stuck
        import random
        candidates = sorted(
            self.questions,
            key=lambda q: self.question_scores.get(q, 1.0) + random.uniform(-0.1, 0.1),
            reverse=True,
        )
        return candidates[0]

    def _answer(
        self, question: str, signals: List[Any], state: Any
    ) -> tuple:
        """Answer the selected question."""
        # Extract signal/dict attributes safely
        def _get(s, key, default=None):
            if hasattr(s, key):
                return getattr(s, key)
            if isinstance(s, dict):
                return s.get(key, default)
            return default

        high_conf = [s for s in signals if _get(s, "confidence", 50) > 75]
        low_agr = len(set(_get(s, "signal", "") for s in signals)) > 3
        
        q_lower = question.lower()
        
        if "consistent" in q_lower:
            if len(high_conf) > 3:
                return "Multiple high-conf signals agree", 0
            return "No strong prior consensus", -5
        
        if "new information" in q_lower or "bias" in q_lower:
            if low_agr:
                return "Low agreement — possible bias reinforcement", -10
            return "Appears to be genuine new signal", 0
        
        if "justified" in q_lower:
            if len(high_conf) > 2 and len(signals) >= 5:
                return "Evidence is substantial", 0
            return "Weak evidence for high confidence", -5
        
        if "wrong" in q_lower:
            return "Always possible — using uncertainty weighting", 0
        
        if "regime" in q_lower:
            regime = _get(state, "regime", "NORMAL") if state else "NORMAL"
            if regime in ("HIGH", "EXTREME"):
                return f"Regime {regime} — reducing confidence", -10
            return "Regime is stable", 0
        
        if "agree" in q_lower or "cherry" in q_lower:
            if low_agr:
                return "Category disagreement — cherry-picking risk", -15
            return "Good cross-category agreement", 0
        
        if "position size" in q_lower:
            return "Position sizing accounts for uncertainty", 0
        
        return "Question processed", 0

    def _meta_question(
        self, signals: List[Any], state: Any
    ) -> tuple:
        """
        ATOM-016: Meta-questioning — reflect on whether our questions are trustworthy.
        Returns (meta_question, meta_confidence: int).
        """
        recent = self.question_history[-10:] if self.question_history else []
        
        if not recent:
            return "No history yet — treating questions as untested", 50
        
        recent_accuracy = sum(
            1 for o in recent if o.actual_outcome == "correct"
        ) / len(recent)
        
        # Score the question bank based on recent accuracy
        avg_score = sum(self.question_scores.values()) / max(len(self.question_scores), 1)
        
        if recent_accuracy < 0.4 or avg_score < 0.5:
            return (
                "WARNING: Questions have poor track record recently — apply extra skepticism",
                -20,
            )
        elif recent_accuracy > 0.7 and avg_score > 0.8:
            return (
                "Questions performing well — maintain current approach",
                0,
            )
        else:
            return (
                "Moderate question quality — stay alert for edge cases",
                -5,
            )

    def record_outcome(
        self, question: str, predicted_answer: str, was_correct: bool, was_hard: bool = False
    ):
        """Record whether the question/answer pair was useful."""
        outcome = QuestionOutcome(
            question=question,
            predicted_answer=predicted_answer,
            actual_outcome="correct" if was_correct else "incorrect",
            was_hard=was_hard,
            timestamp=datetime.now().isoformat(),
        )
        self.question_history.append(outcome)
        
        # Update question score (exponential moving average)
        current = self.question_scores.get(question, 1.0)
        delta = 0.1 if was_correct else -0.15
        self.question_scores[question] = max(0.1, min(1.5, current + delta))
        
        # Evict consistently bad questions
        bad = [q for q, s in self.question_scores.items() if s < 0.3]
        for q in bad:
            if q in self.questions:
                self.questions.remove(q)

    def improve_questions(self) -> Dict[str, Any]:
        """
        ATOM-016: Meta-improvement — analyze question bank and propose improvements.
        Called periodically or on demand.
        """
        if len(self.question_history) < 10:
            return {"status": "insufficient_data", "n_history": len(self.question_history)}
        
        recent = self.question_history[-20:]
        accuracy_by_q: Dict[str, List[str]] = {}
        for o in recent:
            if o.question not in accuracy_by_q:
                accuracy_by_q[o.question] = []
            accuracy_by_q[o.question].append(o.actual_outcome)
        
        question_performance = {}
        for q, outcomes in accuracy_by_q.items():
            acc = outcomes.count("correct") / len(outcomes)
            question_performance[q] = {
                "accuracy": round(acc, 3),
                "n": len(outcomes),
                "score": self.question_scores.get(q, 1.0),
            }
        
        worst = sorted(question_performance.items(), key=lambda x: x[1]["accuracy"])[:2]
        best = sorted(question_performance.items(), key=lambda x: x[1]["accuracy"], reverse=True)[:2]
        
        return {
            "status": "analyzed",
            "n_history": len(self.question_history),
            "avg_question_score": round(sum(self.question_scores.values()) / max(len(self.question_scores), 1), 3),
            "worst_questions": [
                {"question": q, **stats} for q, stats in worst
            ],
            "best_questions": [
                {"question": q, **stats} for q, stats in best
            ],
            "questions_to_evict": [q for q, s in self.question_scores.items() if s < 0.3],
            "recommended_new_questions": self._propose_new_questions(question_performance),
        }

    def _propose_new_questions(
        self, performance: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """Propose new questions based on weaknesses in the current question bank."""
        proposals = []
        
        low_acc = [q for q, s in performance.items() if s["accuracy"] < 0.5]
        if low_acc:
            proposals.append("Am I confusing correlation with causation here?")
        
        hard_cases = [o for o in self.question_history if o.was_hard and o.actual_outcome == "incorrect"]
        if len(hard_cases) > 3:
            proposals.append("Is this a repeat of a previously failed pattern?")
        
        if len(self.questions) < 5:
            proposals.append("Is my uncertainty estimate realistic given the data quality?")
            proposals.append("Should I wait for more data before acting?")
        
        return proposals[:3]