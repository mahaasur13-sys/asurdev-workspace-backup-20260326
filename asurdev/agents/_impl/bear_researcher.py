"""Bear Researcher - Finds bearish arguments"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentResponse

BEAR_PROMPT = """Ты — BearResearcher, находишь ВСЕ медвежьи аргументы.
Ответь JSON:
{
  "signal": "BEARISH",
  "confidence": 0-100,
  "summary": "медвежий кейс",
  "bear_points": ["пункт1"]
}"""


class BearResearcher(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="BearResearcher", system_prompt=BEAR_PROMPT, temperature=0.4, **kwargs)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        if not self.llm:
            return AgentResponse(
                agent_name="BearResearcher",
                signal="BEARISH",
                confidence=50,
                summary=f"Bear case for {context.get('symbol', 'UNKNOWN')}",
                details={"mode": "rule_based"}
            )
        return await self.think(f"Найди медвежьи аргументы для {context.get('symbol')}")
