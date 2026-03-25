"""
LangGraph Nodes for AstroFin Sentinel

Each node represents a step in the analysis pipeline.
Nodes are designed for async execution where applicable.
"""

import asyncio
from datetime import datetime
from typing import Optional
from langgraph.types import Command

from .state import (
    AnalysisState, 
    AgentReport, 
    ReportMetadata,
    AgentStatus,
    QueryType
)


def _state_to_dict(state: AnalysisState) -> dict:
    """Convert state to dict, filtering out fields that will be explicitly set."""
    d = state.__dict__.copy()
    # Remove fields that will be explicitly set in return
    fields_to_remove = [
        'technical_report', 'fundamental_report', 'astrologer_report',
        'technical_meta', 'fundamental_meta', 'astrologer_meta',
        'synthesizer_report', 'composite_score', 'final_recommendation',
        'markdown_output', 'quality_passed', 'quality_issues',
        'memory_context', 'analysis_history', 'error', 'completed_at'
    ]
    for key in fields_to_remove:
        d.pop(key, None)
    return d


# ============================================================================
# SUPERVISOR NODE (Router)
# ============================================================================

async def supervisor_node(state: AnalysisState) -> AnalysisState:
    """Supervisor node - routes the query to appropriate agents."""
    
    if not state.symbol:
        return AnalysisState(error="Symbol is required", created_at=datetime.now())
    
    # Determine query type
    if state.birth_date and state.birth_time:
        query_type = QueryType.FULL_ANALYSIS
    elif state.skip_agents:
        if "fundamental" in state.skip_agents:
            query_type = QueryType.TECHNICAL_ONLY
        else:
            query_type = QueryType.TECHNICAL_FUNDAMENTAL
    else:
        query_type = QueryType.FULL_ANALYSIS
    
    return AnalysisState(
        symbol=state.symbol,
        side=state.side,
        interval=state.interval,
        birth_date=state.birth_date,
        birth_time=state.birth_time,
        weights=state.weights,
        risk_level=state.risk_level,
        query_type=query_type,
        skip_agents=state.skip_agents,
        session_id=state.session_id,
        created_at=state.created_at,
        technical_meta=ReportMetadata(agent_id="technical", status=AgentStatus.PENDING),
        fundamental_meta=ReportMetadata(agent_id="fundamental", status=AgentStatus.PENDING),
        astrologer_meta=ReportMetadata(agent_id="astrologer", status=AgentStatus.PENDING),
    )


# ============================================================================
# AGENT NODES
# ============================================================================

async def technical_node(state: AnalysisState) -> AnalysisState:
    """Technical Analyst Node - fetches market data and calculates indicators."""
    
    if "technical" in state.skip_agents:
        return AnalysisState(
            **_state_to_dict(state),
            technical_meta=ReportMetadata(agent_id="technical", status=AgentStatus.SKIPPED)
        )
    
    meta = ReportMetadata(agent_id="technical", started_at=datetime.now(), status=AgentStatus.RUNNING)
    
    try:
        from agents.technical_analyst import get_technical_analyst
        agent = get_technical_analyst()
        report = agent.analyze(symbol=state.symbol, interval=state.interval)
        
        agent_report = AgentReport(
            agent_id="technical",
            signal=report.signal,
            confidence=report.confidence,
            reasoning=report.reasoning,
            data={"pattern": report.pattern, "levels": report.levels, "indicators": report.indicators}
        )
        
        completed_at = datetime.now()
        meta.status = AgentStatus.COMPLETED
        meta.completed_at = completed_at
        meta.execution_time_ms = int((completed_at - meta.started_at).total_seconds() * 1000)
        
        return AnalysisState(
            **_state_to_dict(state),
            technical_report=agent_report,
            technical_meta=meta
        )
    except Exception as e:
        meta.status = AgentStatus.FAILED
        meta.error = str(e)
        meta.completed_at = datetime.now()
        return AnalysisState(**_state_to_dict(state), technical_meta=meta, error=f"Technical analysis failed: {e}")


