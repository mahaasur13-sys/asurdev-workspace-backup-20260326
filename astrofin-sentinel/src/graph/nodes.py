from langchain_core.messages import AIMessage
from src.graph.state import AgentState
from src.types import Decision, AgentOpinion
from src.tools.market_data import get_market_data, get_technical_indicators
from src.tools.astro import AstroCalculator
from langchain_openai import ChatOpenAI
import os


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0
)

astro_calc = AstroCalculator()


def fetch_market_data(state: AgentState) -> AgentState:
    """Fetch current market data and technical indicators."""
    symbol = state["symbol"]
    timeframe = state["timeframe"]
    
    try:
        market_data = get_market_data(symbol.value, timeframe.value)
        technical = get_technical_indicators(symbol.value, timeframe.value)
        return {
            "market_data": market_data,
            "technical_analysis": technical,
            "messages": state["messages"] + [
                AIMessage(content=f"Market data fetched: {symbol.value} at ${market_data.price}")
            ]
        }
    except Exception as e:
        return {
            "errors": state["errors"] + [f"Market data error: {str(e)}"]
        }


def fetch_astro(state: AgentState) -> AgentState:
    """Calculate astrological signals for current moment."""
    from datetime import datetime
    
    try:
        now = datetime.utcnow()
        astro = astro_calc.calculate(now, 25.2048, 55.2708)  # Dubai
        favorable, strength, interp = astro_calc.is_favorable_for_trading(astro)
        
        astro_signal = {
            "moon_phase": astro.moon_phase,
            "moon_phase_deg": astro.moon_phase_deg,
            "lunar_day": astro.lunar_day,
            "nakshatra": astro.nakshatra,
            "yoga": astro.yoga,
            "karana": astro.karana,
            "is_favorable": favorable,
            "strength_score": strength,
            "interpretation": interp,
            "recommendation": "Favorable for trades" if favorable else "Reduce risk / avoid new positions"
        }
        
        return {
            "astro_signal": astro_signal,
            "messages": state["messages"] + [
                AIMessage(content=f"Astro signal: {astro.nakshatra} nakshatra, {astro.yoga} yoga, strength={strength:.2f}")
            ]
        }
    except Exception as e:
        return {
            "errors": state["errors"] + [f"Astro error: {str(e)}"]
        }


def run_market_analyst(state: AgentState) -> AgentState:
    """Market analyst agent - provides neutral technical overview."""
    market = state["market_data"]
    tech = state["technical_analysis"]
    
    prompt = f"""As a professional market analyst, analyze this asset:

Symbol: {state['symbol'].value.upper()}
Price: ${market.price:,.2f}
24h Change: {market.change_24h:+.2f}%
Volume: ${market.volume:,.0f}
Market Cap: ${market.market_cap:,.0f}
ATH: ${market.ath:,.2f} ({-market.ath_change:.1f}% from ATH)

Technical Indicators:
- Trend: {tech.trend}
- Support: ${tech.support:,.2f}
- Resistance: ${tech.resistance:,.2f}
- RSI: {tech.rsi:.1f}
- MACD: {tech.macd_signal}

Provide your analysis with:
1. Key observations
2. Support/resistance levels
3. Overall sentiment (bullish/bearish/neutral)
4. Confidence level (0-1)
"""
    
    response = llm.invoke(prompt)
    content = response.content
    
    # Parse decision from content
    decision = Decision.NEUTRAL
    if "STRONG BUY" in content.upper():
        decision = Decision.STRONG_BUY
    elif "BUY" in content.upper() and "STRONG" not in content.upper():
        decision = Decision.BUY
    elif "SELL" in content.upper():
        decision = Decision.SELL if "STRONG" not in content.upper() else Decision.STRONG_SELL
    
    opinion = AgentOpinion(
        agent_name="Market Analyst",
        role="Technical Analysis",
        decision=decision,
        confidence=0.7,
        reasoning=content[:500],
        key_factors=["RSI", "Support/Resistance", "Trend"],
        weight=1.0
    )
    
    return {
        "market_analyst_opinion": opinion,
        "messages": state["messages"] + [
            AIMessage(content=f"Market Analyst Opinion: {decision.value} (confidence: 0.7)")
        ]
    }


def run_bull_researcher(state: AgentState) -> AgentState:
    """Bull researcher - finds bullish arguments."""
    market = state["market_data"]
    astro = state.get("astro_signal")
    
    prompt = f"""As a bullish researcher, make the strongest case for buying {state['symbol'].value.upper()}:

Price: ${market.price:,.2f}
24h Change: {market.change_24h:+.2f}%
ATH Distance: {-market.ath_change:.1f}% (closer to ATH = more upside potential)
Volume: {market.volume:,.0f}

Technical: Trend={state['technical_analysis'].trend}, RSI={state['technical_analysis'].rsi:.1f}

{'Astro favorability: ' + ('POSITIVE' if astro['is_favorable'] else 'NEGATIVE') + f' (score: {astro[\"strength_score\"]:.2f})' if astro else ''}

Find:
1. 3 strongest bullish signals
2. Potential catalysts for rally
3. Entry points and targets
"""
    
    response = llm.invoke(prompt)
    
    opinion = AgentOpinion(
        agent_name="Bull Researcher",
        role="Bullish Analysis",
        decision=Decision.BUY,
        confidence=0.65,
        reasoning=response.content[:500],
        key_factors=["Bullish patterns", "Catalysts", "Support bounce"],
        weight=0.8
    )
    
    return {
        "bull_opinion": opinion,
        "messages": state["messages"] + [AIMessage(content="Bull Researcher: BUY")]
    }


