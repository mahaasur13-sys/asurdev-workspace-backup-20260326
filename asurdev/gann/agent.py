"""
Gann Agent — asurdev Sentinel
"""
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import asdict

from agents.base import BaseAgent, AgentResponse
from .square9 import Square9, get_square9, Square9Result
from .death_zones import DeathZones, get_death_zones


class GannAgent(BaseAgent):
    """Gann analysis - Square of 9, Death Zones"""
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Gann",
            system_prompt="Ты — эксперт по методам Ганна.",
            **kwargs
        )
        self.square9 = get_square9()
        self.death_zones = get_death_zones()
    
    def _parse_response(self, raw: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=30,
            summary=raw[:200]
        )
    
    def _result_to_dict(self, result) -> Dict:
        """Convert Square9Result to dict"""
        if isinstance(result, Square9Result):
            return {
                "levels": result.levels,
                "angles": result.angles,
                "cardinal_cross": result.cardinal_cross,
                "fixed_cross": result.fixed_cross,
                "death_zones_days": result.death_zones_days
            }
        return result if isinstance(result, dict) else {}
    
    async def analyze_impl(self, context: Dict[str, Any]) -> AgentResponse:
        """Run Gann analysis"""
        price = context.get("current_price", 0)
        if price <= 0:
            return AgentResponse(
                agent_name=self.name,
                signal="NEUTRAL",
                confidence=0,
                summary="No price data"
            )
        
        symbol = context.get("symbol", "BTC")
        
        # Square of 9
        sq_result = self.square9.calculate_levels(price, size=100)
        sq_dict = self._result_to_dict(sq_result)
        
        # Death Zones
        today = datetime.now().strftime("%Y-%m-%d")
        upcoming = self.death_zones.get_upcoming(today, days_ahead=30)
        
        # BTC targets
        btc_targets = {}
        if symbol == "BTC" and sq_dict.get("levels"):
            levels = sq_dict["levels"]
            btc_targets = {
                "support_1": levels[0] * 0.95,
                "resistance_1": levels[0] * 1.05
            }
        
        return AgentResponse(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=35,
            summary=f"Square9: {len(sq_dict.get('levels', []))} levels | Death zones: {len(upcoming)} upcoming",
            details={
                "square9": sq_dict,
                "death_zones": upcoming,
                "btc_targets": btc_targets
            }
        )


def get_gann_agent() -> GannAgent:
    """Factory function"""
    return GannAgent()