async def fundamental_node(state: AnalysisState) -> AnalysisState:
    """Fundamental Analyst Node - analyzes news, on-chain metrics, macro factors."""
    
    if "fundamental" in state.skip_agents:
        return AnalysisState(
            **_state_to_dict(state),
            fundamental_meta=ReportMetadata(agent_id="fundamental", status=AgentStatus.SKIPPED)
        )
    
    meta = ReportMetadata(agent_id="fundamental", started_at=datetime.now(), status=AgentStatus.RUNNING)
    
    try:
        from agents.fundamental_analyst import get_fundamental_analyst
        agent = get_fundamental_analyst()
        report = agent.analyze(symbol=state.symbol)
        
        agent_report = AgentReport(
            agent_id="fundamental",
            signal=report.verdict,
            confidence=report.strength,
            reasoning=report.reasoning,
            data={
                "factors": report.factors,
                "risk_factors": report.risk_factors,
                "verdict": report.verdict,
                "onchain_summary": report.onchain_summary,
                "news_sentiment": report.news_sentiment
            }
        )
        
        completed_at = datetime.now()
        meta.status = AgentStatus.COMPLETED
        meta.completed_at = completed_at
        meta.execution_time_ms = int((completed_at - meta.started_at).total_seconds() * 1000)
        
        return AnalysisState(
            **_state_to_dict(state),
            fundamental_report=agent_report,
            fundamental_meta=meta
        )
    except Exception as e:
        meta.status = AgentStatus.FAILED
        meta.error = str(e)
        meta.completed_at = datetime.now()
        return AnalysisState(**_state_to_dict(state), fundamental_meta=meta, error=f"Fundamental analysis failed: {e}")


async def astrologer_node(state: AnalysisState) -> AnalysisState:
    """Astrologer Node - performs Vedic astrological analysis."""
    
    if "astrologer" in state.skip_agents:
        return AnalysisState(
            **_state_to_dict(state),
            astrologer_meta=ReportMetadata(agent_id="astrologer", status=AgentStatus.SKIPPED)
        )
    
    meta = ReportMetadata(agent_id="astrologer", started_at=datetime.now(), status=AgentStatus.RUNNING)
    
    try:
        from agents.astrologer import get_astrologer
        agent = get_astrologer(birth_date=state.birth_date, birth_time=state.birth_time)
        report = agent.analyze(symbol=state.symbol, side=state.side)
        
        agent_report = AgentReport(
            agent_id="astrologer",
            signal=report.signal,
            confidence=report.confidence,
            reasoning=report.reasoning,
            data={
                "muhurta": report.muhurta,
                "favorable": report.favorable,
                "unfavorable": report.unfavorable,
                "planetary_yoga": report.planetary_yoga,
                "transits": report.transits,
                "dasha": report.dasha,
                "planet_strength": report.planet_strength or {},
                "nakshatra_influence": report.nakshatra_influence,
                "moon_phase": report.moon_phase,
                "eclipse_risk": report.eclipse_risk
            }
        )
        
        completed_at = datetime.now()
        meta.status = AgentStatus.COMPLETED
        meta.completed_at = completed_at
        meta.execution_time_ms = int((completed_at - meta.started_at).total_seconds() * 1000)
        
        return AnalysisState(
            **_state_to_dict(state),
            astrologer_report=agent_report,
            astrologer_meta=meta
        )
    except Exception as e:
        meta.status = AgentStatus.FAILED
        meta.error = str(e)
        meta.completed_at = datetime.now()
        return AnalysisState(**_state_to_dict(state), astrologer_meta=meta, error=f"Astrological analysis failed: {e}")


# ============================================================================
# QUALITY GATE
# ============================================================================

