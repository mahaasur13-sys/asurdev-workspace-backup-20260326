"""Gann Agent - Gann Square of 9 and Levels"""
import math
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse


class GannSquareOf9:
    @staticmethod
    def get_levels(price: float) -> Dict[str, Any]:
        levels = {"support": [], "resistance": []}
        for pct in [1, 2, 3, 5]:
            levels["support"].append(round(price * (1 - pct/100), 2))
            levels["resistance"].append(round(price * (1 + pct/100), 2))
        return levels
    
    @staticmethod
    def get_square_levels(price: float) -> List[float]:
        base = int(math.sqrt(price))
        return sorted(set([(base + i) ** 2 for i in range(-4, 5)]))


class GannAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Gann", system_prompt="Методы Ганна", temperature=0.2, **kwargs)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        market_data = context.get("market_data", {})
        price = float(market_data.get("current_price", market_data.get("price", 50000)))
        
        levels = GannSquareOf9.get_levels(price)
        nearest_sup = max([l for l in levels["support"] if l < price], default=price * 0.98)
        nearest_res = min([l for l in levels["resistance"] if l > price], default=price * 1.02)
        
        mid = (nearest_sup + nearest_res) / 2
        if price > mid * 1.01:
            signal, conf = "BULLISH", 60
        elif price < mid * 0.99:
            signal, conf = "BEARISH", 60
        else:
            signal, conf = "NEUTRAL", 50
        
        return AgentResponse(
            agent_name="Gann",
            signal=signal,
            confidence=conf,
            summary=f"Gann: {signal} | Sup: ${nearest_sup:,.2f} | Res: ${nearest_res:,.2f}",
            details={"price": price, "support": nearest_sup, "resistance": nearest_res}
        )
