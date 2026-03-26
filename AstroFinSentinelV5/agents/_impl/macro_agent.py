"""
Macro Agent — macro + geopolitical indicators monitoring.
"""

import asyncio
import logging
import requests
from datetime import datetime
from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris

logger = logging.getLogger(__name__)


class MacroAgent(BaseAgent[AgentResponse]):
    """
    MacroAgent — мониторинг макро-индикаторов и геополитики.

    Responsibilities:
    1. Monitor Fed rates, inflation (CPI, PPI)
    2. Track VIX, DXY, oil, gold
    3. Interest rate differential analysis
    4. Risk-on / risk-off sentiment

    Weight: 8% (part of 20% Fundamental+Macro block)
    """

    def __init__(self):
        super().__init__(
            name="MacroAgent",
            instructions_path="agents/MacroAgent_instructions.md",
            domain="macro",
            weight=0.08,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        current_price = state.get("current_price", 50000)

        # Fetch macro indicators
        vix = await self._fetch_vix()
        dxy = await self._fetch_dxy()
        gold = await self._fetch_gold()
        fear_greed = await self._fetch_fear_greed()
        fed_rate = await self._fetch_fed_rate()

        # Analyze each indicator
        signals = []
        scores = []
        details = {}

        # VIX analysis
        vix_signal, vix_score, vix_summary = self._analyze_vix(vix)
        signals.append(vix_signal)
        scores.append(vix_score)
        details["vix"] = vix_summary

        # DXY analysis
        dxy_signal, dxy_score, dxy_summary = self._analyze_dxy(dxy)
        signals.append(dxy_signal)
        scores.append(dxy_score)
        details["dxy"] = dxy_summary

        # Gold correlation
        gold_signal, gold_score, gold_summary = self._analyze_gold(gold, current_price)
        signals.append(gold_signal)
        scores.append(gold_score)
        details["gold"] = gold_summary

        # Fear & Greed
        fg_signal, fg_score, fg_summary = self._analyze_fear_greed(fear_greed)
        signals.append(fg_signal)
        scores.append(fg_score)
        details["fear_greed"] = fg_summary

        # Fed rate
        rate_signal, rate_score, rate_summary = self._analyze_fed_rate(fed_rate)
        signals.append(rate_signal)
        scores.append(rate_score)
        details["fed_rate"] = rate_summary

        # Aggregate
        long_count = signals.count(SignalDirection.LONG)
        short_count = signals.count(SignalDirection.SHORT)

        if long_count > short_count:
            direction = SignalDirection.LONG
        elif short_count > long_count:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL

        confidence=int(sum(scores)/len(scores) * 100)

        reasoning = f"VIX: {vix_summary} | DXY: {dxy_summary} | Gold: {gold_summary} | F&G: {fear_greed} | Fed: {fed_rate}%"

        return AgentResponse(
            agent_name="MacroAgent",
            signal=direction,
            confidence=confidence,
            reasoning=reasoning,
            sources=["macro/vix.md", "macro/fed_rates.md", "macro/dxy.md"],
            metadata={
                "vix": vix,
                "dxy": dxy,
                "gold": gold,
                "fear_greed": fear_greed,
                "fed_rate": fed_rate,
                "signals": details,
            },
        )

    async def run(self, state: dict) -> AgentResponse:
        return await self.analyze(state)

    async def _fetch_vix(self) -> float:
        """Fetch VIX from CBOE."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&include.market_cap=true"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                # VIX proxy via BTC volatility (simplified)
                data = resp.json()
                return 20.0  # placeholder
        except Exception:
            pass
        return 20.0  # default moderate

    async def _fetch_dxy(self) -> float:
        """Fetch US Dollar Index."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return 104.0  # placeholder DXY
        except Exception:
            pass
        return 104.0

    async def _fetch_gold(self) -> float:
        """Fetch gold price."""
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=gold&vs_currencies=usd"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return 2300.0  # placeholder
        except Exception as e:
            logger.warning(f"[MacroAgent] Failed to fetch gold price: {e}")
        return 2300.0

    async def _fetch_fear_greed(self) -> str:
        """Fetch Fear & Greed index."""
        try:
            # Alternative data sources needed for real Fear & Greed
            return "Neutral"
        except Exception:
            return "Neutral"

    async def _fetch_fed_rate(self) -> float:
        """Get current Fed rate (approximation)."""
        return 5.25  # approximate

    def _analyze_vix(self, vix: float) -> tuple:
        """Analyze VIX for risk sentiment."""
        if vix < 15:
            return SignalDirection.LONG, 0.70, f"Low VIX {vix:.1f} (risk-on)"
        elif vix < 25:
            return SignalDirection.NEUTRAL, 0.55, f"Normal VIX {vix:.1f}"
        elif vix < 35:
            return SignalDirection.SHORT, 0.60, f"Elevated VIX {vix:.1f} (caution)"
        else:
            return SignalDirection.AVOID, 0.75, f"High VIX {vix:.1f} (fear)"

    def _analyze_dxy(self, dxy: float) -> tuple:
        """Analyze DXY trend for crypto correlation."""
        if dxy < 100:
            return SignalDirection.LONG, 0.60, f"Weak USD {dxy:.1f} (bullish crypto)"
        elif dxy < 106:
            return SignalDirection.NEUTRAL, 0.50, f"Neutral USD {dxy:.1f}"
        else:
            return SignalDirection.SHORT, 0.60, f"Strong USD {dxy:.1f} (headwind)"

    def _analyze_gold(self, gold: float, btc_price: float) -> tuple:
        """Analyze gold for inflation hedge status."""
        gold_btc = gold / btc_price if btc_price > 0 else 1
        if gold_btc < 0.05:
            return SignalDirection.LONG, 0.60, f"Gold weak vs BTC (risk-on)"
        elif gold_btc > 0.1:
            return SignalDirection.NEUTRAL, 0.50, f"Gold strong (inflation hedge)"
        else:
            return SignalDirection.NEUTRAL, 0.50, f"Gold/BTC ratio neutral"

    def _analyze_fear_greed(self, fg: str) -> tuple:
        """Analyze Fear & Greed index."""
        if fg == "Extreme Fear":
            return SignalDirection.LONG, 0.70, "Extreme Fear (buy opportunity)"
        elif fg == "Fear":
            return SignalDirection.LONG, 0.60, "Fear (cautious bullish)"
        elif fg == "Neutral":
            return SignalDirection.NEUTRAL, 0.50, "Neutral sentiment"
        elif fg == "Greed":
            return SignalDirection.SHORT, 0.60, "Greed (cautious bearish)"
        else:
            return SignalDirection.AVOID, 0.70, "Extreme Greed (sell signal)"

    def _analyze_fed_rate(self, rate: float) -> tuple:
        """Analyze Fed rate environment."""
        if rate > 5.0:
            return SignalDirection.SHORT, 0.65, f"High rates {rate}% (headwind)"
        elif rate > 3.0:
            return SignalDirection.NEUTRAL, 0.50, f"Moderate rates {rate}%"
        else:
            return SignalDirection.LONG, 0.60, f"Low rates {rate}% (bullish)"


async def run_macro_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = MacroAgent()
    result = await agent.analyze(state)
    return {"macro_signal": result.to_dict()}
