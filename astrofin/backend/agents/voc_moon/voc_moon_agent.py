"""
VoidOfCourseMoonAgent — специализированный агент только по VoC Луны.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris, NAKSHATRAS

class VoidOfCourseMoonAgent(BaseAgent):
    """VoidOfCourseMoonAgent — анализ Void of Course Moon. Вес: 0.04"""
    VOC_PATTERNS = [
        "squares to planets",
        "oppositions to planets",
    ]

    def __init__(self):
        super().__init__(
            name="VoidOfCourseMoonAgent",
            system_prompt="Void of Course Moon analysis"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        now = datetime.utcnow()
        
        is_voc = await self._check_voc(now)
        
        # Find next VOC start and end
        next_voc = await self._find_next_voc(now)
        
        if is_voc:
            signal = Signal.AVOID
            confidence = 0.7
            reasoning = "Moon is currently Void of Course — avoid new beginnings"
        elif next_voc:
            signal = Signal.NEUTRAL
            confidence = 0.5
            reasoning = f"Next VOC starts at {next_voc['start']}"
        else:
            signal = Signal.NEUTRAL
            confidence = 0.6
            reasoning = "Moon is not Void of Course — favorable for new beginnings"

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=reasoning,
            sources=["voc_moon.md"],
            metadata={"is_voc": is_voc, "next_voc": next_voc},
        )

    async def _check_voc(self, dt: datetime) -> bool:
        """Check if Moon is currently Void of Course."""
        try:
            eph = swiss_ephemeris(
                date=dt.strftime("%Y-%m-%d"),
                time=dt.strftime("%H:%M:%S"),
                compute_panchanga=False
            )
        except Exception:
            return False
        
        moon_deg = eph.get("planets", {}).get("moon", {}).get("longitude", 0)
        moon_sign = int(moon_deg // 30)
        moon_deg_in_sign = moon_deg % 30
        
        # Simplified VoC check: last 1-2° of each sign
        return moon_deg_in_sign > 28.5

    async def _find_next_voc(self, start: datetime) -> Dict:
        """Find next VOID OF COURSE Moon period."""
        for h in range(24):
            dt = start + timedelta(hours=h)
            if await self._check_voc(dt):
                return {"start": dt.isoformat()}
        return None
