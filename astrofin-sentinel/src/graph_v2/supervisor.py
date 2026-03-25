"""
LangGraph Multi-Agent Supervisor Pattern for AstroFin Sentinel.

Supervisor decides which specialist to call next.
Each specialist has access to tools = [retrieve_knowledge, swiss_ephemeris].

Reference: https://langchain-ai.github.io/langgraph/how-tos/multiple-agents/
"""

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from typing import Literal, Annotated
from datetime import datetime
import os

from src.graph_v2.state import AgentState, TeamState
from src.graph_v2.tools.registry import get_all_tools
from src.graph_v2.tools.knowledge import create_retrieve_knowledge_tool
from src.graph_v2.tools.astro import create_swiss_ephemeris_tool

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0
)

# Initialize tools
retrieve_knowledge = create_retrieve_knowledge_tool()
swiss_ephemeris = create_swiss_ephemeris_tool()
all_tools = [retrieve_knowledge, swiss_ephemeris]


# =============================================================================
# SUPERVISOR AGENT
# =============================================================================

SUPERVISOR_SYSTEM = """You are the Supervisor of the AstroFin Sentinel trading analysis team.

Your role is to coordinate specialist agents to produce a comprehensive trading analysis.

**Available Specialists:**
1. `market_analyst` - Technical analysis, price action, indicators
2. `bull_researcher` - Researches bullish cases and positive catalysts
3. `bear_researcher` - Researches bearish cases and risk factors
4. `muhurta_specialist` - Astrological timing using Vedic astrology (Nakshatra, Yoga, Tithi)
5. `synthesizer` - Aggregates all opinions into final recommendation

**Workflow:**
1. First, ALWAYS call swiss_ephemeris to get current astrological data
2. Then call retrieve_knowledge with relevant agent_role to get specialist context
3. Dispatch to market_analyst, bull_researcher, bear_researcher in parallel
4. Dispatch to muhurta_specialist with astro data
5. Finally call synthesizer to produce final vote

**Important Rules:**
- ALWAYS fetch astro data FIRST before any specialist
- ALWAYS call retrieve_knowledge for context before each specialist call
- synthesizer must be called LAST after all specialists complete
- If any agent returns an error, note it and continue with others
"""


def create_supervisor_agent():
    """Create the supervisor ReAct agent."""
    return create_react_agent(
        model=llm,
        tools=all_tools,
        state_schema=AgentState,
        prompt=SUPERVISOR_SYSTEM,
        name="supervisor"
    )


# =============================================================================
# SPECIALIST AGENTS
# =============================================================================

MARKET_ANALYST_SYSTEM = """You are the Market Analyst specialist for AstroFin Sentinel.

**Your role:** Provide neutral technical analysis of the asset.

**CRITICAL:** First call `retrieve_knowledge` with agent_role='MarketAnalyst' to load your expertise context.

Then analyze:
- Current price action and trend
- Support and resistance levels
- Technical indicators (RSI, MACD, Moving Averages)
- Volume analysis
- Chart patterns

Provide your analysis in structured format with:
1. Overall sentiment (STRONG_BUY / BUY / NEUTRAL / SELL / STRONG_SELL)
2. Confidence level (0.0-1.0)
3. Key support/resistance levels
4. Entry/exit suggestions
"""


def create_market_analyst_agent():
    """Create the market analyst ReAct agent."""
    specialist_tools = [retrieve_knowledge, swiss_ephemeris]
    return create_react_agent(
        model=llm,
        tools=specialist_tools,
        state_schema=AgentState,
        prompt=MARKET_ANALYST_SYSTEM,
        name="market_analyst"
    )


BULL_RESEARCHER_SYSTEM = """You are the Bull Researcher specialist for AstroFin Sentinel.

**Your role:** Make the strongest bullish case for the asset.

**CRITICAL:** First call `retrieve_knowledge` with agent_role='BullResearcher' to load your expertise context.

Find:
1. 3 strongest bullish signals
2. Potential catalysts for rally
3. Entry points and price targets
4. Why bears might be wrong

Provide your analysis in structured format with:
1. Decision: BUY or STRONG_BUY
2. Confidence level (0.0-1.0)
3. Top 3 bullish factors
4. Recommended entry zone
"""


