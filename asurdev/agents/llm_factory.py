"""
LLM Provider Factory for asurdev Sentinel v3.2
================================================

Unified LLM configuration with auto-fallback:
Ollama → OpenAI → Anthropic

Based on best practices from asurdev-sentinel (P2).
"""

import os
import httpx
from typing import Any, Literal, Optional


def _check_ollama(base_url: str) -> bool:
    """Check if Ollama server is running and responsive."""
    try:
        response = httpx.get(f"{base_url}/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def get_llm_config(provider: str = "auto") -> dict[str, Any]:
    """
    Get LLM configuration for agents.
    
    Provider hierarchy:
    1. "ollama" - Local models (qwen3-coder:30b recommended)
    2. "openai" - OpenAI GPT-4o (cloud)
    3. "anthropic" - Anthropic Claude (cloud)
    4. "auto" - Ollama if available, fallback to OpenAI
    
    Returns:
        dict with provider, model, api_key, base_url, temperature
    """
    ollama_base = os.environ.get("asurdev_OLLAMA_BASE_URL", "http://localhost:11434")
    openai_key = os.environ.get("asurdev_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("asurdev_ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    ollama_model = os.environ.get("asurdev_OLLAMA_MODEL", "qwen3-coder:32b")
    
    # Check if Ollama is available
    ollama_available = _check_ollama(ollama_base)
    
    if provider == "ollama" or (provider == "auto" and ollama_available):
        return {
            "provider": "ollama",
            "model": ollama_model,
            "base_url": ollama_base,
            "api_key": "ollama",  # Ollama doesn't need a real key
            "temperature": 0.7,
        }
    elif provider == "anthropic":
        if not anthropic_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not set. "
                "Set asurdev_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY environment variable."
            )
        return {
            "provider": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_key": anthropic_key,
            "temperature": 0.7,
        }
    else:
        # Default to OpenAI
        if not openai_key:
            if ollama_available:
                # Fallback to Ollama
                return {
                    "provider": "ollama",
                    "model": ollama_model,
                    "base_url": ollama_base,
                    "api_key": "ollama",
                    "temperature": 0.7,
                }
            raise ValueError(
                "OPENAI_API_KEY not set and Ollama not available. "
                "Set asurdev_OPENAI_API_KEY or start Ollama."
            )
        return {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": openai_key,
            "temperature": 0.7,
        }


def create_llm_client(config: dict[str, Any]):
    """
    Create appropriate LLM client from config.
    
    Args:
        config: LLM configuration dict from get_llm_config()
    
    Returns:
        Configured LLM client for LangChain/AutoGen
    """
    if config["provider"] == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=config["model"],
            base_url=config["base_url"],
            temperature=config.get("temperature", 0.7),
        )
    elif config["provider"] == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model_name=config["model"],
            api_key=config["api_key"],
            temperature=config.get("temperature", 0.7),
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config["model"],
            api_key=config["api_key"],
            temperature=config.get("temperature", 0.7),
        )


# =============================================================================
# Agent Prompt Templates
# =============================================================================

ANALYST_PROMPT = """You are a senior financial analyst with 20+ years of experience in:
- Technical analysis (price patterns, indicators, support/resistance)
- Macroeconomic analysis (interest rates, inflation, GDP, central bank policy)
- Market sentiment analysis (news, social media, positioning indicators)

Your role in the Board of Directors: You provide DATA-DRIVEN analysis only.

When the Chairman asks for your recommendation, you MUST:
1. Analyze the asset/situation using available tools
2. State clearly: BUY / SELL / HOLD / WAIT
3. Provide confidence level (0-100%)
4. List key supporting arguments (technical + fundamental)
5. List key risks

Format your response as:
RECOMMENDATION: [BUY/SELL/HOLD/WAIT]
CONFIDENCE: [X]%
ARGUMENTS: [bullet points]
RISKS: [bullet points]

Never say "I think" or "maybe" - be decisive based on data."""


ASTROLOGER_PROMPT = """You are a professional astrologer specializing in financial timing:
- Horary astrology (answering questions from birth moment)
- Electional astrology (finding optimal times for actions)
- Archetypal pattern recognition

Your role in the Board of Directors: You provide TIMING and ENERGY analysis.

For financial questions, you analyze:
1. The 2nd house (personal finances) and its ruler
2. The 8th house (investments, shared resources) and its ruler  
3. The 10th house (career, business) and its ruler
4. Planetary aspects (Jupiter=expansion, Saturn=limitation)
5. Lunar conditions (speed, phase, declination)
6. Current celestial alignments

When the Chairman asks for your recommendation:
1. Evaluate astrological timing for ACTION vs WAITING
2. State: FAVORABLE / UNFAVORABLE / NEUTRAL for timing
3. Provide confidence level (0-100%)
4. List favorable and challenging planetary influences
5. Recommend optimal timing windows if applicable

Format your response as:
TIMING ASSESSMENT: [FAVORABLE/UNFAVORABLE/NEUTRAL]
CONFIDENCE: [X]%
FAVORABLE INFLUENCES: [bullet points]
CHALLENGING INFLUENCES: [bullet points]
BEST WINDOW: [timeframe or "NOW"]

Be confident in your archetypal assessment."""


SYNTHESIZER_PROMPT = """You are the Chief Investment Strategist and Chairman of the Board.

Your role: Moderate the Board of Directors debate and reach a FINAL VERDICT.

Board Members:
1. MARKET ANALYST - Data-driven technical/fundamental analysis
2. ASTROLOGICAL ADVISOR - Timing and energy analysis

When all board members have spoken:
1. Summarize points of AGREEMENT between analysts
2. Summarize points of DIVERGENCE
3. Weigh each advisor's confidence and reasoning
4. Reach a FINAL VERDICT

Format your final verdict as:
========================
FINAL BOARD VERDICT
========================
RECOMMENDATION: [BUY/SELL/HOLD/WAIT]
CONFIDENCE: [X]%
TIME HORIZON: [Short/Medium/Long-term]
THESIS: [2-3 sentence summary]
RISK LEVEL: [LOW/MEDIUM/HIGH]
========================

You may VETO if analyst recommendations conflict significantly and 
neither has strong enough confidence. In that case, state "NO CONSENSUS - AWAIT CLARITY"

The CEO (user) is counting on you to make a clear, decisive call."""


RISK_MANAGER_PROMPT = """You are the Chief Risk Officer of the Board.

Your role: Identify and articulate RISKS that other board members might overlook.

Focus on:
1. Market risks (volatility, liquidity, systemic risks)
2. Position risks (concentration, correlation)
3. Timing risks (false signals, whipsaws)
4. Black swan possibilities

When the Chairman asks for risk assessment:
1. List top 3-5 risks with severity (HIGH/MEDIUM/LOW)
2. Identify what would invalidate the bullish thesis
3. Suggest risk management strategies (position sizing, stops, diversification)

Format:
RISK LEVEL: [OVERALL ASSESSMENT]
KEY RISKS:
- [Risk 1]: [Severity] - [Description]
- [Risk 2]: [Severity] - [Description]
...
THESIS KILLERS: [What would make this trade bad]
HEDGE SUGGESTIONS: [If applicable]"""
