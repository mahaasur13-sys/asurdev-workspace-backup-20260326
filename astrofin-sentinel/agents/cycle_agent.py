"""
CycleAgent — Agent #4 в мультиагентной системе AstroFin Sentinel.

Роль: Анализ циклов рынка с использованием:
- Gann Wheel (Wheel of 24 / Square of 9)
- Bradley Model (S&P циклы)
- Фибоначчи временных зон

Ключевые данные:
- Time cycles (Gann)
- Price-time relationships
- Cycle identification
"""

from .base import BaseAgent, AgentInput, AgentOutput
import logging
import math

logger = logging.getLogger(__name__)


class CycleAgent(BaseAgent):
    """
    Cycle Analyst — анализ временных и ценовых циклов.
    
    Использует:
    - Gann Wheel (Square of 9) для определения ключевых уровней
    - Fibonacci time zones для проекции будущих разворотов
    - Bradley Model для синхронизации циклов
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="CycleAgent",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по анализу рыночных ЦИКЛОВ и ВРЕМЕНИ.

Твоя специализация:
1. GANN WHEEL (Square of 9) — углы, уровни поддержки/сопротивления по углам Ганна
2. BRADLEY MODEL — синхронизация циклов для прогнозирования разворотов
3. FIBONACCI TIME ZONES — проекция будущих ключевых дат
4. CYCLE IDENTIFICATION — определение доминирующего цикла (4-year, 10-week, etc.)

Данные для анализа:
- Цена входа: {price}
- Текущая дата: анализируй циклы на основе текущей даты
- symbol: {symbol}

Анализ должен включать:
1. Ключевые циклы для инструмента
2. Следующая потенциальная дата разворота
3. Целевые уровни по Gann
4. Ценово-временные соотношения

Формат ответа — строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения",
    "key_factors": [
        "cycle_type: 4-year cycle confirming",
        "next_turn_date: 2026-04-15",
        "gann_angle: 1x1 (45°)",
        "fib_time_zone: 3.618 extension"
    ],
    "warnings": ["cycle_warning"],
    "metadata": {
        "primary_cycle": "10-week",
        "next_turn": "2026-04-15",
        "gann_levels": [65000, 70000, 75000],
        "cycle_confidence": 0.75
    }
}

Верни ТОЛЬКО валидный JSON без markdown-разметки."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет цикловый анализ."""
        logger.info(f"[CycleAgent] Analyzing cycles for {input_data.symbol}")
        
        # Дополнительный контекст с данными
        extra_context = f"""
## Дополнительные данные:

Текущая цена: ${input_data.price:,.2f}
Таймфрейм: {input_data.timeframe}
Стратегия: {input_data.strategy}

Используй следующие методы:

1. GANN SQUARE OF 9:
   - Определи ближайшие углы Ганна от текущей цены
   - Рассчитай Natural и Cultural squares

2. FIBONACCI TIME ZONES:
   - Найди ключевые максимумы/минимумы на истории
   - Спроецируй будущие даты по фибоначчи

3. CYCLE DETECTION:
   - 4-year cycle (президентский)
   - 10-week cycle (торговый)
   - 28-day lunar cycle
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="CycleAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Cycle analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "cycle_type": result.get("metadata", {}).get("primary_cycle", "unknown"),
                "next_turn": result.get("metadata", {}).get("next_turn"),
                **result.get("metadata", {})
            }
        )


class GannAgent(BaseAgent):
    """
    Gann Analyst — специализированный агент по методам Ганна.
    
    Ключевые инструменты:
    - Gann angles (1x1, 1x2, 2x1, etc.)
    - Square of 9 для цены и времени
    - Gann levels (support/resistance)
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="GannAgent",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по МЕТОДАМ ГАННА (W.D. Gann Trading System).

Твоя специализация:
1. GANN ANGLES — линии тренда под углами 45°, 26.25°, 18.75° и т.д.
2. SQUARE OF 9 — цено-временные квадраты для определения разворотов
3. GANN SUPPORTS/RESISTANCE — уровни на основе квадратов и углов
4. NATURAL/CULTURAL SQUARES — важные ценовые уровни

Ключевые правила Ганна:
- 50% коррекция — критический уровень
- 1x1 угол = 45° = 1 единица цены на 1 единицу времени
- Цена и время должны быть в БАЛАНСЕ

