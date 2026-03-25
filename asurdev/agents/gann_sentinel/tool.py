"""
Gann Sentinel — LangChain Tool
Интеграция с LangChain для использования в агентах
"""
from typing import Optional
from langchain_core.tools import tool

from .gann_sentinel import GannSentinel, GannLevels


# Глобальный экземпляр
_gann_sentinel: Optional[GannSentinel] = None


def get_gann_sentinel_tool() -> GannSentinel:
    """Получить экземпляр GannSentinel"""
    global _gann_sentinel
    if _gann_sentinel is None:
        _gann_sentinel = GannSentinel()
    return _gann_sentinel


@tool
def calculate_gann_levels(price: float, method: str = "square9") -> str:
    """
    Рассчитывает уровни поддержки/сопротивления по методам Ганна.
    
    Args:
        price: Текущая цена актива (например, 58000.0 для BTC)
        method: Метод расчета:
            - "square9": Классический Square of 9 (рекомендуется)
            - "cardinal": Cardinal Cross (4 оси)
            - "combined": Оба метода вместе
    
    Returns:
        Строка с уровнями и рекомендацией для голоса/дашборда
    
    Примеры:
        calculate_gann_levels(58000) -> Уровни Ганна для BTC
        calculate_gann_levels(1850, method="cardinal") -> Cardinal Cross для ETH
    """
    agent = get_gann_sentinel_tool()
    result = agent.calculate(price, method)
    return agent.to_text(result)


@tool  
def calculate_gann_for_crypto(symbol: str, price: float) -> str:
    """
    Рассчитывает уровни Ганна для криптовалюты.
    
    Args:
        symbol: Тикер (BTC, ETH, SOL)
        price: Текущая цена
    
    Returns:
        Уровни и рекомендация
    """
    agent = get_gann_sentinel_tool()
    result = agent.calculate(price)
    return f"*{symbol}* @ {price}\n\n" + agent.to_text(result)


@tool
def get_gann_recommendation(price: float) -> str:
    """
    Быстрая рекомендация по текущей цене.
    
    Args:
        price: Текущая цена
    
    Returns:
        Одна строка с рекомендацией
    """
    agent = get_gann_sentinel_tool()
    result = agent.calculate(price)
    return result["recommendation"]


# Экспорт для удобства
GANN_TOOLS = [
    calculate_gann_levels,
    calculate_gann_for_crypto,
    get_gann_recommendation,
]
