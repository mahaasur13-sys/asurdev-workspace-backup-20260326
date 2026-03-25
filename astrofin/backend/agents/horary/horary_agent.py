"""
HoraryAgent — Horary Astrology.
Хорарная астрология (ответы на конкретные вопросы).
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class HoraryAgent(BaseAgent):
    """HoraryAgent — хорарная астрология. Вес: 0.08"""
    QUESTION_SIGNIFICATORS = {
        "money": ["Sun", "Jupiter", "Venus", "2nd"],
        "love": ["Venus", "Mars", "5th", "7th"],
        "career": ["Sun", "Saturn", "10th", "MC"],
        "health": ["Sun", "Mars", "6th", "Asc"],
    }

    def __init__(self):
        super().__init__(
            name="HoraryAgent",
            system_prompt="Horary Astrology — answering specific questions"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        question = context.get("question", context.get("user_query", ""))
        
        try:
            eph = swiss_ephemeris(
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                time=datetime.utcnow().strftime("%H:%M:%S"),
                compute_panchanga=False
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning=f"Horary error: {e}", sources=["horary_astrology.md"],
            )

        category = self._classify_question(question)
        significators = self.QUESTION_SIGNIFICATORS.get(category, [])
        
        return AgentResponse(
            agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.5,
            reasoning=f"Horary for '{question}' — category: {category}",
            sources=["horary_astrology.md"],
            metadata={"question": question, "category": category, "significators": significators},
        )

    def _classify_question(self, question: str) -> str:
        q = question.lower()
        if any(w in q for w in ["money", "financial", "bank"]):
            return "money"
        elif any(w in q for w in ["love", "relationship", "marriage"]):
            return "love"
        elif any(w in q for w in ["career", "job", "work"]):
            return "career"
        elif any(w in q for w in ["health", "medical"]):
            return "health"
        return "general"