def quality_gate_node(state: AnalysisState) -> AnalysisState:
    """Quality Gate - validates report completeness."""
    
    issues = []
    required = []
    
    if state.query_type == QueryType.FULL_ANALYSIS:
        required = ["technical", "fundamental", "astrologer"]
    elif state.query_type == QueryType.TECHNICAL_FUNDAMENTAL:
        required = ["technical", "fundamental"]
    else:
        required = ["technical"]
    
    for agent_id in required:
        if agent_id in state.skip_agents:
            continue
        meta = getattr(state, f"{agent_id}_meta")
        if not meta:
            issues.append(f"{agent_id}: No metadata")
            continue
        if meta.status == AgentStatus.FAILED:
            issues.append(f"{agent_id}: Failed - {meta.error}")
        elif meta.status != AgentStatus.COMPLETED:
            issues.append(f"{agent_id}: Not completed (status={meta.status})")
        else:
            report = getattr(state, f"{agent_id}_report")
            if report and report.confidence < 0.1:
                issues.append(f"{agent_id}: Very low confidence ({report.confidence})")
    
    quality_passed = len(issues) == 0
    
    # Preserve existing reports and metadata
    return AnalysisState(
        symbol=state.symbol,
        side=state.side,
        interval=state.interval,
        birth_date=state.birth_date,
        birth_time=state.birth_time,
        weights=state.weights,
        risk_level=state.risk_level,
        query_type=state.query_type,
        skip_agents=state.skip_agents,
        session_id=state.session_id,
        created_at=state.created_at,
        technical_report=state.technical_report,
        fundamental_report=state.fundamental_report,
        astrologer_report=state.astrologer_report,
        technical_meta=state.technical_meta,
        fundamental_meta=state.fundamental_meta,
        astrologer_meta=state.astrologer_meta,
        quality_passed=quality_passed,
        quality_issues=issues,
        error="; ".join(issues) if issues else None
    )


# ============================================================================
# SYNTHESIZER
# ============================================================================

def synthesizer_node(state: AnalysisState) -> AnalysisState:
    """Synthesizer Node - combines all reports into final recommendation."""
    
    reports = state.get_all_reports()
    if not reports:
        return AnalysisState(**_state_to_dict(state), error="No reports to synthesize")
    
    try:
        from agents.synthesizer import get_synthesizer, SynthesizerAgent
        from agents.technical_analyst import TechnicalReport
        from agents.fundamental_analyst import FundamentalReport
        from agents.astrologer import AstroReport
        
        # Build legacy report objects
        tech_report = None
        fund_report = None
        astro_report = None
        
        if state.technical_report:
            tr = state.technical_report
            tech_report = TechnicalReport(
                signal=tr.signal, confidence=tr.confidence,
                pattern=tr.data.get("pattern", ""), levels=tr.data.get("levels", {}),
                indicators=tr.data.get("indicators", {}), reasoning=tr.reasoning,
                symbol=state.symbol, interval=state.interval
            )
        
        if state.fundamental_report:
            fr = state.fundamental_report
            fund_report = FundamentalReport(
                verdict=fr.signal, strength=fr.confidence,
                factors=fr.data.get("factors", []), risk_factors=fr.data.get("risk_factors", []),
                reasoning=fr.reasoning, symbol=state.symbol,
                onchain_summary=fr.data.get("onchain_summary", {}),
                news_sentiment=fr.data.get("news_sentiment", "NEUTRAL")
            )
        
        if state.astrologer_report:
            ar = state.astrologer_report
            astro_report = AstroReport(
                muhurta=ar.data.get("muhurta", {}), favorable=ar.data.get("favorable", []),
                unfavorable=ar.data.get("unfavorable", []), planetary_yoga=ar.data.get("planetary_yoga", {}),
                transits=ar.data.get("transits", {}), dasha=ar.data.get("dasha", {}),
                signal=ar.signal, confidence=ar.confidence, reasoning=ar.reasoning,
                planet_strength=ar.data.get("planet_strength", {}),
                nakshatra_influence=ar.data.get("nakshatra_influence", ""),
                moon_phase=ar.data.get("moon_phase", ""), eclipse_risk=ar.data.get("eclipse_risk", False)
            )
        
        synthesizer = SynthesizerAgent(weights=state.weights)
        
        # Create placeholder astro if not available
        if not astro_report:
            astro_report = AstroReport(
                muhurta={"overall": "NEUTRAL", "best_time": "N/A"},
                favorable=[], unfavorable=[],
                planetary_yoga={"active": [], "interpretation": ""},
                transits={"benefic": [], "malefic": []}, dasha={},
                signal="NEUTRAL", confidence=0.5, reasoning="Astrological analysis skipped"
            )
        
        # Create placeholder fund if not available
        if not fund_report:
            fund_report = FundamentalReport(
                verdict="NEUTRAL", strength=0.5, factors=[], risk_factors=[],
                reasoning="Fundamental analysis skipped", symbol=state.symbol,
                onchain_summary={}, news_sentiment="NEUTRAL"
            )
        
        if not tech_report:
            return AnalysisState(**_state_to_dict(state), error="No technical report available")
        
        synth_report = synthesizer.synthesize(
            technical=tech_report, fundamental=fund_report, astrological=astro_report,
            symbol=state.symbol
        )
        
        synth_dict = synthesizer.to_dict(synth_report)
        markdown = synthesizer.to_markdown(synth_report)
        
        return AnalysisState(
            **_state_to_dict(state),
            synthesizer_report=synth_dict,
            composite_score=synth_report.weighted_score.get("composite"),
            final_recommendation={
                "action": synth_report.recommendation.get("action"),
                "position_size": synth_report.recommendation.get("position_size"),
                "entry_zone": synth_report.recommendation.get("entry_zone"),
                "stop_loss": synth_report.recommendation.get("stop_loss"),
                "timeframe": synth_report.recommendation.get("timeframe")
            },
            markdown_output=markdown,
            completed_at=datetime.now()
        )
    except Exception as e:
        return AnalysisState(**_state_to_dict(state), error=f"Synthesis failed: {e}")


