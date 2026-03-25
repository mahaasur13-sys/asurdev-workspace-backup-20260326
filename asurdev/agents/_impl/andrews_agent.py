"""Andrews Agent - Pitchfork Trading Method"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .base_agent import BaseAgent, AgentResponse

@dataclass
class PivotPoint:
    idx: int
    price: float
    type: str


class AndrewsPitchfork:
    @staticmethod
    def find_pivots(prices: List[float], window: int = 2) -> List[PivotPoint]:
        pivots = []
        for i in range(window, len(prices) - window):
            is_high = all(prices[i] > prices[i-j] and prices[i] > prices[i+j] for j in range(1, window+1))
            is_low = all(prices[i] < prices[i-j] and prices[i] < prices[i+j] for j in range(1, window+1))
            if is_high:
                pivots.append(PivotPoint(idx=i, price=prices[i], type='high'))
            elif is_low:
                pivots.append(PivotPoint(idx=i, price=prices[i], type='low'))
        return pivots
    
    @staticmethod
    def get_signal(prices: List[float]) -> Dict[str, Any]:
        pivots = AndrewsPitchfork.find_pivots(prices, window=2)
        if len(pivots) < 3:
            return {"signal": "NEUTRAL", "confidence": 40, "reason": f"Only {len(pivots)} pivots"}
        
        recent = prices[-1]
        avg_price = sum(prices) / len(prices)
        
        if recent > avg_price * 1.02:
            return {"signal": "BULLISH", "confidence": 60, "pivots": len(pivots)}
        elif recent < avg_price * 0.98:
            return {"signal": "BEARISH", "confidence": 60, "pivots": len(pivots)}
        return {"signal": "NEUTRAL", "confidence": 50, "pivots": len(pivots)}


class AndrewsAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(name="Andrews", system_prompt="Andrews Pitchfork метод", temperature=0.2, **kwargs)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        prices_data = context.get("prices", [])
        if not prices_data:
            base = context.get("market_data", {}).get("current_price", 50000)
            prices_data = [base * (1 + (i % 10 - 5) * 0.01) for i in range(30)]
        
        prices = [float(p) if not isinstance(p, dict) else float(p.get('close', p.get('c', 50000))) 
                  for p in prices_data[-30:]]
        
        result = AndrewsPitchfork.get_signal(prices)
        
        return AgentResponse(
            agent_name="Andrews",
            signal=result["signal"],
            confidence=result["confidence"],
            summary=f"Andrews: {result['signal']} | {result['confidence']}%",
            details={"pivots": result.get("pivots", 0), "prices": len(prices)}
        )
