"""
Astro Agent — Vedic Astrology Node
==================================
Астрологический аналитик для AstroFin Sentinel.

Протокол:
1. Получает timestamp + lat/lon из SentinelState
2. Рассчитывает позиции через sweph
3. Интерпретирует Panjanga / Choghadiya / Muhurta
4. При редких комбинациях → RAG search
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agents.base.base_agent import (
    BaseAgent,
    SentinelState,
    AgentResult,
    RawAstroData,
    Confidence,
    Action,
)


class AstroAgent(BaseAgent):
    """
    Астрологический аналитик.

    Использует:
    - Swiss Ephemeris (swe) для расчёта позиций
    - Panchanga / Choghadiya / Muhurta из базы знаний
    - RAG для редких йог и комбинаций
    """

    def __init__(self, kb_path: str = "knowledge_base"):
        super().__init__(
            agent_id="astro",
            agent_role="astro",
            instructions_path=None,
            kb_path=kb_path,
        )

    def execute(self, state: SentinelState) -> AgentResult:
        """
        Выполняет астрологический анализ.

        Args:
            state: SentinelState с astro данными и analysis_timestamp_utc

        Returns:
            AgentResult с астрологической оценкой
        """
        errors = []
        rag_queries = []
        chunks_used = []

        # ── 1. Проверка данных ──────────────────────────────
        if not state.astro:
            return AgentResult(
                agent_id=self.agent_id,
                agent_role=self.agent_role,
                status="error",
                errors=["No astro data in state"],
                knowledge_sources=[],
            )

        astro = state.astro
        timestamp = state.analysis_timestamp_utc

        # ── 2. Оценка благоприятности ────────────────────────
        auspicious_score = self._calculate_auspicious_score(astro)

        # ── 3. Choghadiya анализ ────────────────────────────
        choghadiya_result = self._analyze_choghadiya(astro)
        if choghadiya_result["needs_rag"]:
            query = f"Choghadiya {astro.choghadiya_type} — правила интерпретации"
            chunks = self._rag_search(query)
            chunks_used.extend(chunks)
            rag_queries.append(query)

        # ── 4. Panjanga анализ ─────────────────────────────
        panjanga_result = self._analyze_panjanga(astro)
        if panjanga_result["needs_rag"]:
            query = f"{Nakshatra(astro.nakshatra).name} — характеристика для финансовых решений"
            chunks = self._rag_search(query)
            chunks_used.extend(chunks)
            rag_queries.append(query)

        # ── 5. Астрологический нарратив ─────────────────────
        narrative = self._build_narrative(astro, timestamp, auspicious_score, choghadiya_result, panjanga_result)

        # ── 6. Confidence и Action ─────────────────────────
        confidence = self._get_confidence(astro, auspicious_score)
        action = self._get_action(choghadiya_result, auspicious_score)

        findings = {
            "moon_sign": astro.moon_sign,
            "moon_degree": astro.moon_degree,
            "moon_phase": astro.moon_phase,
            "nakshatra": astro.nakshatra,
            "tithi": astro.tithi,
            "yoga": astro.yoga,
            "choghadiya_type": astro.choghadiya_type,
            "choghadiya_window": f"{astro.choghadiya_window_start} – {astro.choghadiya_window_end}",
            "auspicious_score": auspicious_score,
            "is_auspicious": astro.is_auspicious,
            "choghadiya_analysis": choghadiya_result,
            "panjanga_analysis": panjanga_result,
        }

        knowledge_sources_str = self._format_knowledge_sources(rag_queries, chunks_used)

        # Добавляем источники знаний в narrative
        full_narrative = f"{narrative}\n\n{knowledge_sources_str}"

        return AgentResult(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            status="success",
            findings=findings,
            narrative=full_narrative,
            confidence=confidence,
            action_recommendation=action,
            metadata={
                "timestamp_utc": timestamp,
                "auspicious_score": auspicious_score,
            },
            knowledge_sources=[c["id"] for c in chunks_used],
            errors=errors,
        )

    def _calculate_auspicious_score(self, astro: RawAstroData) -> int:
        """Оценивает общую благоприятность момента (1-10)."""
        score = 5  # базовый

        # Choghadiya
        good_types = ["amrita", "shubha", "labha"]
        if astro.choghadiya_type.lower() in good_types:
            score += 2
        elif astro.choghadiya_type.lower() in ["mrityu", "aranja"]:
            score -= 3

        # Накшатра (упрощённо)
        good_nakshatras = ["rohini", "mrigashirsha", "uttara", "uttara_phalguni", "shravana", "dhanishtha"]
        if astro.nakshatra.lower() in good_nakshatras:
            score += 1

        return max(1, min(10, score))

    def _analyze_choghadiya(self, astro: RawAstroData) -> dict:
        """Анализирует Choghadiya."""
        ch_type = astro.choghadiya_type.lower()
        needs_rag = ch_type not in ["amrita", "shubha", "labha", "mrityu", "aranja"]

        descriptions = {
            "amrita": "Лучшее время. Омоложение, духовность, исцеление.",
            "shubha": "Благоприятно для деловых начинаний и общения.",
            "labha": "Выгодно для финансов и приобретений.",
            "charana": "Нейтральное время для рутинных дел.",
            "dubia": "Неопределённое. Требует осторожности.",
            "krodha": "Неблагоприятно. Избегать важных решений.",
            "mrityu": "Критически неблагоприятно. Не начинать дела.",
            "aranja": "Неблагоприятно для коммерции и финансов.",
        }

        return {
            "type": astro.choghadiya_type,
            "description": descriptions.get(ch_type, f"Тип {ch_type} — требует дополнительного анализа"),
            "is_good": ch_type in ["amrita", "shubha", "labha"],
            "needs_rag": needs_rag,
        }

    def _analyze_panjanga(self, astro: RawAstroData) -> dict:
        """Анализирует Panjanga (5 факторов)."""
        needs_rag = astro.yoga.lower() in ["vitatha", "ganda", "vajra"]

        return {
            "nakshatra": astro.nakshatra,
            "tithi": astro.tithi,
            "yoga": astro.yoga,
            "karana": astro.karana,
            "needs_rag": needs_rag,
        }

    def _build_narrative(
        self,
        astro: RawAstroData,
        timestamp: str,
        auspicious_score: int,
        choghadiya_result: dict,
        panjanga_result: dict,
    ) -> str:
        """Строит астрологический нарратив."""
        ch = choghadiya_result

        narrative = f"""**Астрологический анализ**