# ============================================================================
# MEMORY (RAG)
# ============================================================================

async def memory_node(state: AnalysisState) -> AnalysisState:
    """Memory Node - stores and retrieves context via RAG."""
    
    from .memory import get_memory
    memory = get_memory()
    
    if state.final_recommendation:
        await memory.store_analysis(state)
    
    relevant = await memory.retrieve_relevant(
        query=f"{state.symbol} {state.side}", symbol=state.symbol, limit=3
    )
    
    # Preserve all existing state and only update memory-related fields
    return AnalysisState(
        symbol=state.symbol,
        side=state.side,
        interval=state.interval,
        birth_date=state.birth_date,
        birth_time=state.birth_time,
        weights=state.weights,
        risk_level=state.risk_level,
        query_type=state.query_type,
        skip_agents=state.skip_agents,
        session_id=state.session_id,
        created_at=state.created_at,
        # Preserve agent reports
        technical_report=state.technical_report,
        fundamental_report=state.fundamental_report,
        astrologer_report=state.astrologer_report,
        technical_meta=state.technical_meta,
        fundamental_meta=state.fundamental_meta,
        astrologer_meta=state.astrologer_meta,
        # Preserve synthesis output
        synthesizer_report=state.synthesizer_report,
        composite_score=state.composite_score,
        final_recommendation=state.final_recommendation,
        markdown_output=state.markdown_output,
        # Preserve quality gate results
        quality_passed=state.quality_passed,
        quality_issues=state.quality_issues,
        # Update memory fields
        memory_context=relevant,
        analysis_history=relevant,
        completed_at=datetime.now()
    )


# ============================================================================
# PARALLEL EXECUTION WRAPPER
# ============================================================================

async def run_agents_parallel(state: AnalysisState, agent_names: list[str]) -> AnalysisState:
    """Run multiple agents in parallel using asyncio.gather."""
    
    tasks = []
    if "technical" in agent_names and "technical" not in state.skip_agents:
        tasks.append(technical_node(state))
    if "fundamental" in agent_names and "fundamental" not in state.skip_agents:
        tasks.append(fundamental_node(state))
    if "astrologer" in agent_names and "astrologer" not in state.skip_agents:
        tasks.append(astrologer_node(state))
    
    if not tasks:
        return state
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            continue
        if isinstance(result, AnalysisState):
            if result.technical_report:
                state.technical_report = result.technical_report
                state.technical_meta = result.technical_meta
            if result.fundamental_report:
                state.fundamental_report = result.fundamental_report
                state.fundamental_meta = result.fundamental_meta
            if result.astrologer_report:
                state.astrologer_report = result.astrologer_report
                state.astrologer_meta = result.astrologer_meta
    
    return state
