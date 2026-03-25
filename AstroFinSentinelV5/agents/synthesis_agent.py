"""
AstroFin Sentinel v5 — Synthesis Agent
AstroCouncil: координатор всех агентов, финальный синтез.
Вес в финальном сигнале = 100% (координатор)
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection


# ─── Финальные веса агентов (сумма = 100%) ────────────────────────────────
# По спецификации пользователя:

AGENT_WEIGHTS = {
    # Фундаментал + Макро
    "FundamentalAgent": 0.20,   # Фундаментальный анализ
    "MacroAgent": 0.15,         # Макроэкономика
    
    # Quant/AI
    "QuantAgent": 0.20,        # ML + бэктестирование
    
    # Options Flow
    "OptionsFlowAgent": 0.15,   # Gamma exposure, unusual activity
    
    # Sentiment
    "SentimentAgent": 0.10,     # Новости, соцсети
    "BullResearcher": 0.05,    # Бычий нарратив + сильные астро факторы
    "BearResearcher": 0.05,    # Медвежий нарратив + рисковые факторы
    
    # Technical (фильтр)
    "TechnicalAgent": 0.10,    # RSI, MACD, Bollinger
}

# AstroCouncil — координатор, получает 100% на финальном этапе
# Его суб-агенты (BradleyAgent, ElectoralAgent, TimeWindowAgent)
# объединяются в блок Astro и суммируются в SynthesisAgent


class SynthesisAgent(BaseAgent[AgentResponse]):
    """
    SynthesisAgent = Координатор финального синтеза.
    
    Получает сигналы от ВСЕХ аналитических агентов,
    применяет гибридное взвешивание,
    формирует финальный торговый сигнал.
    """

    def __init__(self):
        super().__init__(
            name="SynthesisAgent",
            instructions_path="agents/SynthesisAgent_instructions.md",
            domain=None,
            weight=0.0,
        )
    
    async def run(self, state: dict) -> AgentResponse:
        """
        Финальный синтез всех агентов.
        
        Args:
            state: SentinelState с all_signals
            
        Returns:
            AgentResponse с финальным сигналом
        """
        all_signals = state.get("all_signals", [])
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")
        
        # ─── 1. Группируем по категориям ────────────────────────────────
        categories = self._group_by_category(all_signals)
        
        # ─── 2. Проверяем конфликты ────────────────────────────────────
        conflicts = self._detect_conflicts(categories)
        
        # ─── 3. Считаем взвешенные оценки ───────────────────────────────
        direction, confidence, reasoning = self._synthesize(
            categories, conflicts, symbol
        )
        
        # ─── 4. Формируем breakdown ────────────────────────────────────
        breakdown = self._format_breakdown(categories)
        
        # ─── 5. Entry zones, targets, stop ────────────────────────────
        meta = self._calculate_levels(direction, current_price)
        
        return AgentResponse(
            agent_name="SynthesisAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=self._collect_sources(all_signals),
            metadata={
                "symbol": symbol,
                "timeframe": timeframe,
                "current_price": current_price,
                "breakdown": breakdown,
                "conflicts": conflicts,
                "agent_weights": AGENT_WEIGHTS,
                **meta,
            },
        )
    
    def _group_by_category(self, signals: list) -> Dict[str, list]:
        """Группирует сигналы по категориям."""
        category_map = {
            "AstroCouncil": "astro",
            "ElectoralAgent": "astro",
            "BradleyAgent": "astro",
            "TimeWindowAgent": "astro",
            "FundamentalAgent": "fundamental",
            "InsiderAgent": "fundamental",
            "MacroAgent": "macro",
            "QuantAgent": "quant",
            "MLPredictorAgent": "quant",
            "OptionsFlowAgent": "options",
            "BullResearcher": "sentiment",
            "BearResearcher": "sentiment",
            "SentimentAgent": "sentiment",
            "TechnicalAgent": "technical",
            "MarketAnalyst": "technical",
            "GannAgent": "technical",
            "ElliotAgent": "technical",
        }
        
        categories = {
            "astro": [], "fundamental": [], "macro": [],
            "quant": [], "options": [], "sentiment": [], "technical": [],
        }
        
        for sig in signals:
            agent = sig.get("agent_name", "")
            cat = category_map.get(agent, "other")
            if cat in categories:
                categories[cat].append(sig)
        
        return categories
    
    def _detect_conflicts(self, categories: Dict[str, list]) -> list:
        """Определяет конфликты между категориями."""
        conflicts = []
        
        def get_direction(signals):
            if not signals:
                return "NEUTRAL"
            votes = [s.get("signal", "NEUTRAL").upper() for s in signals]
            long_v = votes.count("LONG") + votes.count("BUY") + votes.count("STRONG_BUY")
            short_v = votes.count("SHORT") + votes.count("SELL") + votes.count("STRONG_SELL")
            return "LONG" if long_v > short_v else "SHORT" if short_v > long_v else "NEUTRAL"
        
        astro_dir = get_direction(categories.get("astro", []))
        fund_dir = get_direction(categories.get("fundamental", []))
        quant_dir = get_direction(categories.get("quant", []))
        
        # Конфликт Astro vs Fundamental+Quant
        if astro_dir != "NEUTRAL" and astro_dir != "NEUTRAL":
            other = [fund_dir, quant_dir]
            non_neutral = [d for d in other if d != "NEUTRAL"]
            if non_neutral and astro_dir != non_neutral[0]:
                conflicts.append({
                    "type": "astro_vs_fundamental_quant",
                    "astro": astro_dir,
                    "fundamental": fund_dir,
                    "quant": quant_dir,
                    "resolution": "reduce_astro_weight_by_30pct",
                })
        
        return conflicts
    
    def _synthesize(
        self, categories: Dict[str, list], conflicts: list, symbol: str
    ) -> tuple:
        """Финальный синтез."""
        
        # Эффективные веса
        eff = {k: v for k, v in AGENT_WEIGHTS.items()}
        
        # Применяем разрешение конфликтов
        if conflicts:
            for c in conflicts:
                if c["type"] == "astro_vs_fundamental_quant":
                    # Astro -30%, Fundamental +18%, Quant +12%
                    eff["AstroCouncil"] *= 0.70
                    eff["FundamentalAgent"] *= 1.18
                    eff["QuantAgent"] *= 1.12
        
        # Считаем взвешенные оценки
        scores = {k: 0.0 for k in ["LONG", "SHORT", "NEUTRAL", "AVOID"]}
        
        for agent, weight in eff.items():
            # Находим сигнал агента во всех сигналах
            # (Это упрощение — в реальном коде нужно передавать все сигналы)
            pass
        
        # Простое голосование
        direction, confidence, reasoning = self._vote(categories)
        
        return direction, confidence, reasoning
    
    def _vote(self, categories: Dict[str, list]) -> tuple:
        """Простое голосование по категориям."""
        
        cat_weights = {
            "astro": 0.25,
            "fundamental": 0.20,
            "macro": 0.15,
            "quant": 0.20,
            "options": 0.15,
            "sentiment": 0.10,
            "technical": 0.10,
        }
        
        long_w = 0.0
        short_w = 0.0
        neutral_w = 0.0
        
        for cat, signals in categories.items():
            if not signals:
                continue
            w = cat_weights.get(cat, 0.10)
            
            for sig in signals:
                conf = sig.get("confidence", 0.5)
                direction = sig.get("signal", "NEUTRAL").upper()
                
                if direction in ("LONG", "BUY", "STRONG_BUY"):
                    long_w += conf * w
                elif direction in ("SHORT", "SELL", "STRONG_SELL"):
                    short_w += conf * w
                else:
                    neutral_w += conf * w
        
        total = long_w + short_w + neutral_w
        if total > 0:
            long_pct = long_w / total
            short_pct = short_w / total
        else:
            long_pct = short_pct = 0.5
        
        if long_pct > 0.55:
            direction = SignalDirection.LONG
            confidence = min(0.92, 0.5 + long_pct * 0.4)
            reasoning = f"Long consensus: {long_pct*100:.0f}% weighted votes"
        elif short_pct > 0.55:
            direction = SignalDirection.SHORT
            confidence = min(0.92, 0.5 + short_pct * 0.4)
            reasoning = f"Short consensus: {short_pct*100:.0f}% weighted votes"
        else:
            direction = SignalDirection.NEUTRAL
            confidence = 0.5
            reasoning = f"No strong consensus: Long {long_pct*100:.0f}% | Short {short_pct*100:.0f}%"
        
        return direction, confidence, reasoning
    
    def _format_breakdown(self, categories: Dict[str, list]) -> str:
        """Форматирует breakdown."""
        lines = []
        cat_weights = {
            "astro": 0.25, "fundamental": 0.20, "macro": 0.15,
            "quant": 0.20, "options": 0.15, "sentiment": 0.10, "technical": 0.10,
        }
        
        for cat, signals in categories.items():
            w = cat_weights.get(cat, 0.0)
            if not signals:
                lines.append(f"  [{cat.upper():12s}] NEUTRAL    [░░░░░░░░░░]   0.0% w={w:.2f} (no signals)")
                continue
            
            conf_avg = sum(s.get("confidence", 0) for s in signals) / len(signals)
            votes = [s.get("signal", "NEUTRAL").upper() for s in signals]
            long_v = votes.count("LONG") + votes.count("BUY")
            short_v = votes.count("SHORT") + votes.count("SELL")
            
            direction = "LONG ▲" if long_v > short_v else "SHORT ▼" if short_v > long_v else "NEUT"
            
            bar = "█" * int(conf_avg * 10) + "░" * (10 - int(conf_avg * 10))
            agents = ", ".join(s.get("agent_name", "?") for s in signals)
            
            lines.append(f"  [{cat.upper():12s}] {direction:12s} [{bar}] {conf_avg*100:5.1f}% w={w:.2f} ({agents})")
        
        return "\n".join(lines)
    
    def _collect_sources(self, signals: list) -> list:
        """Собирает источники."""
        sources = []
        for sig in signals:
            for src in sig.get("sources", []):
                if src and isinstance(src, str):
                    sources.append(src)
        return list(set(sources))
    
    def _calculate_levels(self, direction: SignalDirection, price: float) -> dict:
        """Рассчитывает entry zones, targets, stop."""
        
        if direction == SignalDirection.LONG:
            entry_low = price * 0.985
            entry_high = price * 1.015
            stop = price * 0.95
            targets = [price * 1.03, price * 1.06, price * 1.10]
            position = 0.05
        elif direction == SignalDirection.SHORT:
            entry_low = price * 0.985
            entry_high = price * 1.015
            stop = price * 1.05
            targets = [price * 0.97, price * 0.94, price * 0.90]
            position = 0.03
        else:
            entry_low = price * 0.98
            entry_high = price * 1.02
            stop = price * 0.95
            targets = [price * 1.02, price * 1.05, price * 1.08]
            position = 0.02
        
        return {
            "entry_zone": (entry_low, entry_high),
            "stop_loss": stop,
            "targets": targets,
            "position_size": position,
        }


# ─── Convenience runner ──────────────────────────────────────────────────

async def run_synthesis_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = SynthesisAgent()
    result = await agent.run(state)
    return {"synthesis_signal": result.to_dict()}
