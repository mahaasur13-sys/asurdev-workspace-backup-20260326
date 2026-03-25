"""
Orchestrator for AstroFin Sentinel

Coordinates the multi-agent workflow: spawns agents,
collects reports, and passes to synthesizer.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

from agents.technical_analyst import get_technical_analyst, TechnicalReport
from agents.fundamental_analyst import get_fundamental_analyst, FundamentalReport
from agents.astrologer import get_astrologer, VedicAstrologerAgent, AstroReport
from agents.synthesizer import get_synthesizer, SynthesizerAgent


@dataclass
class Query:
    """User query for analysis."""
    symbol: str  # e.g., "BTC/USDT"
    side: str  # "buy" or "sell"
    interval: str  # timeframe for technical analysis
    birth_date: Optional[str]  # birth date for personalized astrology
    birth_time: Optional[str]  # birth time
    custom_weights: Optional[dict]  # custom weights for synthesis


@dataclass
class AnalysisResult:
    """Complete analysis result."""
    query: Query
    technical_report: TechnicalReport
    fundamental_report: FundamentalReport
    astrological_report: AstroReport
    synthesizer_report: Any  # Will be SynthesizerReport
    markdown_output: str
    timestamp: str


class Orchestrator:
    """
    Orchestrator for AstroFin Sentinel.
    
    Coordinates the multi-agent workflow:
    1. Parse user query
    2. Spawn parallel agents
    3. Collect reports
    4. Synthesize final recommendation
    """
    
    def __init__(self):
        self.technical_agent = get_technical_analyst()
        self.fundamental_agent = get_fundamental_analyst()
        self.synthesizer = get_synthesizer()
    
    def create_query(self, symbol: str, side: str = "buy",
                    interval: str = "1h",
                    birth_date: str = None,
                    birth_time: str = None,
                    weights: dict = None) -> Query:
        """Create a query object."""
        return Query(
            symbol=symbol,
            side=side,
            interval=interval,
            birth_date=birth_date,
            birth_time=birth_time,
            custom_weights=weights
        )
    
    async def analyze(self, query: Query) -> AnalysisResult:
        """
        Run complete analysis.
        
        Args:
            query: Query object with analysis parameters
            
        Returns:
            AnalysisResult with all reports and final output
        """
        # Initialize astrologer with birth data if provided
        if query.birth_date and query.birth_time:
            astrologer = get_astrologer(query.birth_date, query.birth_time)
        else:
            astrologer = get_astrologer()
        
        # Run agents in parallel (simulated with sequential for now)
        # In production, use asyncio.gather or similar
        
        # 1. Technical Analysis
        technical_report = self.technical_agent.analyze(
            symbol=query.symbol,
            interval=query.interval
        )
        
        # 2. Fundamental Analysis
        fundamental_report = self.fundamental_agent.analyze(
            symbol=query.symbol
        )
        
        # 3. Astrological Analysis
        astrological_report = astrologer.analyze(
            symbol=query.symbol,
            side=query.side
        )
        
        # 4. Synthesis
        synthesizer_report = self.synthesizer.synthesize(
            technical=technical_report,
            fundamental=fundamental_report,
            astrological=astrological_report,
            symbol=query.symbol
        )
        
        # 5. Generate markdown output
        markdown_output = self.synthesizer.to_markdown(synthesizer_report)
        
        return AnalysisResult(
            query=query,
            technical_report=technical_report,
            fundamental_report=fundamental_report,
            astrological_report=astrological_report,
            synthesizer_report=synthesizer_report,
            markdown_output=markdown_output,
            timestamp=datetime.now().isoformat()
        )
    
    def analyze_sync(self, query: Query) -> AnalysisResult:
        """
        Synchronous version of analyze.
        """
        # Initialize astrologer with birth data if provided
        if query.birth_date and query.birth_time:
            astrologer = get_astrologer(query.birth_date, query.birth_time)
        else:
            astrologer = get_astrologer()
        
        # 1. Technical Analysis
        technical_report = self.technical_agent.analyze(
            symbol=query.symbol,
            interval=query.interval
        )
        
        # 2. Fundamental Analysis
        fundamental_report = self.fundamental_agent.analyze(
            symbol=query.symbol
        )
        
        # 3. Astrological Analysis
        astrological_report = astrologer.analyze(
            symbol=query.symbol,
            side=query.side
        )
        
        # 4. Synthesis
        synthesizer_report = self.synthesizer.synthesize(
            technical=technical_report,
            fundamental=fundamental_report,
            astrological=astrological_report,
            symbol=query.symbol
        )
        
        # 5. Generate markdown output
        markdown_output = self.synthesizer.to_markdown(synthesizer_report)
        
        return AnalysisResult(
            query=query,
            technical_report=technical_report,
            fundamental_report=fundamental_report,
            astrological_report=astrological_report,
            synthesizer_report=synthesizer_report,
            markdown_output=markdown_output,
            timestamp=datetime.now().isoformat()
        )


# Global instance
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator


# Convenience function
def analyze_symbol(symbol: str, side: str = "buy",
                  interval: str = "1h",
                  birth_date: str = None,
                  birth_time: str = None) -> str:
    """
    Convenience function to analyze a symbol.
    
    Returns markdown-formatted report.
    """
    orch = get_orchestrator()
    
    query = orch.create_query(
        symbol=symbol,
        side=side,
        interval=interval,
        birth_date=birth_date,
        birth_time=birth_time
    )
    
    result = orch.analyze_sync(query)
    return result.markdown_output
