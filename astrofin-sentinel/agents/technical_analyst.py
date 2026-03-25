"""
Технический аналитик — Agent #1 в мультиагентной системе AstroFin Sentinel.

Роль: Выполняет классический технический анализ на основе паттернов,
индикаторов (RSI, MACD, MA, Bollinger Bands) и объёмов.
"""

from .base import BaseAgent, AgentInput, AgentOutput
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyst(BaseAgent):
    """
    Агент технического анализа.
    
    Анализирует:
    - Ценовые паттерны (голова-плечи, двойное дно, etc.)
    - Индикаторы тренда (MA, EMA, MACD)
    - Осцилляторы (RSI, Stochastic)
    - Объёмы и волатильность (Bollinger Bands, ATR)
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="TechnicalAnalyst",
            model=model
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — опытный технический аналитик финансовых рынков с 20-летним стажем.

Твоя специализация:
- Price Action анализ (свечные паттерны, уровни поддержки/сопротивления)
- Трендовые индикаторы (SMA, EMA, MACD, ADX)
- Осцилляторы (RSI, Stochastic, CCI)
- Объёмный анализ (OBV, Volume Profile)
- Волатильность (Bollinger Bands, ATR, Standard Deviation)

Твои принципы:
1. Никогда не давай 100% уверенности — всегда учитывай неопределённость
2. Приоритизируй подтверждения от нескольких индикаторов
3. Учитывай таймфрейм — то, что работает на 1H, может не работать на 1D
4. Объёмы — ключевой подтверждающий фактор
5. Дивергенции — мощный разворотный сигнал

Твоя задача: проанализировать предоставленные данные и дать объективную
техническую оценку с конкретными уровнями входа/выхода и стоп-лоссом.

Всегда возвращай ТОЛЬКО валидный JSON в указанном формате."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет технический анализ."""
        logger.info(f"[TechnicalAnalyst] Analyzing {input_data.symbol} {input_data.action}")
        
        # Дополнительный контекст для анализа
        extra_context = """
## Дополнительные инструкции:

1. Определи текущий тренд (бычий/медвежий/боковой)
2. Найди ключевые уровни поддержки и сопротивления
3. Оцени силу сигнала от ML-модели
4. Учти таймфрейм — какие паттерны наиболее релевантны
5. Дай конкретные уровни:
   - Entry zone (зона входа)
   - Stop-loss (уровень стопа)
   - Take-profit targets (цели по прибыли)
   - Risk/Reward ratio

Будь консервативен в оценках. Лучше сказать "неопределённо" чем дать
ложный сигнал с высокой уверенностью.
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        logger.info(f"[TechnicalAnalyst] Confidence: {result.get('confidence', 0)}")
        
        return AgentOutput(
            agent="technical_analyst",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "No analysis available"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "signal_source": input_data.strategy,
                "indicators_checked": ["RSI", "MACD", "MA", "Bollinger"],
                **result.get("metadata", {})
            }
        )
