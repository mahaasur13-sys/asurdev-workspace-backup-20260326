"""
Monte Carlo Agent — asurdev Sentinel
Использует метод Monte Carlo для симуляции будущих цен и оценки рисков

Метод основан на:
- Geometric Brownian Motion (GBM) модели
- Стохастических симуляциях (10000+ траекторий)
- Расчёте VaR, CVaR, вероятностей
"""

from .simulator import (
    MonteCarloSimulator,
    PricePath,
    SimulationResult,
    quick_monte_carlo
)
from .agent import MonteCarloAgent, get_montecarlo_agent

__all__ = [
    "MonteCarloSimulator",
    "PricePath",
    "SimulationResult",
    "MonteCarloAgent",
    "get_montecarlo_agent",
    "quick_monte_carlo"
]
