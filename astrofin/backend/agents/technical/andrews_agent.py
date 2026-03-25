"""Andrews Pitchfork Agent — Линии Эндрюса. Вес: 6%"""
from ..base_agent import BaseAgent, AgentResponse, Signal


class AndrewsAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="AndrewsAgent", system_prompt="Andrews Pitchfork analysis")

    async def run(self, context: dict) -> AgentResponse:
        return AgentResponse(
            agent_name="AndrewsAgent",
            signal=Signal.NEUTRAL,
            confidence=0.50,
            reasoning="Andrews: requires 3 pivot points",
            metadata={"method": "Andrews Pitchfork", "weight": 0.06}
        )


class TrendlineAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TrendlineAgent", system_prompt="Trendlines analysis")

    async def run(self, context: dict) -> AgentResponse:
        return AgentResponse(
            agent_name="TrendlineAgent",
            signal=Signal.NEUTRAL,
            confidence=0.45,
            reasoning="Trendline analysis",
            metadata={"method": "Trendlines", "weight": 0.03}
        )
