"""
AstroFin Sentinel v5 — Directional Agents (Bull/Bear)
"""

import asyncio
from agents.base_agent import BaseAgent, AgentResponse, SignalDirection


class BullResearcherAgent(BaseAgent[AgentResponse]):
    """Bull researcher — ищет бычий кейс. Вес: 15%."""

    def __init__(self):
        super().__init__(
            name="BullResearcher",
            instructions_path="agents/BullResearcher_instructions.md",
            domain="trading",
            weight=0.15,
        )

    async def run(self, state: dict) -> AgentResponse:
        # Stub — requires real fundamental/news analysis
        return AgentResponse(
            agent_name="BullResearcher",
            signal=SignalDirection.NEUTRAL,
            confidence=0.35,
            reasoning="Bull researcher not yet implemented — requires news/sentiment API integration",
            sources=[],
        )


class BearResearcherAgent(BaseAgent[AgentResponse]):
    """Bear researcher — ищет медвежий кейс. Вес: 15%."""

    def __init__(self):
        super().__init__(
            name="BearResearcher",
            instructions_path="agents/BearResearcher_instructions.md",
            domain="trading",
            weight=0.15,
        )

    async def run(self, state: dict) -> AgentResponse:
        # Stub
        return AgentResponse(
            agent_name="BearResearcher",
            signal=SignalDirection.NEUTRAL,
            confidence=0.35,
            reasoning="Bear researcher not yet implemented — requires news/sentiment API integration",
            sources=[],
        )


async def run_bull_researcher(state: dict) -> dict:
    agent = BullResearcherAgent()
    result = await agent.run(state)
    return {"bull_signal": result.to_dict()}


async def run_bear_researcher(state: dict) -> dict:
    agent = BearResearcherAgent()
    result = await agent.run(state)
    return {"bear_signal": result.to_dict()}
