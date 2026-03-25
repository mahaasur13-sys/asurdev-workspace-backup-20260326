"""Dow Theory Agent - Trend Confirmation"""
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentResponse


class DowTheoryAnalyzer:
    @staticmethod
    def analyze(prices: List[float]) -> Dict[str, Any]:
        if len(prices) < 20:
            return {"trend": "sideways", "strength": 0, "confirmed": False}
        
        highs, lows = [], []
        for i in range(2, len(prices) - 2):
            if prices[i] > prices[i-1] and prices[i] > prices[i+1] and prices[i] > prices[i-2] and prices[i] > prices[i+2]:
                highs.append(prices[i])
            if prices[i] < prices[i-1] and prices[i] < prices[i+1] and prices[i] < prices[i-2] and prices[i] < prices[i+2]:
                lows.append(prices[i])
        
        if len(highs) < 2 or len(lows) < 2:
            return {"trend": "sideways", "strength": 3, "confirmed": False}
        
        recent_h = highs[-1] if highs else 0
        recent_l = lows[-1] if lows else 0
        
        if len(highs) > 1 and highs[-1] > highs[-2] and lows[-1] > lows[-2]:
            return {"trend": "uptrend", "strength": min(10, 6 + len(highs)), "confirmed": len(highs) >= 3}
        elif len(highs) > 1 and highs[-1] < highs[-2] and lows[-1] < lows[-2]:
            return {"trend": "downtrend", "strength": min(10, 6 + len(lows)), "confirmed": len(lows) >= 3}
        
        return {"trend": "sideways", "strength": 4, "confirmed": False}


class DowTheoryAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="DowTheory", system_prompt="Теория Доу", temperature=0.2, **kwargs)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        prices_data = context.get("prices", [])
        if not prices_data:
            base = context.get("market_data", {}).get("current_price", 50000)
            prices_data = [base * (1 + (i % 7 - 3) * 0.015) for i in range(30)]
        
        prices = [float(p) if not isinstance(p, dict) else float(p.get('close', p.get('c', 50000))) 
                  for p in prices_data[-30:]]
        
        result = DowTheoryAnalyzer.analyze(prices)
        signal_map = {"uptrend": "BULLISH", "downtrend": "BEARISH", "sideways": "NEUTRAL"}
        
        return AgentResponse(
            agent_name="DowTheory",
            signal=signal_map.get(result["trend"], "NEUTRAL"),
            confidence=result["strength"] * 8,
            summary=f"Dow: {result['trend'].upper()} | Strength: {result['strength']}/10",
            details=result
        )
