"""Cycle Agent - Timing Solution Integration"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from .base_agent import BaseAgent, AgentResponse

class TSParser:
    @staticmethod
    def find_latest_signal(signals_dir: Path, symbol: str) -> Optional[Dict]:
        if not signals_dir.exists():
            return None
        pattern = f"ts_{symbol.upper()}*"
        files = sorted(signals_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if files:
            try:
                with open(files[0], 'r') as f:
                    return json.load(f)
            except:
                pass
        return None


class CycleAgent(BaseAgent):
    def __init__(self, signals_dir: str = "/home/workspace/asurdevSentinel/data/ts_signals", **kwargs):
        super().__init__(name="CycleAgent", **kwargs)
        self.signals_dir = Path(signals_dir)
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        signal_data = TSParser.find_latest_signal(self.signals_dir, symbol)
        
        if signal_data:
            direction = signal_data.get("position", "FLAT")
            signal_map = {"LONG": "BULLISH", "SHORT": "BEARISH", "FLAT": "NEUTRAL"}
            return AgentResponse(
                agent_name="CycleAgent",
                signal=signal_map.get(direction, "NEUTRAL"),
                confidence=signal_data.get("confidence", 50),
                summary=f"TS {direction}",
                details=signal_data
            )
        
        hour = datetime.now().hour
        direction = "LONG" if 6 <= hour <= 12 else "SHORT" if 18 <= hour <= 23 else "FLAT"
        signal_map = {"LONG": "BULLISH", "SHORT": "BEARISH", "FLAT": "NEUTRAL"}
        
        return AgentResponse(
            agent_name="CycleAgent",
            signal=signal_map[direction],
            confidence=55,
            summary=f"Internal cycle: {direction}",
            details={"hour": hour, "source": "internal"}
        )