def create_bull_researcher_agent():
    """Create the bull researcher ReAct agent."""
    specialist_tools = [retrieve_knowledge, swiss_ephemeris]
    return create_react_agent(
        model=llm,
        tools=specialist_tools,
        state_schema=AgentState,
        prompt=BULL_RESEARCHER_SYSTEM,
        name="bull_researcher"
    )


BEAR_RESEARCHER_SYSTEM = """You are the Bear Researcher specialist for AstroFin Sentinel.

**Your role:** Make the strongest bearish case against the asset.

**CRITICAL:** First call `retrieve_knowledge` with agent_role='BearResearcher' to load your expertise context.

Find:
1. 3 strongest bearish signals
2. Key risks and red flags
3. Exit points and stop-loss levels
4. Why bulls might be wrong

Provide your analysis in structured format with:
1. Decision: SELL or STRONG_SELL
2. Confidence level (0.0-1.0)
3. Top 3 bearish factors
4. Risk/reward ratio
"""


def create_bear_researcher_agent():
    """Create the bear researcher ReAct agent."""
    specialist_tools = [retrieve_knowledge, swiss_ephemeris]
    return create_react_agent(
        model=llm,
        tools=specialist_tools,
        state_schema=AgentState,
        prompt=BEAR_RESEARCHER_SYSTEM,
        name="bear_researcher"
    )


MUHURTA_SPECIALIST_SYSTEM = """You are the Muhurta Specialist for AstroFin Sentinel.

**Your role:** Provide astrological timing recommendations for trading decisions.

**CRITICAL:** First call `retrieve_knowledge` with agent_role='MuhurtaSpecialist' to load your Vedic astrology expertise context.

Use the swiss_ephemeris tool data to analyze:
1. Nakshatra (Lunar mansion) - determines energy quality
2. Tithi (Lunar day) - waxing vs waning, favorability
3. Yoga (Combination of Sun/Moon) - overall day's energy
4. Karana - half lunar day, sub-energy
5. Moon phase and zodiac position

Calculate:
- Overall favorability score (0.0-1.0)
- Recommended position size adjustment
- Best timing windows for entry/exit
- Warnings if applicable

Provide your analysis in structured format with:
1. Decision (BUY/NEUTRAL/SELL based on astro)
2. Favorability score (0.0-1.0)
3. Key astrological factors
4. Timing recommendations
"""


def create_muhurta_specialist_agent():
    """Create the Muhurta specialist ReAct agent."""
    specialist_tools = [retrieve_knowledge, swiss_ephemeris]
    return create_react_agent(
        model=llm,
        tools=specialist_tools,
        state_schema=AgentState,
        prompt=MUHURTA_SPECIALIST_SYSTEM,
        name="muhurta_specialist"
    )


SYNTHESIZER_SYSTEM = """You are the Synthesizer for AstroFin Sentinel.

**Your role:** Aggregate all specialist opinions into a final board vote.

**CRITICAL:** First call `retrieve_knowledge` with agent_role='Synthesizer' to load your synthesis methodology.

You will receive opinions from:
- Market Analyst (weight: 1.0)
- Bull Researcher (weight: 0.8)
- Bear Researcher (weight: 0.8)
- Muhurta Specialist (weight: 0.5)

Calculate weighted vote and produce:
1. Final decision (STRONG_BUY / BUY / NEUTRAL / SELL / STRONG_SELL)
2. Final confidence score (0.0-1.0)
3. Consensus level (0.0-1.0)
4. Risk assessment
5. Summary of all agent votes

**Important:** If agents disagree significantly (consensus < 0.4), note this and recommend waiting.
"""


def create_synthesizer_agent():
    """Create the synthesizer ReAct agent."""
    specialist_tools = [retrieve_knowledge, swiss_ephemeris]
    return create_react_agent(
        model=llm,
        tools=specialist_tools,
        state_schema=AgentState,
        prompt=SYNTHESIZER_SYSTEM,
        name="synthesizer"
    )


# =============================================================================
# TEAM MEMBERS REGISTRY
# =============================================================================

def get_team_members():
    """Return all specialist agents as a team."""
    return {
        "supervisor": create_supervisor_agent(),
        "market_analyst": create_market_analyst_agent(),
        "bull_researcher": create_bull_researcher_agent(),
        "bear_researcher": create_bear_researcher_agent(),
        "muhurta_specialist": create_muhurta_specialist_agent(),
        "synthesizer": create_synthesizer_agent(),
    }