Анализ для {symbol} при цене ${price:,.2f}:

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения",
    "key_factors": [
        "gann_angle: 1x2 bullish",
        "square_of_9_resistance: 68500",
        "balance_date: 2026-04-01"
    ],
    "warnings": ["time_not_confirming"],
    "metadata": {
        "primary_angle": "1x1",
        "support_levels": [65000, 63000],
        "resistance_levels": [70000, 72000],
        "balance_date": "2026-04-01",
        "squ_of_9_price": 68200
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет Gann-анализ."""
        logger.info(f"[GannAgent] Gann analysis for {input_data.symbol}")
        
        prompt = self._build_prompt(input_data, "")
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="GannAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Gann analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "primary_angle": result.get("metadata", {}).get("primary_angle"),
                "support_levels": result.get("metadata", {}).get("support_levels", []),
                "resistance_levels": result.get("metadata", {}).get("resistance_levels", []),
                **result.get("metadata", {})
            }
        )


class ElliotAgent(BaseAgent):
    """
    Elliott Wave Agent — анализ по волновой теории Эллиотта.
    
    Структура волн:
    - Impulse waves (1-2-3-4-5)
    - Corrective waves (A-B-C)
    -_extensions and truncations
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="ElliotAgent",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по ВОЛНОВОЙ ТЕОРИИ ЭЛЛИОТТА.

Твоя специализация:
1. WAVE COUNTING — определение текущей волны (1,2,3,4,5 или A,B,C)
2. FIBONACCI RELATIONSHIPS — волны в соотношениях фибоначчи
   - Wave 2 = 0.382, 0.5, 0.618 x Wave 1
   - Wave 3 = 1.618, 2.618 x Wave 1
   - Wave 4 = 0.382 x Wave 3
   - Wave 5 = 0.618, 1.0 x Wave 1
3. WAVE PERSONALITY — характеристики каждой волны
4. CORRECTION PATTERNS — zigzag, flat, triangle, combination

Анализ для {symbol} при цене ${price:,.2f}:

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения о волновой структуре",
    "key_factors": [
        "wave_count: Wave 3 of (3)",
        "wave_3_target: 72000 (2.618 x wave 1)",
        "subwave_structure: 1-2-3-4-5 in progress",
        "correction_expected: Wave 4 = 65000 zone"
    ],
    "warnings": ["wave_4_correction_imminent"],
    "metadata": {
        "current_wave": "3",
        "wave_3_target": 72000,
        "wave_4_support": 65000,
        "alternatives": ["wave_5_extension", "flat_correction"],
        "fib_ratios": {"wave2_wave1": 0.618, "wave3_wave1": 2.618}
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет Elliott Wave анализ."""
        logger.info(f"[ElliotAgent] Elliott analysis for {input_data.symbol}")
        
        prompt = self._build_prompt(input_data, "")
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="ElliotAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Elliott wave analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "current_wave": result.get("metadata", {}).get("current_wave"),
                "wave_targets": result.get("metadata", {}).get("wave_3_target"),
                **result.get("metadata", {})
            }
        )


class BradleyAgent(BaseAgent):
    """
    Bradley Agent — модель Брэдли для прогнозирования разворотов.
    
    Bradley Model синхронизирует циклы для определения
    "важных" дат разворотов рынка.
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="BradleyAgent",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по МОДЕЛИ БРЭДЛИ (Bradley Model).

Модель Брэдли использует синхронизацию циклов:
- 22-летний цикл (Bradley Model cycle)
- 10-недельный цикл
- 4-летний (президентский) цикл
- Солнечные циклы (11, 22 года)

Цель: определить "синхронизированные даты" когда
несколько циклов сходятся = высокая вероятность разворота.

Данные:
- symbol: {symbol}
- current_price: ${price:,.2f}
- current_date: {текущая дата}

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения",
    "key_factors": [
        "bradley_date: 2026-04-15",
        "cycle_confluence: 10-week + lunar",
        "historical_accuracy: 73%",
        "days_to_turn: 22"
    ],
    "warnings": ["low_confidence_cycle"],
    "metadata": {
        "next_bradley_date": "2026-04-15",
        "cycle_strength": "medium",
        "historical_reliability": 0.73,
        "supporting_cycles": ["10-week", "lunar"],
        "opposing_cycles": []
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет Bradley Model анализ."""
        logger.info(f"[BradleyAgent] Bradley model analysis for {input_data.symbol}")
        
        prompt = self._build_prompt(input_data, "")
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="BradleyAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Bradley model analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "next_bradley_date": result.get("metadata", {}).get("next_bradley_date"),
                "cycle_confluence": result.get("metadata", {}).get("supporting_cycles", []),
                **result.get("metadata", {})
            }
        )
