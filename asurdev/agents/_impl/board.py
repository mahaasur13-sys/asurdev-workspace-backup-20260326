"""
Board of Directors — Alternative Orchestrator
==============================================

Multi-agent Board of Directors with real-time voting.
Provides an alternative to LangGraph for simpler use cases.

Based on asurdev-sentinel (P2) BoardOfDirectors.
"""

import asyncio
import json
import re
from typing import Any, AsyncGenerator, Literal, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..types import Signal, AgentResponse
from ..llm_factory import get_llm_config, ANALYST_PROMPT, ASTROLOGER_PROMPT, SYNTHESIZER_PROMPT, RISK_MANAGER_PROMPT


class Recommendation(str, Enum):
    """Investment recommendation types."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WAIT = "WAIT"
    NEUTRAL = "NEUTRAL"


class RiskLevel(str, Enum):
    """Risk level assessment."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass
class AgentVote:
    """A single agent's vote."""
    agent_name: str
    recommendation: Recommendation
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BoardVerdict:
    """Final board verdict with voting results."""
    recommendation: Recommendation
    confidence: float
    time_horizon: str
    thesis: str
    risk_level: RiskLevel
    votes: list[AgentVote]
    dissent: list[str]
    timestamp: datetime = field(default_factory=datetime.now)
    elapsed_seconds: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation": self.recommendation.value,
            "confidence": self.confidence,
            "time_horizon": self.time_horizon,
            "thesis": self.thesis,
            "risk_level": self.risk_level.value,
            "votes": [
                {
                    "agent": v.agent_name,
                    "recommendation": v.recommendation.value,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                }
                for v in self.votes
            ],
            "dissent": self.dissent,
            "timestamp": self.timestamp.isoformat(),
            "elapsed_seconds": self.elapsed_seconds,
        }


class BoardOfDirectors:
    """
    Multi-agent Board of Directors with voting.
    
    Architecture:
    - Analyst, Astrologer, Risk Manager present initial views
    - Optional: Agents debate/argue with each other
    - Chairman (Synthesizer) calls for vote
    - Votes are tallied and weighted by confidence
    - Final verdict issued
    
    Supports two modes:
    1. ROUND_ROBIN - Each agent speaks once in order
    2. DEBATE - Agents can respond to each other
    """

    def __init__(
        self,
        provider: str = "auto",
        mode: Literal["round_robin", "debate"] = "debate",
        max_rounds: int = 4,
        include_astrology: bool = True,
        include_risk_manager: bool = True,
    ):
        self.provider = provider
        self.mode = mode
        self.max_rounds = max_rounds
        self.include_astrology = include_astrology
        self.include_risk_manager = include_risk_manager
        
        self.llm_config = get_llm_config(provider)
        self.agents: list = []
        self.votes: list[AgentVote] = []
        self.turn_log: list[dict[str, Any]] = []

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def initialize(self):
        """Initialize agents."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        client = self._create_client()
        self.agents = []
        
        # Create Analyst
        self.agents.append({
            "name": "Market_Analyst",
            "system": ANALYST_PROMPT,
            "client": client,
        })
        
        # Create Astrologer if enabled
        if self.include_astrology:
            self.agents.append({
                "name": "Astrological_Advisor",
                "system": ASTROLOGER_PROMPT,
                "client": client,
            })
        
        # Create Risk Manager if enabled
        if self.include_risk_manager:
            self.agents.append({
                "name": "Risk_Manager",
                "system": RISK_MANAGER_PROMPT,
                "client": client,
            })
        
        # Add Chairman (Synthesizer) last
        self.agents.append({
            "name": "Chief_Strategist",
            "system": SYNTHESIZER_PROMPT,
            "client": client,
        })

    def _create_client(self):
        """Create LLM client based on config."""
        if self.llm_config["provider"] == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=self.llm_config["model"],
                base_url=self.llm_config["base_url"],
                temperature=self.llm_config.get("temperature", 0.7),
            )
        elif self.llm_config["provider"] == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model_name=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                temperature=self.llm_config.get("temperature", 0.7),
            )
        else:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=self.llm_config["model"],
                api_key=self.llm_config["api_key"],
                temperature=self.llm_config.get("temperature", 0.7),
            )

    async def conduct_vote(self, query: str) -> BoardVerdict:
        """
        Conduct a board meeting and vote on the query.
        
        Returns BoardVerdict with voting results.
        """
        start_time = datetime.now()
        self.votes = []
        self.turn_log = []
        
        messages = []
        
        # Each agent speaks in order
        for i, agent in enumerate(self.agents):
            is_chairman = (i == len(self.agents) - 1)
            
            if is_chairman:
                # Chairman waits for others then synthesizes
                context = "\n\n".join([
                    f"{a['name']}: {self._last_content(messages, a['name'])}"
                    for a in self.agents[:-1]
                    if self._last_content(messages, a["name"])
                ])
                prompt = f"""CEO has asked: "{query}"

