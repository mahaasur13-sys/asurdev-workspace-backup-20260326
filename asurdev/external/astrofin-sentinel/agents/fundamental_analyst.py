"""
Fundamental Analyst Agent for AstroFin Sentinel

Analyzes fundamental factors: news, on-chain metrics, macro factors.
"""

import json
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class FundamentalReport:
    """Output from Fundamental Analyst Agent."""
    verdict: str  # STRONG_BUY, BUY, NEUTRAL, SELL, STRONG_SELL
    strength: float  # 0.0 - 1.0
    factors: list  # [{"type": "positive|negative", "factor": "...", "impact": "HIGH|MEDIUM|LOW"}]
    risk_factors: list  # [{"risk": "...", "severity": "HIGH|MEDIUM|LOW"}]
    onchain_summary: dict  # tvl_trend, addresses_trend, exchange_flow
    news_sentiment: str  # BULLISH, BEARISH, NEUTRAL
    reasoning: str
    symbol: str = ""


class FundamentalAnalystAgent:
    """
    Fundamental Analyst Agent.
    
    Analyzes fundamental factors including:
    - News sentiment
    - On-chain metrics (TVL, addresses, flows)
    - Macro factors
    - Project fundamentals
    """
    
    def __init__(self):
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from file."""
        try:
            with open("prompts/fundamental_analyst.txt", "r") as f:
                return f.read()
        except FileNotFoundError:
            return "You are a fundamental analyst."
    
    def analyze(self, symbol: str, news: list = None, onchain: dict = None) -> FundamentalReport:
        """
        Perform fundamental analysis.
        
        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            news: Optional list of recent news items
            onchain: Optional on-chain metrics
            
        Returns:
            FundamentalReport with analysis results
        """
        # If no data provided, use placeholder/mock data
        if news is None:
            news = self._get_default_news(symbol)
        
        if onchain is None:
            onchain = self._get_default_onchain(symbol)
        
        # Analyze news sentiment
        sentiment, sentiment_strength = self._analyze_news(news)
        
        # Analyze on-chain metrics
        onchain_trends = self._analyze_onchain(onchain)
        
        # Generate verdict
        verdict, strength, factors, risks = self._generate_verdict(
            sentiment, sentiment_strength, onchain_trends, symbol
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            verdict, sentiment, onchain_trends, factors
        )
        
        return FundamentalReport(
            verdict=verdict,
            strength=strength,
            factors=factors,
            risk_factors=risks,
            onchain_summary=onchain_trends,
            news_sentiment=sentiment,
            reasoning=reasoning,
            symbol=symbol
        )
    
    def _get_default_news(self, symbol: str) -> list:
        """Get placeholder news data."""
        # In production, this would fetch from news APIs
        return [
            {"headline": f"{symbol} shows strong adoption", "sentiment": "positive"},
            {"headline": "Macro environment remains uncertain", "sentiment": "neutral"},
        ]
    
    def _get_default_onchain(self, symbol: str) -> dict:
        """Get placeholder on-chain data."""
        # In production, this would fetch from DeFiLlama, Glassnode, etc.
        return {
            "tvl_change_24h": 5.2,
            "active_addresses_change_7d": 12.5,
            "exchange_flow": "outflow",
            "funding_rate": 0.001,
            "open_interest_change_24h": 8.3
        }
    
    def _analyze_news(self, news: list) -> tuple:
        """Analyze news sentiment."""
        if not news:
            return "NEUTRAL", 0.5
        
        positive = sum(1 for n in news if n.get("sentiment") == "positive")
        negative = sum(1 for n in news if n.get("sentiment") == "negative")
        total = len(news)
        
        score = (positive - negative) / total if total > 0 else 0
        
        if score > 0.3:
            sentiment = "BULLISH"
            strength = 0.5 + score * 0.5
        elif score < -0.3:
            sentiment = "BEARISH"
            strength = 0.5 + abs(score) * 0.5
        else:
            sentiment = "NEUTRAL"
            strength = 0.5
        
        return sentiment, min(strength, 0.95)
    
    def _analyze_onchain(self, onchain: dict) -> dict:
        """Analyze on-chain metrics."""
        trends = {}
        
        # TVL trend
        tvl_change = onchain.get("tvl_change_24h", 0)
        if tvl_change > 5:
            trends["tvl_trend"] = "UP"
        elif tvl_change < -5:
            trends["tvl_trend"] = "DOWN"
        else:
            trends["tvl_trend"] = "SIDEWAYS"
        
        # Active addresses trend
        addr_change = onchain.get("active_addresses_change_7d", 0)
        if addr_change > 10:
            trends["addresses_trend"] = "UP"
        elif addr_change < -10:
            trends["addresses_trend"] = "DOWN"
        else:
            trends["addresses_trend"] = "SIDEWAYS"
        
        # Exchange flow
        trends["exchange_flow"] = onchain.get("exchange_flow", "NEUTRAL")
        
        return trends
    
    def _generate_verdict(self, sentiment: str, sentiment_strength: float,
                          onchain: dict, symbol: str) -> tuple:
        """Generate fundamental verdict."""
        score = sentiment_strength
        
        # Adjust based on on-chain
        if onchain.get("tvl_trend") == "UP":
            score += 0.1
        elif onchain.get("tvl_trend") == "DOWN":
            score -= 0.1
        
        if onchain.get("exchange_flow") == "outflow":
            score += 0.1
        elif onchain.get("exchange_flow") == "inflow":
            score -= 0.1
        
        # Cap score
        score = max(0.2, min(0.9, score))
        
        # Determine verdict
        if score >= 0.75:
            verdict = "STRONG_BUY"
        elif score >= 0.6:
            verdict = "BUY"
        elif score >= 0.45:
            verdict = "NEUTRAL"
        elif score >= 0.3:
            verdict = "SELL"
        else:
            verdict = "STRONG_SELL"
        
        # Generate factors
        factors = []
        if sentiment == "BULLISH":
            factors.append({
                "type": "positive",
                "factor": f"{symbol} has positive news sentiment",
                "impact": "HIGH"
            })
        elif sentiment == "BEARISH":
            factors.append({
                "type": "negative",
                "factor": f"{symbol} has negative news sentiment",
                "impact": "HIGH"
            })
        
        if onchain.get("tvl_trend") == "UP":
            factors.append({
                "type": "positive",
                "factor": "TVL is growing, indicating increased usage",
                "impact": "MEDIUM"
            })
        elif onchain.get("tvl_trend") == "DOWN":
            factors.append({
                "type": "negative",
                "factor": "TVL is declining",
                "impact": "MEDIUM"
            })
        
        # Risk factors
        risks = []
        if sentiment == "BEARISH":
            risks.append({"risk": "Negative news sentiment", "severity": "HIGH"})
        if onchain.get("exchange_flow") == "inflow":
            risks.append({"risk": "Crypto flowing to exchanges (selling pressure)", "severity": "MEDIUM"})
        
        return verdict, score, factors, risks
    
    def _generate_reasoning(self, verdict: str, sentiment: str,
                           onchain: dict, factors: list) -> str:
        """Generate reasoning summary."""
        reasoning = f"Verdict: {verdict}. "
        reasoning += f"News sentiment: {sentiment}. "
        
        if factors:
            top_factor = factors[0]
            reasoning += f"Key factor: {top_factor['factor']}."
        
        return reasoning
    
    def to_dict(self, report: FundamentalReport) -> dict:
        """Convert report to dictionary."""
        return asdict(report)


# Global instance
_fundamental_agent = None

def get_fundamental_analyst() -> FundamentalAnalystAgent:
    global _fundamental_agent
    if _fundamental_agent is None:
        _fundamental_agent = FundamentalAnalystAgent()
    return _fundamental_agent
