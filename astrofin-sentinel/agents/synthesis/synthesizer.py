"""
Synthesizer Agent — Final Decision Node
=======================================
Синтезатор AstroFin Sentinel. Финальный агент в цепочке.

Протокол:
1. Получает все AgentResult от предыдущих агентов
2. Взвешивает сигналы (technical 70%, astro 30%)
3. Формирует финальную рекомендацию с Confidence Score
4. Всегда добавляет блоки Risk и Limitations
"""

from __future__ import annotations
from typing import Optional

from agents.base.base_agent import (
    BaseAgent,
    SentinelState,
    AgentResult,
    Confidence,
    Action,
)


class SynthesizerAgent(BaseAgent):
    """
    Синтезатор. Объединяет результаты всех агентов.

    Веса по умолчанию:
    - Technical (market + scenarios): 70%
    - Astro: 30%
    """

    # Веса можно переопределять через init
    DEFAULT_WEIGHTS = {
        "technical": 0.70,
        "astro": 0.30,
    }

    def __init__(self, kb_path: str = "knowledge_base", weights: dict | None = None):
        super().__init__(
            agent_id="synthesizer",
            agent_role="synthesizer",
            instructions_path=None,
            kb_path=kb_path,
        )
        self.weights = weights or self.DEFAULT_WEIGHTS

    def execute(self, state: SentinelState) -> AgentResult:
        """
        Выполняет финальный синтез.

        Args:
            state: SentinelState со всеми AgentResult

        Returns:
            AgentResult с финальной рекомендацией
        """
        errors = []
        chunks_used = []

        # ── 1. Сбор результатов ─────────────────────────────
        market = state.market_analysis
        bull = state.bull_case
        bear = state.bear_case
        astro = state.astro_analysis

        if not market:
            errors.append("Missing market_analysis in state")

        # ── 2. Техническая сводка ────────────────────────────
        tech_signal = self._evaluate_technical(market, bull, bear)

        # ── 3. Астрологическая сводка ────────────────────────
        astro_signal = self._evaluate_astro(astro)

        # ── 4. Взвешенный итог ──────────────────────────────
        final_score = (
            tech_signal * self.weights["technical"] +
            astro_signal * self.weights["astro"]
        )

        # ── 5. Финальное решение ─────────────────────────────
        action, confidence = self._make_decision(final_score, tech_signal, astro_signal)

        # ── 6. Уровни ──────────────────────────────────────
        levels = self._calculate_levels(state, action)

        # ── 7. Формирование нарратива ───────────────────────
        narrative = self._build_final_report(state, tech_signal, astro_signal, final_score, action, levels)

        findings = {
            "tech_signal": tech_signal,
            "astro_signal": astro_signal,
            "final_score": final_score,
            "action": action.value,
            "confidence": confidence.value,
            "weights_used": self.weights,
            "levels": levels,
            "correlation": self._describe_correlation(tech_signal, astro_signal),
        }

        return AgentResult(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            status="success",
            findings=findings,
            narrative=narrative,
            confidence=confidence,
            action_recommendation=action,
            metadata={
                "tech_weight": self.weights["technical"],
                "astro_weight": self.weights["astro"],
            },
            knowledge_sources=[c["id"] for c in chunks_used],
            errors=errors,
        )

    def _evaluate_technical(
        self,
        market: Optional[AgentResult],
        bull: Optional[AgentResult],
        bear: Optional[AgentResult],
    ) -> float:
        """
        Оценивает технические сигналы. Возвращает -1 to +1.
        """
        if not market:
            return 0.0

        direction = market.findings.get("direction", "neutral")
        rsi = market.findings.get("rsi", 50)

        signal = 0.0

        # Направление
        if direction == "bullish":
            signal += 0.5
        elif direction == "bearish":
            signal -= 0.5

        # RSI экстремумы
        if rsi < 30:
            signal += 0.3  # перепродан = бычий потенциал
        elif rsi > 70:
            signal -= 0.3  # перекуплен = медвежий потенциал

        return max(-1.0, min(1.0, signal))

    def _evaluate_astro(self, astro: Optional[AgentResult]) -> float:
        """
        Оценивает астрологические сигналы. Возвращает -1 to +1.
        """
        if not astro:
            return 0.0

        auspicious = astro.findings.get("auspicious_score", 5)
        ch_is_good = astro.findings.get("choghadiya_analysis", {}).get("is_good", None)

        # Нормализуем auspicious_score (1-10) → (-1 to +1)
        normalized = (auspicious - 5) / 5

        if ch_is_good is True:
            normalized += 0.2
        elif ch_is_good is False:
            normalized -= 0.3

        return max(-1.0, min(1.0, normalized))

    def _make_decision(
        self,
        final_score: float,
        tech: float,
        astro: float,
    ) -> tuple[Action, Confidence]:
        """Принимает финальное решение."""
        if final_score > 0.4:
            action = Action.BUY
        elif final_score < -0.4:
            action = Action.SELL
        else:
            action = Action.HOLD

        # Confidence зависит от согласованности сигналов
        signal_spread = abs(tech - astro)
        if signal_spread < 0.3 and abs(final_score) > 0.5:
            confidence = Confidence.HIGH
        elif signal_spread < 0.5:
            confidence = Confidence.MEDIUM
        else:
            confidence = Confidence.LOW  # Техника и астрология противоречат

        return action, confidence

    def _calculate_levels(self, state: SentinelState, action: Action) -> dict:
        """Рассчитывает уровни входа, стопа и целей."""
        market = state.market
        if not market:
            return {"entry": None, "stop": None, "target1": None, "target2": None}

        price = market.price
        support = market.support
        resistance = market.resistance

        if action == Action.BUY:
            entry = round(price * 1.005, 2)  # небольшое проскальзывание
            stop = round(support * 0.99, 2)
            target1 = round(resistance * 1.02, 2)
            target2 = round(resistance * 1.05, 2)
        elif action == Action.SELL:
            entry = round(price * 0.995, 2)
            stop = round(resistance * 1.01, 2)
            target1 = round(support * 0.98, 2)
            target2 = round(support * 0.95, 2)
        else:
            entry = round(price, 2)
            stop = round(support * 0.98, 2)
            target1 = round(resistance * 1.01, 2)
            target2 = None

        return {
            "entry": entry,
            "stop": stop,
            "target1": target1,
            "target2": target2,
        }

    def _describe_correlation(self, tech: float, astro: float) -> str:
        """Описывает согласованность техники и астрологии."""
        diff = abs(tech - astro)
        if diff < 0.2:
            return "Синхронны — оба сигнала указывают в одну сторону"
        elif diff < 0.5:
            return "Частично согласованы — есть расхождение в силе"
        else:
            return "Противоречат — техника и астрология дают противоположные сигналы"

    def _build_final_report(
        self,
        state: SentinelState,
        tech_signal: float,
        astro_signal: float,
        final_score: float,
        action: Action,
        levels: dict,
    ) -> str:
        """Формирует финальный отчёт Synthesizer."""
        tech_dir = "↑ Бычий" if tech_signal > 0 else ("↓ Медвежий" if tech_signal < 0 else "→ Нейтральный")
        astro_dir = "↑ Благоприятно" if astro_signal > 0 else ("↓ Неблагоприятно" if astro_signal < 0 else "→ Нейтрально")

        risk_factors = []
        if abs(tech_signal) < 0.2:
            risk_factors.append("Слабый технический сигнал")
        if abs(astro_signal) < 0.2:
            risk_factors.append("Неопределённая астрологическая картина")
        if abs(tech_signal - astro_signal) > 0.4:
            risk_factors.append("Расхождение техники и астрологии")
        if not risk_factors:
            risk_factors.append("Классические рыночные риски")

        report = f"""=== SYNTHESIS REPORT ===
Инструмент: {state.symbol}
Таймфрейм: {state.timeframe}
Дата: {state.analysis_timestamp_utc}

=== TECHNICAL SIGNALS ===
Сигнал: {tech_dir} (score: {tech_signal:+.2f})

=== ASTRO SIGNALS ===
Сигнал: {astro_dir} (score: {astro_signal:+.2f})

=== FINAL RECOMMENDATION ===
Action: {action.value}
Confidence: {state.synthesis.confidence.value.upper() if state.synthesis else 'N/A'}
Score: {final_score:+.2f} / 1.0

=== LEVELS ===
Entry: ${levels['entry']}
Stop Loss: ${levels['stop']}
Target 1: ${levels['target1']}
Target 2: ${levels['target2']}

=== RISK FACTORS ===
{chr(10).join(f"• {r}" for r in risk_factors)}

=== ASTRO-TECH CORRELATION ===
{self._describe_correlation(tech_signal, astro_signal)}

⚠️ Ограничения: Система — интеллектуальный помощник, а не автоматический торговый робот.
Решение принимает человек. Прошлые результаты не гарантируют будущих.
"""
        return report
