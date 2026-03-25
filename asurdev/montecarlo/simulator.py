"""
Monte Carlo Simulator — Симуляция будущих ценовых траекторий
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import random


@dataclass
class PricePath:
    """Одна симулированная траектория цены"""
    path_id: int
    prices: List[float]
    timestamps: List[datetime]
    final_price: float
    max_price: float
    min_price: float
    max_drawdown: float
    volatility_used: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "path_id": self.path_id,
            "final_price": round(self.final_price, 2),
            "max_price": round(self.max_price, 2),
            "min_price": round(self.min_price, 2),
            "max_drawdown": round(self.max_drawdown * 100, 2),
            "volatility": round(self.volatility_used * 100, 2)
        }


@dataclass
class SimulationResult:
    """Результат Monte Carlo симуляции"""
    symbol: str
    current_price: float
    num_simulations: int
    num_days: int
    paths: List[PricePath]
    timestamp: datetime
    
    # Статистика
    mean_price: float
    median_price: float
    std_price: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    
    # Риск метрики
    var_95: float  # Value at Risk 95%
    cvar_95: float  # Conditional VaR
    max_drawdown_avg: float
    
    # Вероятности
    prob_up_5pct: float  # P(цена вырастет на 5%+)
    prob_down_5pct: float  # P(цена упадёт на 5%+)
    prob_reaches_target: float  # P(достигнет цели)
    target_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "current_price": round(self.current_price, 2),
            "num_simulations": self.num_simulations,
            "num_days": self.num_days,
            "timestamp": self.timestamp.isoformat(),
            "forecast": {
                "mean": round(self.mean_price, 2),
                "median": round(self.median_price, 2),
                "std": round(self.std_price, 2),
                "percentiles": {
                    "5%": round(self.percentile_5, 2),
                    "25%": round(self.percentile_25, 2),
                    "75%": round(self.percentile_75, 2),
                    "95%": round(self.percentile_95, 2)
                }
            },
            "risk": {
                "var_95": round(self.var_95 * 100, 2),
                "cvar_95": round(self.cvar_95 * 100, 2),
                "max_drawdown_avg": round(self.max_drawdown_avg * 100, 2)
            },
            "probabilities": {
                "up_5pct": round(self.prob_up_5pct * 100, 1),
                "down_5pct": round(self.prob_down_5pct * 100, 1),
                "reaches_target": round(self.prob_reaches_target * 100, 1) if self.target_price else None
            },
            "target_price": round(self.target_price, 2) if self.target_price else None
        }


class MonteCarloSimulator:
    """
    Monte Carlo симулятор для финансовых временных рядов.
    
    Использует Geometric Brownian Motion (GBM) модель:
    dS = μSdt + σSdW
    
    где:
    - S — цена
    - μ — drift (средняя доходность)
    - σ — волатильность
    - dW — винеровский процесс
    """
    
    def __init__(
        self,
        num_simulations: int = 10000,
        seed: Optional[int] = None
    ):
        self.num_simulations = num_simulations
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
    
    def calculate_volatility(self, prices: List[float]) -> float:
        """Расчёт волатильности из исторических цен"""
        if len(prices) < 2:
            return 0.02  # Default 2%
        
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns)
    
    def simulate(
        self,
        current_price: float,
        days: int = 30,
        annual_drift: float = 0.0,  # Средняя годовая доходность
        volatility: Optional[float] = None,
        target_price: Optional[float] = None
    ) -> SimulationResult:
        """
        Запуск Monte Carlo симуляции.
        
        Args:
            current_price: Текущая цена
            days: Горизонт симуляции (дней)
            annual_drift: Годовая доходность (напр. 0.12 для 12%)
            volatility: Волатильность (если None — рассчитается)
            target_price: Целевая цена для расчёта вероятности достижения
        
        Returns:
            SimulationResult с траекториями и статистикой
        """
        # Если волатильность не дана — используем оценку
        if volatility is None:
            volatility = 0.02  # Default 2%
        
        # Время
        dt = 1 / 252  # 1 торговый день
        
        # Генерация случайных траекторий
        paths = []
        final_prices = []
        max_drawdowns = []
        
        for i in range(self.num_simulations):
            path = [current_price]
            max_price = current_price
            peak = current_price
            
            for _ in range(days):
                # Случайный винеровский процесс
                z = np.random.standard_normal()
                
                # Геометрическое броуновское движение
                drift = (annual_drift - 0.5 * volatility**2) * dt
                diffusion = volatility * np.sqrt(dt) * z
                
                new_price = path[-1] * np.exp(drift + diffusion)
                path.append(new_price)
                
                # Отслеживаем максимум для drawdown
                if new_price > max_price:
                    max_price = new_price
                
            # Max drawdown для этой траектории
            max_dd = (max_price - min(path)) / max_price if max_price > 0 else 0
            max_drawdowns.append(max_dd)
            
            final_prices.append(path[-1])
            
            # Создаём timestamps
            timestamps = [
                datetime.now() + timedelta(days=j) 
                for j in range(len(path))
            ]
            
            paths.append(PricePath(
                path_id=i,
                prices=[round(p, 2) for p in path],
                timestamps=timestamps,
                final_price=round(path[-1], 2),
                max_price=round(max_price, 2),
                min_price=round(min(path), 2),
                max_drawdown=max_dd,
                volatility_used=volatility
            ))
        
        final_prices = np.array(final_prices)
        
        # Статистика
        mean_price = np.mean(final_prices)
        median_price = np.median(final_prices)
        std_price = np.std(final_prices)
        
        percentiles = np.percentile(final_prices, [5, 25, 75, 95])
        
        # VaR и CVaR (95%)
        var_95 = (np.percentile(final_prices, 5) - current_price) / current_price
        cvar_95 = np.mean(final_prices[final_prices <= np.percentile(final_prices, 5)])
        cvar_95 = (cvar_95 - current_price) / current_price
        
        # Вероятности
        prob_up_5pct = np.sum(final_prices >= current_price * 1.05) / self.num_simulations
        prob_down_5pct = np.sum(final_prices <= current_price * 0.95) / self.num_simulations
        
        prob_reaches = 0.0
        if target_price:
            prob_reaches = np.sum(final_prices >= target_price) / self.num_simulations
        
        return SimulationResult(
            symbol="UNKNOWN",
            current_price=current_price,
            num_simulations=self.num_simulations,
            num_days=days,
            paths=paths[:100],  # Сохраняем только 100 траекторий
            timestamp=datetime.now(),
            mean_price=mean_price,
            median_price=median_price,
            std_price=std_price,
            percentile_5=percentiles[0],
            percentile_25=percentiles[1],
            percentile_75=percentiles[2],
            percentile_95=percentiles[3],
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown_avg=np.mean(max_drawdowns),
            prob_up_5pct=prob_up_5pct,
            prob_down_5pct=prob_down_5pct,
            prob_reaches_target=prob_reaches,
            target_price=target_price
        )
    
    def get_signal(
        self,
        result: SimulationResult,
        confidence_threshold: float = 0.6
    ) -> Tuple[str, int, str]:
        """
        Генерация торгового сигнала на основе Monte Carlo.
        
        Returns:
            (signal, confidence, reason)
        """
        prob_up = result.prob_up_5pct
        prob_down = result.prob_down_5pct
        
        # Ожидаемая доходность
        expected_return = (result.mean_price - result.current_price) / result.current_price
        
        # Риск-скорректированная оценка
        risk_adj_score = expected_return / (result.std_price / result.current_price + 0.001)
        
        if prob_up >= confidence_threshold and risk_adj_score > 0:
            confidence = int(min(prob_up * 100, 99))
            return "BUY", confidence, f"P(up)={prob_up:.1%}, E(r)={expected_return:.1%}"
        
        elif prob_down >= confidence_threshold and risk_adj_score < 0:
            confidence = int(min(prob_down * 100, 99))
            return "SELL", confidence, f"P(down)={prob_down:.1%}, E(r)={expected_return:.1%}"
        
        else:
            # Neutral на основе медианы
            if result.median_price > result.current_price:
                confidence = 45
                reason = f"Median > Current (not confident)"
            elif result.median_price < result.current_price:
                confidence = 45
                reason = f"Median < Current (not confident)"
            else:
                confidence = 50
                reason = "No clear signal"
            
            return "HOLD", confidence, reason


def quick_monte_carlo(
    current_price: float,
    days: int = 30,
    volatility: float = 0.02,
    simulations: int = 1000
) -> Dict[str, Any]:
    """
    Быстрая Monte Carlo симуляция одной функцией.
    """
    sim = MonteCarloSimulator(num_simulations=simulations, seed=42)
    result = sim.simulate(
        current_price=current_price,
        days=days,
        volatility=volatility
    )
    signal, confidence, reason = sim.get_signal(result)
    
    return {
        "current_price": current_price,
        "days": days,
        "forecast": {
            "mean": round(result.mean_price, 2),
            "median": round(result.median_price, 2),
            "range": [round(result.percentile_5, 2), round(result.percentile_95, 2)]
        },
        "signal": signal,
        "confidence": confidence,
        "reason": reason,
        "risk": {
            "var_95": round(result.var_95 * 100, 2),
            "max_drawdown_avg": round(result.max_drawdown_avg * 100, 2)
        }
    }


if __name__ == "__main__":
    # Тест
    print("=== Monte Carlo Test ===")
    result = quick_monte_carlo(50000, days=30, volatility=0.03)
    print(f"Price: ${result['current_price']}")
    print(f"Forecast: ${result['forecast']['median']} (median)")
    print(f"Range 5-95%: ${result['forecast']['range'][0]} - ${result['forecast']['range'][1]}")
    print(f"Signal: {result['signal']} ({result['confidence']}%)")
    print(f"Reason: {result['reason']}")
    print(f"VaR 95%: {result['risk']['var_95']}%")
