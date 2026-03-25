"""Gann Agent — Уровни Ганна. Вес: 5%"""
from ..base_agent import BaseAgent, AgentResponse, Signal


class GannAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="GannAgent", system_prompt="Gann levels analysis")

    async def run(self, context: dict) -> AgentResponse:
        price = context.get("current_price", 50000)
        levels = self._calculate_gann_levels(price)
        current = self._find_current_level(price, levels)
        return AgentResponse(
            agent_name="GannAgent",
            signal=Signal.NEUTRAL,
            confidence=0.55,
            reasoning=f"Gann: at {current}",
            metadata={"method": "Gann Levels", "levels": levels, "weight": 0.05}
        )

    def _calculate_gann_levels(self, price: float) -> dict:
        levels = {}
        for i, mult in enumerate([0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875], 1):
            levels[f"S{i}"] = round(price * (1 - mult), 2)
            levels[f"R{i}"] = round(price * (1 + mult), 2)
        return levels

    def _find_current_level(self, price: float, levels: dict) -> str:
        for k, v in sorted([(k, v) for k, v in levels.items() if k.startswith("S")], key=lambda x: x[1], reverse=True):
            if price > v:
                return k
        return "S1"