def run_bear_researcher(state: AgentState) -> AgentState:
    """Bear researcher - finds bearish arguments."""
    market = state["market_data"]
    astro = state.get("astro_signal")
    
    prompt = f"""As a bearish researcher, make the strongest case against buying {state['symbol'].value.upper()}:

Price: ${market.price:,.2f}
24h Change: {market.change_24h:+.2f}%
ATH Distance: {-market.ath_change:.1f}%

Technical: Trend={state['technical_analysis'].trend}, RSI={state['technical_analysis'].rsi:.1f}

{'Astro favorability: ' + ('POSITIVE' if astro['is_favorable'] else 'NEGATIVE') + f' (score: {astro[\"strength_score\"]:.2f})' if astro else ''}

Find:
1. 3 strongest bearish signals
2. Risks and red flags
3. Exit points and stop-loss levels
"""
    
    response = llm.invoke(prompt)
    
    opinion = AgentOpinion(
        agent_name="Bear Researcher",
        role="Bearish Analysis",
        decision=Decision.SELL,
        confidence=0.65,
        reasoning=response.content[:500],
        key_factors=["Bearish patterns", "Overbought", "Resistance rejection"],
        weight=0.8
    )
    
    return {
        "bear_opinion": opinion,
        "messages": state["messages"] + [AIMessage(content="Bear Researcher: SELL")]
    }


def run_astrologer(state: AgentState) -> AgentState:
    """Astrologer agent - provides astro-based recommendations."""
    astro = state["astro_signal"]
    
    prompt = f"""As a financial astrologer, interpret these celestial signals for trading:

Moon Phase: {astro['moon_phase']} ({astro['moon_phase_deg']:.1f}°)
Nakshatra: {astro['nakshatra']}
Yoga: {astro['yoga']}
Paksha: {astro['lunar_day']}

Favorability Score: {astro['strength_score']:.2f}/1.0
Interpretation: {astro['interpretation']}

Provide:
1. How these signals affect the trade decision
2. Recommended position size adjustment
3. Best timing (if applicable)
"""
    
    response = llm.invoke(prompt)
    
    decision = Decision.BUY if astro["is_favorable"] else Decision.SELL
    # Downgrade to neutral if score is close to 0.5
    if 0.45 < astro["strength_score"] < 0.55:
        decision = Decision.NEUTRAL
    
    opinion = AgentOpinion(
        agent_name="Financial Astrologer",
        role="Astrological Analysis",
        decision=decision,
        confidence=astro["strength_score"],
        reasoning=response.content[:500],
        key_factors=["Moon Phase", "Nakshatra", "Yoga", "Paksha"],
        weight=0.5  # Astro gets 50% weight
    )
    
    return {
        "astro_opinion": opinion,
        "messages": state["messages"] + [
            AIMessage(content=f"Astrologer: {decision.value} (confidence: {astro['strength_score']:.2f})")
        ]
    }


def run_synthesizer(state: AgentState) -> AgentState:
    """Synthesizer - aggregates all opinions and produces final recommendation."""
    from datetime import datetime
    
    opinions = [
        state["market_analyst_opinion"],
        state["bull_opinion"],
        state["bear_opinion"],
        state["astro_opinion"]
    ]
    
    # Weighted voting
    total_weight = sum(o.weight for o in opinions if o)
    decision_scores = {d: 0.0 for d in Decision}
    
    for opinion in opinions:
        if opinion:
            decision_scores[opinion.decision] += opinion.weight * opinion.confidence
    
    # Normalize and pick winner
    if total_weight > 0:
        for d in decision_scores:
            decision_scores[d] /= total_weight
    
    final_decision = max(decision_scores, key=decision_scores.get)
    consensus = 1 - (max(decision_scores.values()) - min(decision_scores.values()))
    
    # Final confidence based on consensus and individual confidences
    avg_confidence = sum(o.confidence for o in opinions if o) / len(opinions)
    final_confidence = avg_confidence * (0.5 + consensus * 0.5)
    
    # Risk assessment
    if final_decision in [Decision.STRONG_BUY, Decision.STRONG_SELL]:
        risk = "HIGH - Extreme position, reduce size"
    elif consensus < 0.3:
        risk = "MEDIUM - Agents disagree, wait for clarity"
    else:
        risk = "LOW - Consensus reached"
    
    recommendation = f"""Board Vote Result for {state['symbol'].value.upper()}:

CONSENSUS: {final_decision.value} (confidence: {final_confidence:.1%})
Risk Level: {risk}

Agent Votes:
- Market Analyst: {state['market_analyst_opinion'].decision.value} ({state['market_analyst_opinion'].confidence:.0%})
- Bull Researcher: {state['bull_opinion'].decision.value} ({state['bull_opinion'].confidence:.0%})
- Bear Researcher: {state['bear_opinion'].decision.value} ({state['bear_opinion'].confidence:.0%})
- Astrologer: {state['astro_opinion'].decision.value} ({state['astro_opinion'].confidence:.0%})

Market: ${state['market_data'].price:,.2f} ({state['market_data'].change_24h:+.1f}% 24h)
Astro Score: {state['astro_signal']['strength_score']:.2f}/1.0 ({state['astro_signal']['is_favorable']})

⚠️ This is NOT financial advice. Make your own decisions.
"""
    
    board_vote = BoardVote(
        timestamp=datetime.utcnow(),
        symbol=state["symbol"],
        agents=opinions,
        consensus_score=consensus,
        final_decision=final_decision,
        final_confidence=final_confidence,
        final_recommendation=recommendation,
        risk_assessment=risk
    )
    
    return {
        "board_vote": board_vote,
        "messages": state["messages"] + [AIMessage(content=recommendation)]
    }
