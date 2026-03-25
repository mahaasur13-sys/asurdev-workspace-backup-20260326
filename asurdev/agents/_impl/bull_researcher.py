"""Bull Researcher - Finds bullish arguments"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentResponse

BULL_PROMPT = """Ты — BullResearcher, находишь ВСЕ бычьи аргументы.
Ответь JSON:
{
  "signal": "BULLISH",
  "confidence": 0-100,
  "summary": "бычий кейс",
  "bull_points": ["пункт1"]
}"""


class BullResearcher(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="BullResearcher", system_prompt=BULL_PROMPT, temperature=0.4, **kwargs)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        if not self.llm:
            return AgentResponse(
                agent_name="BullResearcher",
                signal="BULLISH",
                confidence=50,
                summary=f"Bull case for {context.get('symbol', 'UNKNOWN')}",
                details={"mode": "rule_based"}
            )
        return await self.think(f"Найди бычьи аргументы для {context.get('symbol')}")
