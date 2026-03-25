"""
Monte Carlo Backtester — Бэктестинг сигналов Monte Carlo
"""

import json
from datetime import datetime
from typing import Dict, Any, List

def generate_test_prices(start: float, days: int, trend: float = 0) -> List[float]:
    """Генерация тестовых цен"""
    import random
    import math
    
    prices = [start]
    for i in range(days):
        # Случайное изменение
        change = random.gauss(trend / days, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    return prices

def run_backtest() -> Dict[str, Any]:
    """Запуск бэктеста Monte Carlo сигналов"""
    from montecarlo import get_montecarlo_agent
    import asyncio
    
    results = []
    
    test_cases = [
        {"price": 50000, "days": 30, "vol": 0.03, "trend": 0.05, "name": "BTC Up"},
        {"price": 50000, "days": 30, "vol": 0.03, "trend": -0.05, "name": "BTC Down"},
        {"price": 50000, "days": 30, "vol": 0.03, "trend": 0, "name": "BTC Sideways"},
    ]
    
    async def run():
        agent = get_montecarlo_agent()
        
        for tc in test_cases:
            prices = generate_test_prices(tc["price"], tc["days"], tc["trend"])
            
            result = await agent.analyze(
                current_price=prices[-1],
                prices=prices,
                days=7,
                volatility=tc["vol"]
            )
            
            results.append({
                "name": tc["name"],
                "signal": result.signal,
                "confidence": result.confidence,
                "var_95": result.details["risk"]["var_95"]
            })
    
    asyncio.run(run())
    
    return {
        "timestamp": datetime.now().isoformat(),
        "num_tests": len(results),
        "results": results
    }

if __name__ == "__main__":
    print("=== Monte Carlo Backtest ===")
    result = run_backtest()
    print(json.dumps(result, indent=2))