Дата/Время (UTC): {timestamp}

Луна: {astro.moon_sign} {astro.moon_degree:.1f}° | Фаза: {astro.moon_phase}

Panjanga:
• Накшатра: {panjanga_result['nakshatra']}
• Тидхи: {astro.tithi}
• Йога: {astro.yoga}
• Карана: {astro.karana}

Choghadiya: [{ch['type']}] — {ch['description']}
Время окна: {astro.choghadiya_window_start} – {astro.choghadiya_window_end}

Оценка дня: {auspicious_score}/10
Астрологическая рекомендация: {"Благоприятно" if ch['is_good'] else "Осторожность"} для финансовых решений
"""
        return narrative

    def _get_confidence(self, astro: RawAstroData, auspicious_score: int) -> Confidence:
        """Определяет confidence астрологического сигнала."""
        if auspicious_score >= 8:
            return Confidence.HIGH
        elif auspicious_score >= 5:
            return Confidence.MEDIUM
        return Confidence.LOW

    def _get_action(self, choghadiya_result: dict, auspicious_score: int) -> Action:
        """Определяет рекомендуемое действие по астрологии."""
        if choghadiya_result["is_good"] and auspicious_score >= 7:
            return Action.HOLD
        elif auspicious_score < 4:
            return Action.SKIP
        return Action.HOLD


# ──────────────────────────────────────────────
# Вспомогательные enum'ы для типов данных
# ──────────────────────────────────────────────

from enum import Enum


class Nakshatra(Enum):
    ASHWINI = "ashwini"
    BHARINI = "bharini"
    KRITIKA = "kritika"
    ROHINI = "rohini"
    MRIGASHIRSHA = "mrigashirsha"
    ARDRA = "ardra"
    PUNARVASU = "punarvasu"
    PUSHYA = "pushya"
    ASHLESHA = "ashlesha"
    MAGHA = "magha"
    PURVA_PHALGUNI = "purva_phalguni"
    UTTARA_PHALGUNI = "uttara_phalguni"
    HASTA = "hasta"
    CHITRA = "chitra"
    SWATI = "swati"
    VISHAKHA = "vishakha"
    ANURADHA = "anuradha"
    JYESHTHA = "jyeshtha"
    MULA = "mula"
    PURVA_SHADHA = "purva_shadha"
    UTTARA_SHADHA = "uttara_shadha"
    SHRAVANA = "shravana"
    DHANISHTHA = "dhanishtha"
    SHATABHISHA = "shatabhisha"
    PURVA_BHADRAPADA = "purva_bhadrapada"
    UTTARA_BHADRAPADA = "uttara_bhadrapada"
    REVATI = "revati"
