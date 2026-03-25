"""
AstroCouncil — Agent #5 в мультиагентной системе AstroFin Sentinel.

Роль: Астрологический совет — коллективная "мудрость" планет.
Выступает как астролог-советник с несколькими ветвями:
- Natal aspects (кармические)
- Current transits (текущие влияния)
- Muhurta (выбор момента)

Ключевые данные:
- Moon phases
- Planetary aspects (conjunctions, oppositions, etc.)
- Zodiac positions
"""

from .base import BaseAgent, AgentInput, AgentOutput
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class AstroCouncil(BaseAgent):
    """
    Astro Council — коллективный астрологический совет.
    
    Внутренние "члены совета":
    1. LUNAR COUNCIL — фазы Луны и их влияние
    2. PLANETARY COUNCIL — аспекты планет
    3. ZODIAC COUNCIL — положение в знаках
    4. MUHURTA COUNCIL — выбор времени
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="AstroCouncil",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — АСТРОЛОГИЧЕСКИЙ СОВЕТ (Astro Council) для трейдинга.

Ты объединяешь несколько астрологических дисциплин:

1. LUNAR INFLUENCE (Фазы Луны):
   - New Moon: начало цикла, осторожность
   - Full Moon: кульминация, возможны развороты
   - Waxing (растущая): благоприятно для BUY
   - Waning (убывающая): благоприятно для SELL
   
2. PLANETARY ASPECTS (Аспекты планет):
   - Conjunction (0°): начало нового цикла
   - Trine (120°): гармония, легкая энергия
   - Square (90°): напряжение, перемены
   - Opposition (180°): кульминация, интенсивность
   - Sextile (60°): возможности
   
3. ZODIAC POSITIONS (Положение в знаках):
   - Fire signs (Aries, Leo, Sag): активность, агрессия
   - Earth signs (Taurus, Virgo, Cap): стабильность
   - Air signs (Gemini, Libra, Aqu): интеллект, анализ
   - Water signs (Cancer, Scorpio, Pis): эмоции, интуиция
   
4. MUHURTA TIMING (Выбор момента):
   - Choghadiya windows
   - Benefic/malefic planets
   - Hora (час планеты)

Текущие данные:
- symbol: {symbol}
- price: ${price:,.2f}
- action: {action}

Анализ должен включать:
1. Текущую фазу Луны и её влияние на трейдинг
2. Ключевые планетные аспекты
3. Положение Луны в знаке
4. Оценку момента для сделки (Muhurta)

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения",
    "key_factors": [
        "moon_phase: Waxing Gibbous",
        "moon_in: Scorpio (intensity)",
        "key_aspect: Jupiter trine Saturn",
        "muhurta: Labh (profit window)"
    ],
    "warnings": [
        "full_moon_volatility",
        "mercury_retrograde"
    ],
    "metadata": {
        "moon_phase": "Waxing Gibbous",
        "moon_illumination": 78,
        "moon_zodiac": "Scorpio",
        "key_aspects": [
            {"aspect": "Jupiter trine Saturn", "nature": "benefic"},
            {"aspect": "Mars square Pluto", "nature": "challenging"}
        ],
        "muhurta": {
            "current": "Labh",
            "meaning": "Profit window",
            "score": 0.82
        },
        "trading_recommendation": "favorable_with_caution"
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет астрологический совет."""
        logger.info(f"[AstroCouncil] Astro council for {input_data.symbol}")
        
        extra_context = f"""
## Астрологические данные:

Current Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
symbol: {input_data.symbol}
Action: {input_data.action}
Price: ${input_data.price:,.2f}

Используй инструменты:
- get_moon_phase — фаза Луны
- get_upcoming_astro_events — планетные аспекты

Проведи полный астрологический анализ и дай рекомендацию.
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="AstroCouncil",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Astro council analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "moon_phase": result.get("metadata", {}).get("moon_phase"),
                "moon_zodiac": result.get("metadata", {}).get("moon_zodiac"),
                "key_aspects": result.get("metadata", {}).get("key_aspects", []),
                "muhurta": result.get("metadata", {}).get("muhurta"),
                "trading_recommendation": result.get("metadata", {}).get("trading_recommendation"),
                **result.get("metadata", {})
            }
        )


class SentimentAgent(BaseAgent):
    """
    Sentiment Agent — анализ настроений рынка.
    
    Собирает данные из:
    - Crypto news
    - Social media (Twitter/X)
    - Funding rates (Binance)
    - Order book imbalance
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="SentimentAgent",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — эксперт по ANALYSIS OF MARKET SENTIMENT.

Твоя специализация:
1. NEWS SENTIMENT — анализ новостей и их влияния
2. SOCIAL SENTIMENT — настроения в Twitter/X, Reddit
3. FUNDING RATES — ставки финансирования на биржах
4. ORDER BOOK IMBALANCE — дисбаланс ордербука
5. FEAR & GREED INDEX — индекс страха/жадности

Ключевые индикаторы:
- Funding Rate > 0.01% =过度乐观 (overly bullish)
- Funding Rate < -0.01% =过度悲观 (overly bearish)
- Order Book Ratio > 1.5 = buy side dominant
- Fear & Greed > 75 = крайняя жадность
- Fear & Greed < 25 = крайний страх

symbol: {symbol}
Current Price: ${price:,.2f}

Верни строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения",
    "key_factors": [
        "fear_greed: 72 (Greed)",
        "funding_rate: 0.015% (bullish)",
        "social_sentiment: 68% positive",
        "order_book_ratio: 1.3"
    ],
    "warnings": [
        "extreme_greed_warning",
        "funding_rate_correction_risk"
    ],
    "metadata": {
        "fear_greed_index": 72,
        "fear_greed_label": "Greed",
        "funding_rate": 0.015,
        "social_score": 68,
        "order_book_ratio": 1.3,
        "sentiment_reversal_risk": 0.45,
        "contrarian_signal": "sell"
    }
}

Верни ТОЛЬКО валидный JSON без markdown."""
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет анализ настроений."""
        logger.info(f"[SentimentAgent] Sentiment analysis for {input_data.symbol}")
        
        extra_context = f"""
## Sentiment данные:

symbol: {input_data.symbol}
Price: ${input_data.price:,.2f}
Action: {input_data.action}

Используй инструменты:
- search_financial_news — поиск новостей
- get_crypto_sentiment — общий sentiment

Собери данные и дай рекомендацию на основе contrarian analysis.
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        return AgentOutput(
            agent="SentimentAgent",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "Sentiment analysis completed"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "fear_greed_index": result.get("metadata", {}).get("fear_greed_index"),
                "funding_rate": result.get("metadata", {}).get("funding_rate"),
                "social_score": result.get("metadata", {}).get("social_score"),
                "order_book_ratio": result.get("metadata", {}).get("order_book_ratio"),
                "contrarian_signal": result.get("metadata", {}).get("contrarian_signal"),
                **result.get("metadata", {})
            }
        )
