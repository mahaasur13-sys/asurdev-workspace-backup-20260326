"""
EventTimingAgent — General Timing.
Общий тайминг событий (не элекция).
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class EventTimingAgent(BaseAgent):
    """EventTimingAgent — общий тайминг событий. Вес: 0.07"""
    def __init__(self):
        super().__init__(
            name="EventTimingAgent",
            system_prompt="Event Timing — general timing without election"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        event_type = context.get("event_type", "general")
        now = datetime.utcnow()
        
        windows = await self._find_timing_windows(event_type, now)
        
        if windows:
            best = windows[0]
            return AgentResponse(
                agent_name=self.name, signal=Signal.LONG, confidence=best["score"],
                reasoning=f"Best timing for {event_type}: {best['datetime']}",
                sources=["event_timing.md"],
                metadata={"event_type": event_type, "best_window": best, "all_windows": windows[:3]},
            )
        
        return AgentResponse(
            agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.4,
            reasoning=f"No optimal timing found for {event_type}",
            sources=["event_timing.md"],
            metadata={"event_type": event_type},
        )

    async def _find_timing_windows(self, event_type: str, start: datetime) -> List[Dict]:
        windows = []
        for h in range(24):
            dt = start + timedelta(hours=h)
            try:
                eph = swiss_ephemeris(
                    date=dt.strftime("%Y-%m-%d"),
                    time=dt.strftime("%H:%M:%S"),
                    compute_panchanga=False
                )
            except Exception:
                continue
            
            moon = eph.get("planets", {}).get("moon", {}).get("sign", "")
            if moon in ["Cancer", "Leo", "Sagittarius", "Pisces"]:
                windows.append({
                    "datetime": dt.isoformat(),
                    "score": 0.65,
                    "moon_sign": moon,
                })
        
        windows.sort(key=lambda x: x["score"], reverse=True)
        return windows[:5]
