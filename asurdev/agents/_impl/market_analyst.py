"""Market Analyst Agent - Technical Analysis"""
from typing import Dict, Any
from .base_agent import BaseAgent, AgentResponse

MARKET_ANALYST_PROMPT = """Ты — MarketAnalyst, эксперт по техническому анализу.

Анализируй:
1. Тренд (выше/ниже 200 EMA)
2. Уровни поддержки/сопротивления
3. RSI (перекуплен >70 / перепродан <30)
4. Объёмы

Отвечай JSON:
{
  "signal": "BULLISH/BEARISH/NEUTRAL",
  "confidence": 0-100,
  "summary": "краткое описание"
}"""


class MarketAnalyst(BaseAgent):
    """Technical market analysis agent"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="MarketAnalyst",
            system_prompt=MARKET_ANALYST_PROMPT,
            temperature=0.2,
            **kwargs
        )
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        market_data = context.get("market_data", {})
        price = market_data.get("current_price", 0) or market_data.get("price", 0)
        change_24h = market_data.get("price_change_pct", 0) or market_data.get("change_24h", 0)
        
        if not self.llm:
            return self._rule_based_analysis(price, change_24h, market_data)
        
        prompt = f"""Проанализируй {context.get('symbol', 'UNKNOWN')}:
Цена: ${price:,.2f}
Изменение 24ч: {change_24h:+.2f}%
Ответь JSON."""
        return await self.think(prompt)
    
    def _rule_based_analysis(self, price: float, change_24h: float, data: Dict) -> AgentResponse:
        if change_24h > 3:
            signal = "BULLISH"
            confidence = min(80, 50 + change_24h * 5)
        elif change_24h < -3:
            signal = "BEARISH"
            confidence = min(80, 50 + abs(change_24h) * 5)
        else:
            signal = "NEUTRAL"
            confidence = 50
        
        return AgentResponse(
            agent_name="MarketAnalyst",
            signal=signal,
            confidence=confidence,
            summary=f"Цена {price:,.2f}, изменение {change_24h:+.2f}%",
            details={"price": price, "change_24h": change_24h, "mode": "rule_based"}
        )
