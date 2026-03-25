"""
Monte Carlo Agent — Агент для asurdev Sentinel
Интегрирует Monte Carlo симуляции с рыночными данными
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import asyncio
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from agents.base import BaseAgent, AgentResponse
except ImportError:
    # Fallback definitions if agents not available
    from dataclasses import dataclass
    from typing import Any
    
    @dataclass
    class AgentResponse:
        agent_name: str
        signal: str
        confidence: int
        summary: str
        details: Dict[str, Any]


MONTE_CARLO_PROMPT = """Ты — MonteCarlo Agent, эксперт по стохастическому моделированию финансовых рынков.

Твоя роль: использовать метод Monte Carlo для симуляции будущих ценовых траекторий и оценки рисков.

Что ты делаешь:
1. Берёшь текущую цену и исторические данные
2. Оцениваешь волатильность
3. Запускаешь 10000+ симуляций будущих траекторий
4. Анализируешь распределение исходов
5. Выдаёшь вероятностный прогноз и рекомендацию

Ключевые метрики:
- VaR 95% (Value at Risk) — максимальный ожидаемый убыток
- CVaR — средний убыток в худших 5% случаях
- P(up/down) — вероятность роста/падения

Формат ответа — JSON:
{
  "signal": "BUY/SELL/HOLD",
  "confidence": 0-100,
  "summary": "1-2 предложения"
}
"""


@dataclass
class MonteCarloAgent:
    """Агент для Monte Carlo симуляций"""
    
    name: str = "MonteCarlo"
    
    def __init__(self, **kwargs):
        self.name = "MonteCarlo"
    
    async def analyze(
        self,
        current_price: float,
        prices: list = None,
        days: int = 30,
        volatility: float = None,
        target_price: float = None,
        simulations: int = 10000
    ) -> AgentResponse:
        """Запуск Monte Carlo анализа."""
        from .simulator import MonteCarloSimulator
        
        # Рассчитываем волатильность
        if volatility is None and prices:
            sim_calc = MonteCarloSimulator(num_simulations=100)
            volatility = sim_calc.calculate_volatility(
                prices[-30:] if len(prices) > 30 else prices
            )
        elif volatility is None:
            volatility = 0.02
        
        # Симуляция
        sim = MonteCarloSimulator(num_simulations=simulations)
        result = sim.simulate(
            current_price=current_price,
            days=days,
            volatility=volatility,
            target_price=target_price
        )
        
        signal, confidence, reason = sim.get_signal(result)
        
        return AgentResponse(
            agent_name="MonteCarlo",
            signal=signal,
            confidence=confidence,
            summary=f"{signal} ({confidence}%): {reason}",
            details={
                "current_price": current_price,
                "forecast": {
                    "mean": round(result.mean_price, 2),
                    "median": round(result.median_price, 2),
                    "range_5_95": [round(result.percentile_5, 2), round(result.percentile_95, 2)]
                },
                "risk": {
                    "var_95": round(result.var_95 * 100, 2),
                    "max_drawdown_avg": round(result.max_drawdown_avg * 100, 2)
                },
                "probabilities": {
                    "up_5pct": round(result.prob_up_5pct * 100, 1),
                    "down_5pct": round(result.prob_down_5pct * 100, 1)
                }
            }
        )


def get_montecarlo_agent(**kwargs) -> MonteCarloAgent:
    """Get or create Monte Carlo agent singleton"""
    return MonteCarloAgent(**kwargs)


if __name__ == "__main__":
    async def test():
        agent = MonteCarloAgent()
        result = await agent.analyze(
            current_price=50000,
            days=30,
            volatility=0.025
        )
        print(f"Signal: {result.signal}")
        print(f"Confidence: {result.confidence}%")
        print(f"Details: {result.details}")
    
    asyncio.run(test())
