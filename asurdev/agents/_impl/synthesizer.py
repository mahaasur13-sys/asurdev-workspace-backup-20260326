"""Synthesizer Agent - Final C.L.E.A.R. verdict"""
from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResponse

SYNTHESIZER_PROMPT = """Объедини сигналы в C.L.E.A.R. рекомендацию.
Ответь JSON:
{
  "signal": "BULLISH/BEARISH/NEUTRAL",
  "confidence": 0-100,
  "summary": "1-2 предложения",
  "details": {"context": "", "logic": "", "evidence": {}, "assessment": {}, "recommendation": ""}
}"""


class Synthesizer(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Synthesizer", system_prompt=SYNTHESIZER_PROMPT, temperature=0.2, **kwargs)
    
    async def synthesize(
        self,
        market: AgentResponse,
        bull: AgentResponse,
        bear: AgentResponse,
        astro: AgentResponse,
        cycle: Optional[AgentResponse] = None
    ) -> AgentResponse:
        if self.llm:
            prompt = f"""Market: {market.signal} ({market.confidence}%)
Bull: {bull.signal} ({bull.confidence}%)
Bear: {bear.signal} ({bear.confidence}%)
Astro: {astro.signal} ({astro.confidence}%)
{f'Cycle: {cycle.signal} ({cycle.confidence}%)' if cycle else ''}
Ответь JSON."""
            return await self.think(prompt)
        return self._rule_synthesize(market, bull, bear, astro, cycle)
    
    def _rule_synthesize(self, market, bull, bear, astro, cycle) -> AgentResponse:
        signals = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
        for resp in [market, bull, bear, astro, cycle]:
            if resp and resp.signal in signals:
                signals[resp.signal] += resp.confidence
        
        if signals["BULLISH"] > signals["BEARISH"]:
            final = "BULLISH"
        elif signals["BEARISH"] > signals["BULLISH"]:
            final = "BEARISH"
        else:
            final = "NEUTRAL"
        
        return AgentResponse(
            agent_name="Synthesizer",
            signal=final,
            confidence=min(85, 50 + signals[final] / 10),
            summary=f"C.L.E.A.R. {final} | Bull:{signals['BULLISH']} Bear:{signals['BEARISH']}",
            details={"signals": signals}
        )
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        return AgentResponse(
            agent_name="Synthesizer",
            signal="NEUTRAL",
            confidence=50,
            summary="Use synthesize() method"
        )
