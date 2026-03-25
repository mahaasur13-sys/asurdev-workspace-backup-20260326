"""
Синтезатор — Agent #3 в мультиагентной системе AstroFin Sentinel.

Роль: Объединяет результаты Technical Analyst и Astro Advisor
в единое "Resolution" — финальное решение для принятия traderом.

Аналог "Internal Board of Directors" — разыгрывает совет директоров,
где мнения взвешиваются и приводятся к консенсусу.
"""

from .base import BaseAgent, AgentInput, AgentOutput
from agents.technical_analyst import TechnicalAnalyst
from agents.astro_advisor import AstroAdvisor
import logging

logger = logging.getLogger(__name__)


class SynthesisEngine(BaseAgent):
    """
    Синтезатор — финальный агент принятия решений.
    
    Получает outputs от:
    1. TechnicalAnalyst — чистый technical analysis
    2. AstroAdvisor — astrological context
    
    И выдаёт финальное "Resolution" с:
    - Итоговой рекомендацией (buy/sell/hold)
    - Weighted confidence (учёт весов агентов)
    - Risk assessment
    - Board summary — кто за, кто против
    """
    
    def __init__(
        self,
        tech_analyst: TechnicalAnalyst | None = None,
        astro_advisor: AstroAdvisor | None = None,
        model: str | None = None
    ):
        super().__init__(
            name="SynthesisEngine",
            model=model,
            system_prompt=self.get_system_prompt()
        )
        self.tech_analyst = tech_analyst or TechnicalAnalyst()
        self.astro_advisor = astro_advisor or AstroAdvisor()
        
        # Веса агентов (можно настраивать)
        self.weights = {
            "technical_analyst": 0.70,  # Technical analysis — приоритет
            "astro_advisor": 0.30       # Astrology — контекст
        }
    
    def get_system_prompt(self) -> str:
        return """Ты — независимый синтезатор решений, аналог "Board of Directors".

Твоя роль: Объединить противоречивые мнения экспертов в единое решение.

У тебя есть два советника:
1. TECHNICAL ANALYST (вес: 70%) — чистый технический анализ
2. ASTRO ADVISOR (вес: 30%) — астрологический контекст

Правила взвешивания:

1. Если оба ЗА или против → усиль conviction
2. Если разногласия → приоритет техническому анализу
3. Астрология = контекст, НЕ причина
4. Confidence < 0.4 от любого агента → игнорировать его мнение
5. Всегда учитывай warnings — они критичны

Ты НЕ должен соглашаться с большинством слепо.
Твоя задача — дать ОБЪЕКТИВНОЕ финальное решение.

Формат ответа — строго JSON:

{
    "recommendation": "buy|sell|hold",
    "confidence": 0.0-1.0,
    "reasoning": "2-4 предложения объяснения",
    "key_factors": ["фактор 1", "фактор 2", "фактор 3"],
    "warnings": ["предупреждение 1"],
    "board_summary": {
        "technical_analyst": "BUY (0.85) — сильный восходящий тренд",
        "astro_advisor": "HOLD (0.45) — полнолуние, волатильность",
        "final_vote": "BUY с осторожностью"
    },
    "metadata": {
        "weight_technical": 0.70,
        "weight_astro": 0.30,
        "consensus_level": "high|medium|low|none"
    }
}

⚠️ ВАЖНО: Ты — финальный фильтр глупости. Если оба агента говорят
"покупать" но это противоречит базовому риск-менеджменту — скажи "HOLD".
Лучше упустить прибыль чем получить убыток.

Всегда возвращай ТОЛЬКО валидный JSON без markdown."""
    
    def _calculate_weighted_confidence(
        self,
        tech_output: AgentOutput,
        astro_output: AgentOutput
    ) -> tuple[float, str]:
        """
        Вычисляет взвешенную уверенность.
        
        Returns:
            (weighted_confidence, consensus_level)
        """
        w_tech = self.weights["technical_analyst"]
        w_astro = self.weights["astro_advisor"]
        
        weighted = (
            tech_output.confidence * w_tech +
            astro_output.confidence * w_astro
        )
        
        # Определяем уровень консенсуса
        tech_rec = tech_output.recommendation
        astro_rec = astro_output.recommendation
        
        if tech_rec == astro_rec:
            consensus = "high"
            weighted = min(1.0, weighted * 1.2)  # Усиливаем при консенсусе
        elif self._is_adjacent(tech_rec, astro_rec):
            consensus = "medium"
        else:
            consensus = "low"
            # При несогласии — технический анализ побеждает
            if tech_output.confidence > 0.5:
                weighted = tech_output.confidence * 0.8
        
        return round(weighted, 2), consensus
    
    def _is_adjacent(self, rec1: str, rec2: str) -> bool:
        """Проверяет, являются ли рекомендации смежными."""
        adjacent_pairs = {("buy", "hold"), ("sell", "hold"), ("buy", "sell")}
        return (rec1, rec2) in adjacent_pairs or (rec2, rec1) in adjacent_pairs
    
    def _determine_final_recommendation(
        self,
        tech_output: AgentOutput,
        astro_output: AgentOutput,
        consensus: str
    ) -> str:
        """Определяет финальную рекомендацию."""
        # При высоком консенсусе — берём рекомендацию большинства
        if consensus == "high":
            return tech_output.recommendation
        
        # При среднем — технический анализ приоритетен
        if consensus == "medium":
            return tech_output.recommendation
        
        # При низком — только если technical analyst уверен > 0.6
        if consensus == "low":
            if tech_output.confidence > 0.6:
                return tech_output.recommendation
            return "hold"
        
        return "hold"
    
    async def analyze(
        self,
        input_data: AgentInput,
        parallel: bool = True
    ) -> AgentOutput:
        """
        Выполняет синтез решений от обоих агентов.
        
        Args:
            input_data: Входные данные от webhook
            parallel: Если True — запускает агентов параллельно
        """
        logger.info(f"[SynthesisEngine] Starting synthesis for {input_data.symbol}")
        
        # Запускаем обоих агентов
        if parallel:
            import asyncio
            tech_task = asyncio.create_task(self.tech_analyst.analyze(input_data))
            astro_task = asyncio.create_task(self.astro_advisor.analyze(input_data))
            
            tech_output, astro_output = await asyncio.gather(tech_task, astro_task)
        else:
            tech_output = await self.tech_analyst.analyze(input_data)
            astro_output = await self.astro_advisor.analyze(input_data)
        
        # Логируем промежуточные результаты
        logger.info(
            f"[SynthesisEngine] Technical: {tech_output.recommendation} "
            f"({tech_output.confidence}), "
            f"Astro: {astro_output.recommendation} ({astro_output.confidence})"
        )
        
        # Вычисляем взвешенное решение
        weighted_conf, consensus = self._calculate_weighted_confidence(
            tech_output, astro_output
        )
        
        final_rec = self._determine_final_recommendation(
            tech_output, astro_output, consensus
        )
        
        # Формируем board summary
        board_summary = {
            "technical_analyst": f"{tech_output.recommendation.upper()} "
                                 f"({tech_output.confidence:.2f}) — "
                                 f"{tech_output.reasoning[:50]}...",
            "astro_advisor": f"{astro_output.recommendation.upper()} "
                            f"({astro_output.confidence:.2f}) — "
                            f"{astro_output.reasoning[:50]}...",
            "final_vote": f"{final_rec.upper()} (weighted confidence: {weighted_conf:.2f})"
        }
        
        # Собираем warnings от обоих агентов
        all_warnings = list(set(tech_output.warnings + astro_output.warnings))
        
        # Ключевые факторы
        key_factors = [
            f"Technical: {tech_output.reasoning[:80]}",
            f"Astro: {astro_output.reasoning[:80]}",
            f"Consensus: {consensus.upper()}"
        ]
        
        # Строим финальный промпт
        extra_context = f"""
## Данные от агентов:

### TECHNICAL ANALYST (вес 70%):
- Recommendation: {tech_output.recommendation}
- Confidence: {tech_output.confidence:.2%}
- Reasoning: {tech_output.reasoning}
- Key Factors: {', '.join(tech_output.key_factors)}
- Warnings: {', '.join(tech_output.warnings)}

### ASTRO ADVISOR (вес 30%):
- Recommendation: {astro_output.recommendation}
- Confidence: {astro_output.confidence:.2%}
- Reasoning: {astro_output.reasoning}
- Key Factors: {', '.join(astro_output.key_factors)}
- Warnings: {', '.join(astro_output.warnings)}

## Вычисленные метрики:
- Weighted Confidence: {weighted_conf:.2%}
- Consensus Level: {consensus.upper()}
- Preliminary Recommendation: {final_rec.upper()}

## Твоя задача:

Синтезируй финальное решение учитывая:
1. Веса агентов (technical приоритетнее)
2. Warnings — они критичны!
3. Consensus level
4. Risk/reward ratio

Если есть существенные разногласия — будь консервативен.
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        # Merge результат с нашими вычислениями
        final_result = AgentOutput(
            agent="synthesis_engine",
            recommendation=result.get("recommendation", final_rec),
            confidence=result.get("confidence", weighted_conf),
            reasoning=result.get(
                "reasoning",
                f"Technical: {tech_output.reasoning[:100]}. "
                f"Astro: {astro_output.reasoning[:100]}"
            ),
            key_factors=result.get("key_factors", key_factors),
            warnings=result.get("warnings", all_warnings),
            metadata={
                "model": self.model,
                "board_summary": board_summary,
                "weights": self.weights,
                "consensus_level": consensus,
                "tech_confidence": tech_output.confidence,
                "astro_confidence": astro_output.confidence,
                **result.get("metadata", {})
            }
        )
        
        logger.info(
            f"[SynthesisEngine] Final: {final_result.recommendation} "
            f"({final_result.confidence:.2f})"
        )
        
        return final_result