Previous board members have said:
{context}

As Chief Strategist, provide the FINAL BOARD VERDICT based on all input."""
            else:
                prompt = f"""CEO has asked: "{query}"

As {agent['name']}, provide your analysis and recommendation.
Be decisive - state BUY/SELL/HOLD with confidence level."""
            
            response = await self._call_agent(agent, prompt)
            messages.append({"name": agent["name"], "content": response})
            
            # Log turn
            self.turn_log.append({
                "speaker": agent["name"],
                "content": response[:500],
            })
            
            # Extract vote from non-chairman agents
            if not is_chairman:
                rec = self._parse_recommendation(response)
                conf = self._parse_confidence(response)
                if rec:
                    self.votes.append(AgentVote(
                        agent_name=agent["name"],
                        recommendation=rec,
                        confidence=conf,
                        reasoning=response[:300],
                    ))
        
        # Synthesize final verdict
        elapsed = (datetime.now() - start_time).total_seconds()
        verdict = self._synthesize_verdict(query, elapsed)
        
        return verdict

    async def conduct_vote_streaming(self, query: str) -> AsyncGenerator[dict[str, Any], None]:
        """
        Conduct a board meeting with streaming output.
        
        Yields events as dicts:
        - {"type": "agent_speaking", "data": {"agent": "...", "content": "..."}}
        - {"type": "vote", "data": {"agent": "...", "recommendation": "...", "confidence": 0.x}}
        - {"type": "verdict", "data": BoardVerdict.to_dict()}
        """
        start_time = datetime.now()
        self.votes = []
        self.turn_log = []
        
        for i, agent in enumerate(self.agents):
            is_chairman = (i == len(self.agents) - 1)
            
            if is_chairman:
                context = "\n\n".join([
                    f"{a['name']}: {self._last_content([], a['name'])}"
                    for a in self.agents[:-1]
                ])
                prompt = f"""CEO has asked: "{query}"

Previous board members have said:
{context}

As Chief Strategist, provide the FINAL BOARD VERDICT."""
            else:
                prompt = f"""CEO has asked: "{query}"

