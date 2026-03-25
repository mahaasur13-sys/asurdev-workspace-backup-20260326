"""
Simplified Orchestrator — asurdev Sentinel v2.0
Coordinates all agents and produces C.L.E.A.R. verdicts
"""
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from ._impl import (
    AgentResponse,
    MarketAnalyst,
    BullResearcher,
    BearResearcher,
    AstrologerAgent,
    CycleAgent,
    Synthesizer,
    AndrewsAgent,
    DowTheoryAgent,
    GannAgent,
    MerrimanAgent,
    MeridianAgent,
    MerrimanCycleCalculator,
    MeridianNatalChart,
)


@dataclass
class SentinelConfig:
    """Sentinel configuration"""
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = os.environ.get("asurdev_MODEL", "qwen3-coder:30b-a3b")
    core_pc: str = "192.168.10.10"
    rk3576: str = "192.168.20.40"
    ts_signals_dir: str = "/home/workspace/asurdevSentinel/data/ts_signals"
    latitude: float = 28.6139
    longitude: float = 77.2090
    agent_timeout: int = 120
    enable_cycle_agent: bool = True


@dataclass
class AnalysisResult:
    """Complete analysis result"""
    timestamp: str
    symbol: str
    market_price: float
    agents_result: Dict[str, AgentResponse]
    synthesis: AgentResponse
    config: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        # Convert AgentResponse objects
        for k, v in d.get("agents_result", {}).items():
            if hasattr(v, "to_dict"):
                d["agents_result"][k] = v.to_dict()
        if hasattr(d["synthesis"], "to_dict"):
            d["synthesis"] = d["synthesis"].to_dict()
        # Convert datetime
        if isinstance(d.get("timestamp"), datetime):
            d["timestamp"] = d["timestamp"].isoformat()
        return d
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str, indent=2)


class Orchestrator:
    """
    Main orchestrator — coordinates all agents
    
    Usage:
        orchestrator = Orchestrator()
        result = await orchestrator.analyze("BTC")
    """
    
    def __init__(self, config: Optional[SentinelConfig] = None):
        self.config = config or SentinelConfig()
        
        # Initialize agents with config
        self.market = MarketAnalyst(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=self.config.agent_timeout,
        )
        
        self.bull = BullResearcher(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=self.config.agent_timeout,
        )
        
        self.bear = BearResearcher(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=self.config.agent_timeout,
        )
        
        self.astro = AstrologerAgent(
            lat=self.config.latitude,
            lon=self.config.longitude,
            model="gemma:2b",  # Light model for RK3576
            base_url=f"http://{self.config.rk3576}:11434",
            timeout=60,
        )
        
        if self.config.enable_cycle_agent:
            self.cycle = CycleAgent(
                signals_dir=self.config.ts_signals_dir,
                timeout=30,
            )
        else:
            self.cycle = None
        
        # Technical analysis agents
        self.dow = DowTheoryAgent(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=60,
        )
        
        self.andrews = AndrewsAgent(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=60,
        )
        
        self.gann = GannAgent(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=60,
        )
        
        # Synthesizer
        self.synth = Synthesizer(
            model=self.config.default_model,
            base_url=self.config.ollama_base_url,
            timeout=self.config.agent_timeout,
        )
    
    async def analyze(self, symbol: str, action: str = "hold") -> AnalysisResult:
        """
        Run complete analysis for symbol
        
        Args:
            symbol: BTC, ETH, etc.
            action: buy, sell, hold (for astrology focus)
        
        Returns:
            AnalysisResult with all agent responses and synthesis
        """
        print(f"🔍 Analyzing {symbol}...")
        
        # Build context
        context = {
            "symbol": symbol.upper(),
            "action": action,
            "market_data": self._get_market_data(symbol),
            "location": (self.config.latitude, self.config.longitude),
        }
        
        # Run agents in parallel
        tasks = [
            ("market", self.market.analyze(context)),
            ("bull", self.bull.analyze(context)),
            ("bear", self.bear.analyze(context)),
            ("astro", self.astro.analyze(context)),
            ("dow", self.dow.analyze(context)),
            ("andrews", self.andrews.analyze(context)),
            ("gann", self.gann.analyze(context)),
        ]
        
        if self.cycle:
            tasks.append(("cycle", self.cycle.analyze(context)))
        
        # Execute all
        results = {}
        for name, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=self.config.agent_timeout)
                results[name] = result
                print(f"  ✓ {name}: {result.signal} ({result.confidence}%)")
            except asyncio.TimeoutError:
                print(f"  ⏱ {name}: Timeout")
                results[name] = AgentResponse(
                    agent_name=name,
                    signal="ERROR",
                    confidence=0,
                    summary="Timeout"
                )
            except Exception as e:
                print(f"  ✗ {name}: {e}")
                results[name] = AgentResponse(
                    agent_name=name,
                    signal="ERROR",
                    confidence=0,
                    summary=str(e)
                )
        
        # Synthesize
        print("🧠 Synthesizing...")
        synthesis = await self.synth.synthesize(
            market=results.get("market"),
            bull=results.get("bull"),
            bear=results.get("bear"),
            astro=results.get("astro"),
            cycle=results.get("cycle"),
        )
        
        return AnalysisResult(
            timestamp=datetime.now().isoformat(),
            symbol=symbol.upper(),
            market_price=context["market_data"].get("current_price", 0),
            agents_result=results,
            synthesis=synthesis,
            config={
                "model": self.config.default_model,
                "timeout": self.config.agent_timeout,
            }
        )
    
    def _get_market_data(self, symbol: str) -> Dict:
        """Get market data (simplified - no API call)"""
        # In production, call CoinGecko
        default_prices = {
            "BTC": 67500,
            "ETH": 3400,
            "SOL": 145,
            "BNB": 580,
            "XRP": 0.52,
            "ADA": 0.45,
            "DOGE": 0.12,
            "DOT": 7.20,
        }
        return {
            "symbol": symbol.upper(),
            "current_price": default_prices.get(symbol.upper(), 100),
            "price_change_pct": 2.5,
            "volume_24h": 1_000_000_000,
            "high_24h": 68000,
            "low_24h": 66000,
        }
    
    async def analyze_batch(self, symbols: List[str]) -> Dict[str, AnalysisResult]:
        """Analyze multiple symbols in parallel"""
        tasks = [self.analyze(s) for s in symbols]
        results = await asyncio.gather(*tasks)
        return dict(zip(symbols, results))


async def quick_analyze(symbol: str) -> AnalysisResult:
    """Quick single-symbol analysis"""
    orch = Orchestrator()
    return await orch.analyze(symbol)


if __name__ == "__main__":
    # Demo
    result = asyncio.run(quick_analyze("BTC"))
    print("\n📊 Result:")
    print(result.to_json())
