"""
Gann Sentinel — AutoGen Tool
Интеграция с AutoGen для мультиагентных систем
"""
from typing import Callable, Optional
from autogen import Tool, ToolFunc

from .gann_sentinel import GannSentinel


class GannSentinelAutoGen:
    """
    Gann Sentinel для AutoGen агентов.
    
    Использование:
    
    from autogen import ConversableAgent
        
    gann_tool = GannSentinelAutoGen().get_tool()
    
    agent = ConversableAgent(
        "trader",
        system_message="Ты трейдер. Используй Gann Sentinel для уровней.",
        tools=[gann_tool]
    )
    """
    
    def __init__(self):
        self._agent = GannSentinel()
    
    def get_tool(self) -> Tool:
        """Получить AutoGen Tool"""
        return Tool(
            name="gann_levels",
            description="""Рассчитывает уровни поддержки/сопротивления по Square of 9 (Ганн).
            
Вход: price (float) - текущая цена
Выход: уровни и рекомендация

Пример: gann_levels(58000) покажет:
- Buy Zone: 58350 - 58710
- Sell Zone: 57620 - 57290  
- Targets UP: 59100, 59500, 59920
- Targets DOWN: 57080, 56650, 56230
- Strong Resistance: 59500
- Strong Support: 57080
- Recommendation: LONG/SHORT/WAIT""",
            func_or_tool_func=self._calculate_wrapper,
        )
    
    def _calculate_wrapper(self, price: float) -> str:
        """Обертка для AutoGen"""
        result = self._agent.calculate(price)
        return self._agent.to_text(result)
    
    def get_all_tools(self) -> list[Tool]:
        """Получить все инструменты"""
        return [
            Tool(
                name="gann_square9",
                description="Классический Square of 9",
                func_or_tool_func=lambda price: self._agent.to_text(self._agent.calculate(price, "square9")),
            ),
            Tool(
                name="gann_cardinal", 
                description="Cardinal Cross Method",
                func_or_tool_func=lambda price: self._agent.to_text(self._agent.calculate(price, "cardinal")),
            ),
            Tool(
                name="gann_combined",
                description="Комбинированный метод",
                func_or_tool_func=lambda price: self._agent.to_text(self._agent.calculate(price, "combined")),
            ),
            Tool(
                name="gann_recommendation",
                description="Быстрая рекомендация",
                func_or_tool_func=lambda price: self._agent.calculate(price)["recommendation"],
            ),
        ]


def get_gann_autogen_tool() -> Tool:
    """Быстрое получение инструмента"""
    return GannSentinelAutoGen().get_tool()