As {agent['name']}, provide your analysis and recommendation.
Be decisive - state BUY/SELL/HOLD with confidence level."""
            
            response = await self._call_agent(agent, prompt)
            
            # Emit agent speaking event
            yield {
                "type": "agent_speaking",
                "data": {
                    "agent": agent["name"],
                    "content": response,
                },
            }
            
            # Try to extract and emit vote
            rec = self._parse_recommendation(response)
            conf = self._parse_confidence(response)
            
            if rec:
                vote = AgentVote(
                    agent_name=agent["name"],
                    recommendation=rec,
                    confidence=conf,
                    reasoning=response[:300],
                )
                self.votes.append(vote)
                
                yield {
                    "type": "vote",
                    "data": {
                        "agent": agent["name"],
                        "recommendation": rec.value,
                        "confidence": conf,
                    },
                }
            
            # Log turn
            self.turn_log.append({
                "speaker": agent["name"],
                "content": response[:500],
            })
        
        # Synthesize final verdict
        elapsed = (datetime.now() - start_time).total_seconds()
        verdict = self._synthesize_verdict(query, elapsed)
        
        yield {
            "type": "verdict",
            "data": verdict.to_dict(),
        }

    async def _call_agent(self, agent: dict, prompt: str) -> str:
        """Call an agent and return its response."""
        from langchain_core.messages import HumanMessage, SystemMessage
        
        messages = [
            SystemMessage(content=agent["system"]),
            HumanMessage(content=prompt),
        ]
        
        response = await agent["client"].ainvoke(messages)
        return response.content

    def _last_content(self, messages: list, name: str) -> str:
        """Get last content from a specific agent."""
        for msg in reversed(messages):
            if msg.get("name") == name:
                return msg.get("content", "")[:500]
        return ""

    def _parse_recommendation(self, text: str) -> Recommendation | None:
        """Parse recommendation from agent text."""
        text_upper = text.upper()
        
        patterns = [
            (r'RECOMMENDATION:\s*(BUY|SELL|HOLD|WAIT)', ['BUY', 'SELL', 'HOLD', 'WAIT']),
            (r'TIMING ASSESSMENT:\s*(FAVORABLE|UNFAVORABLE|NEUTRAL)', ['FAVORABLE', 'UNFAVORABLE', 'NEUTRAL']),
            (r'SHOULD\s+(BUY|SELL|HOLD)', ['BUY', 'SELL', 'HOLD']),
        ]
        
        for pattern, values in patterns:
            match = re.search(pattern, text_upper)
            if match:
                val = match.group(1)
                if val in ['BUY', 'SELL', 'HOLD', 'WAIT']:
                    return Recommendation(val)
                if val == 'FAVORABLE':
                    return Recommendation.BUY
                if val == 'UNFAVORABLE':
                    return Recommendation.SELL
                if val == 'NEUTRAL':
                    return Recommendation.HOLD
                    
        return None

    def _parse_confidence(self, text: str) -> float:
        """Parse confidence level from text."""
        match = re.search(r'CONFIDENCE:\s*(\d+)%?', text, re.IGNORECASE)
        if match:
            return int(match.group(1)) / 100.0
        return 0.5  # Default 50%

    def _synthesize_verdict(self, query: str, elapsed: float) -> BoardVerdict:
        """Synthesize final verdict from votes."""
        
        # Count votes with confidence weighting
        vote_tally: dict[Recommendation, float] = {}
        
        for vote in self.votes:
            rec = vote.recommendation
            conf = vote.confidence
            vote_tally[rec] = vote_tally.get(rec, 0.0) + conf
            
        # Determine consensus
        if vote_tally:
            consensus_rec = max(vote_tally, key=vote_tally.get)
            avg_confidence = sum(v.confidence for v in self.votes) / len(self.votes) if self.votes else 0.5
        else:
            consensus_rec = Recommendation.HOLD
            avg_confidence = 0.3
            
        # Check for dissent
        dissent = []
        if vote_tally:
            max_votes = vote_tally[consensus_rec]
            for rec, votes in vote_tally.items():
                if rec != consensus_rec and votes > max_votes * 0.5:
                    dissent.append(f"{rec.value} received {votes:.1f} weighted votes")
                    
        # If significant dissent, lower confidence
        if dissent:
            avg_confidence *= 0.8
            
        # Determine risk level
        if len(dissent) > 1:
            risk = RiskLevel.HIGH
        elif dissent:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW
            
        # Extract thesis
        thesis = f"Board vote: {consensus_rec.value} with {avg_confidence:.0%} confidence"
        if dissent:
            thesis += f". Dissent: {'; '.join(dissent)}"
            
        return BoardVerdict(
            recommendation=consensus_rec,
            confidence=min(avg_confidence, 0.95),
            time_horizon="Medium-term",
            thesis=thesis,
            risk_level=risk,
            votes=self.votes,
            dissent=dissent,
            elapsed_seconds=elapsed,
        )


async def run_board_meeting(
    query: str,
    provider: str = "auto",
    mode: Literal["round_robin", "debate"] = "debate",
    include_astrology: bool = True,
) -> BoardVerdict:
    """
    Convenience function to run a single board meeting.
    
    Example:
        verdict = await run_board_meeting(
            "Should I buy AAPL at current levels?",
            provider="openai",
        )
        print(f"Board recommends: {verdict.recommendation.value}")
    """
    async with BoardOfDirectors(
        provider=provider,
        mode=mode,
        include_astrology=include_astrology,
    ) as board:
        return await board.conduct_vote(query)
