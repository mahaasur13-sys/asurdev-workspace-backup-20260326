"""
AstroFin Sentinel v5 — ElectoralAgent
Electional astrology for trading entry timing.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection


class ElectoralAgent(BaseAgent[AgentResponse]):
    """
    ElectoralAgent — Muhurta specialist for trading.
    
    Responsibilities:
    1. Scan election windows (today/week/month)
    2. Calculate Muhurta scores
    3. Avoid bad periods (Marana, Vyatipata, Rahukaal)
    4. Recommend optimal entry windows
    """
    
    def __init__(self):
        super().__init__(
            name="ElectoralAgent",
            instructions_path="agents/ElectoralAgent_instructions.md",
            domain="astrology",
            weight=0.10,
        )
    
    async def run(self, state: dict) -> AgentResponse:
        """
        Scan for best trading muhurta.
        
        Returns recommendation: ENTER / WAIT / AVOID
        """
        from astrology.vedic import (
            get_current_nakshatra,
            get_choghadiya,
            get_rahukaal,
            is_good_muhurta,
        )
        
        now = datetime.utcnow()
        symbol = state.get("symbol", "BTCUSDT")
        
        # Current state
        current_nakshatra = get_current_nakshatra(now)
        current_choghadiya = get_choghadiya(now)
        
        # Scan next 24 hours for best window
        best_window = None
        best_score = 0
        
        for hour_offset in range(24):
            check_time = now + timedelta(hours=hour_offset)
            ch = get_choghadiya(check_time)
            nak = get_current_nakshatra(check_time)
            
            # Calculate muhurta score
            score = self._calculate_muhurta_score(ch, nak)
            
            if score > best_score:
                best_score = score
                best_window = {
                    "start": check_time,
                    "end": check_time + timedelta(hours=1.5),
                    "choghadiya": ch,
                    "nakshatra": nak,
                    "score": score,
                }
        
        # Determine recommendation
        if current_choghadiya["name"] in ["Marana", "Vyatipata", "Parivesha"]:
            recommendation = SignalDirection.AVOID
            confidence = 0.75
            reasoning = (
                f"Current Choghadiya: {current_choghadiya['name']} — "
                f"Marana period. Trading NOT recommended. "
                f"Next favorable window: {best_window['start'].strftime('%H:%M')} "
                f"({best_window['choghadiya']['name']})"
            )
        elif best_window["score"] >= 7:
            recommendation = SignalDirection.LONG
            confidence = best_window["score"] / 10.0
            reasoning = (
                f"Best window found: {best_window['start'].strftime('%H:%M')}–"
                f"{best_window['end'].strftime('%H:%M')} "
                f"({best_window['choghadiya']['name']}, "
                f"Nakshatra: {best_window['nakshatra']['name']}). "
                f"Muhurta Score: {best_window['score']:.1f}/10"
            )
        else:
            recommendation = SignalDirection.NEUTRAL
            confidence = 0.45
            reasoning = (
                f"No strong muhurta in next 24h. "
                f"Best available: {best_window['choghadiya']['name']} "
                f"at {best_window['start'].strftime('%H:%M')} "
                f"(score: {best_window['score']:.1f}/10)"
            )
        
        return AgentResponse(
            agent_name="ElectoralAgent",
            signal=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            sources=["astrology/choghadiya.md", "astrology/muhurta.md"],
            metadata={
                "current_choghadiya": current_choghadiya,
                "current_nakshatra": current_nakshatra,
                "best_window": best_window,
                "symbol": symbol,
            },
        )
    
    def _calculate_muhurta_score(self, choghadiya: dict, nakshatra: dict) -> float:
        """Calculate 0-10 muhurta score."""
        score = 5.0  # Base
        
        # Choghadiya adjustments
        choghadiya_scores = {
            "Amrita": +3.0,      # Best
            "Shubha": +2.0,     # Good
            "Labha": +1.5,      # Profitable
            "Rog": -2.0,        # Disease
            "Mrityu": -3.0,     # Death
            "Marana": -3.0,     # Deadly
            "Vyatipata": -2.5,  # Danger
            "Parivesha": -2.0,  # Trouble
        }
        score += choghadiya_scores.get(choghadiya["name"], 0)
        
        # Nakshatra adjustments
        nakshatra_quality = nakshatra.get("quality", "neutral")
        nak_scores = {
            "excellent": +1.5,
            "good": +1.0,
            "neutral": 0,
            "bad": -1.0,
            "worst": -1.5,
        }
        score += nak_scores.get(nakshatra_quality, 0)
        
        return max(0, min(10, score))


# ─── Convenience runner ───────────────────────────────────────────────────────

async def run_electoral_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = ElectoralAgent()
    result = await agent.run(state)
    return {"electoral_signal": result.to_dict()}
