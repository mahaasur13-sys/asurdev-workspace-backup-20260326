"""
Market Analyst Agent — Technical Analysis Node
================================================
Агент технического анализа для AstroFin Sentinel.

Протокол:
1. Получает symbol + timeframe из SentinelState
2. Получает market data (RSI, MACD, Bollinger, support/resistance)
3. Выдаёт 3 сценария + направление
4. При незнакомых паттернах → RAG search
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agents.base.base_agent import (
    BaseAgent,
    SentinelState,
    AgentResult,
    RawMarketData,
    Confidence,
    Action,
)


class MarketAnalystAgent(BaseAgent):
    """
    Технический аналитик.
    
    Использует паттерны и индикаторы из базы знаний.
    При незнакомом паттерне — запрос к RAG.
    """

    def __init__(self, kb_path: str = "knowledge_base"):
        super().__init__(
            agent_id="market_analyst",
            agent_role="market_analyst",
            instructions_path=None,
            kb_path=kb_path,
        )

    def execute(self, state: SentinelState) -> AgentResult:
        """
        Выполняет технический анализ.
        
        Args:
            state: SentinelState с symbol, timeframe и market данными
            
        Returns:
            AgentResult с findings, narrative и action_recommendation
        """
        symbol = state.symbol.upper()
        timeframe = state.timeframe
        market = state.market

        errors = []
        rag_queries = []
        chunks_used = []

        # ── 1. Проверка данных ──────────────────────────────
        if not market:
            return AgentResult(
                agent_id=self.agent_id,
                agent_role=self.agent_role,
                status="error",
                errors=["No market data in state"],
                knowledge_sources=[],
            )

        # ── 2. Анализ паттернов (с RAG при необходимости) ──
        rsi = market.rsi
        macd = market.macd_signal
        trend = market.trend

        findings = {
            "symbol": symbol,
            "timeframe": timeframe,
            "price": market.price,
            "volume_24h": market.volume_24h,
            "change_24h": market.change_24h,
            "rsi": rsi,
            "macd_signal": macd,
            "trend": trend,
            "support": market.support,
            "resistance": market.resistance,
        }

        # ── 3. Определение 3 сценариев ──────────────────────
        scenarios = self._analyze_scenarios(market)
        findings["scenarios"] = scenarios

        # ── 4. Направление ─────────────────────────────────
        direction = self._determine_direction(trend, rsi, macd)
        findings["direction"] = direction

        # ── 5. Формирование нарратива ──────────────────────
        narrative = self._build_narrative(symbol, timeframe, findings)

        # ── 6. Confidence и Action ─────────────────────────
        confidence, action = self._get_confidence_and_action(findings)

        return AgentResult(
            agent_id=self.agent_id,
            agent_role=self.agent_role,
            status="success",
            findings=findings,
            narrative=narrative,
            confidence=confidence,
            action_recommendation=action,
            metadata={
                "price": market.price,
                "rsi": rsi,
                "trend": trend,
            },
            knowledge_sources=[c["id"] for c in chunks_used],
            errors=errors,
        )

    def _analyze_scenarios(self, market: RawMarketData) -> dict:
        """Формирует 3 сценария."""
        price = market.price
        support = market.support
        resistance = market.resistance
        rsi = market.rsi
        macd = market.macd_signal

        # Бычий сценарий
        bull_case = {
            "scenario": "бычий",
            "probability": 0.30,
            "trigger": "Пробой {r} с подтверждённым объёмом".format(r=resistance),
            "target": round(resistance * 1.05, 2),
            "stop_loss": round(price * 0.97, 2),
        }

        # Медвежий сценарий
        bear_case = {
            "scenario": "медвежий",
            "probability": 0.25,
            "trigger": "Пробой {s} с дивергенцией RSI".format(s=support),
            "target": round(support * 0.95, 2),
            "stop_loss": round(price * 1.03, 2),
        }

        # Нейтральный
        neutral_case = {
            "scenario": "нейтральный",
            "probability": 0.45,
            "range": [round(support, 2), round(resistance, 2)],
            "note": "Консолидация до прорыва",
        }

        return {
            "bull": bull_case,
            "bear": bear_case,
            "neutral": neutral_case,
        }

    def _determine_direction(self, trend: str, rsi: float, macd: str) -> str:
        """Определяет краткосрочное направление."""
        bullish_signals = 0
        bearish_signals = 0

        # Тренд
        if trend == "uptrend":
            bullish_signals += 2
        elif trend == "downtrend":
            bearish_signals += 2

        # RSI
        if rsi < 30:
            bullish_signals += 1
        elif rsi > 70:
            bearish_signals += 1

        # MACD
        if macd == "bullish":
            bullish_signals += 1
        elif macd == "bearish":
            bearish_signals += 1

        if bullish_signals > bearish_signals:
            return "bullish"
        elif bearish_signals > bullish_signals:
            return "bearish"
        return "neutral"

    def _build_narrative(self, symbol: str, timeframe: str, findings: dict) -> str:
        """Строит narrative для Synthesizer."""
        price = findings["price"]
        rsi = findings["rsi"]
        trend = findings["trend"]
        direction = findings["direction"]
        support = findings["support"]
        resistance = findings["resistance"]

        narrative = f"""**{symbol} | {timeframe}**

Техническая картина:
• Цена: ${price}
• Тренд: {trend.upper()}
• RSI (14): {rsi:.1f}
• Направление: {direction.upper()}

Уровни:
• Support: ${support}
• Resistance: ${resistance}

Сценарии:
• Бычий: {findings['scenarios']['bull']['trigger']} → ${findings['scenarios']['bull']['target']}
• Медвежий: {findings['scenarios']['bear']['trigger']} → ${findings['scenarios']['bear']['target']}
• Нейтральный: диапазон ${findings['scenarios']['neutral']['range'][0]}–${findings['scenarios']['neutral']['range'][1]}
"""
        return narrative

    def _get_confidence_and_action(self, findings: dict) -> tuple[Confidence, Action]:
        """Определяет confidence и рекомендуемое действие."""
        direction = findings["direction"]
        rsi = findings["rsi"]

        if direction == "bullish" and 30 < rsi < 70:
            confidence = Confidence.HIGH
            action = Action.HOLD
        elif direction == "bearish" and rsi > 70:
            confidence = Confidence.MEDIUM
            action = Action.HOLD
        else:
            confidence = Confidence.MEDIUM
            action = Action.HOLD

        return confidence, action
