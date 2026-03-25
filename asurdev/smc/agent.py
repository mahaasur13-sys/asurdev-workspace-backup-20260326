"""Smart Money Concepts Agent for asurdev Sentinel"""
from typing import Dict, Any, List, Optional
from dataclasses import asdict
import numpy as np

from .smart_money import (
    SmartMoneyAnalyzer, Candle, SMCSignal, MarketPhase,
    OrderBlock, LiquidityZone
)

class SMCAgent:
    """Institutional Trading Signals Agent"""
    
    def __init__(self):
        self.name = "SMC_Agent"
        self.description = "Smart Money Concepts - Order Blocks, FVG, Liquidity Sweeps"
    
    def analyze(self, candles: List[Candle], symbol: str = "UNKNOWN") -> Dict[str, Any]:
        """Analyze market for institutional trading opportunities"""
        analyzer = SmartMoneyAnalyzer(candles)
        
        # Detect all patterns
        swing_highs, swing_lows = analyzer.find_swing_points()
        order_blocks = analyzer.detect_order_blocks()
        fvg = analyzer.detect_fvg()
        liquidity = analyzer.detect_liquidity_sweeps()
        phase = analyzer.detect_market_phase()
        signals = analyzer.generate_signals()
        
        # Format results
        return {
            "symbol": symbol,
            "agent": self.name,
            "market_phase": {
                "phase": phase.phase,
                "confidence": phase.confidence,
                "evidence": phase.evidence
            },
            "swing_points": {
                "swing_highs": [analyzer.candles[i].high for i in swing_highs[-5:]],
                "swing_lows": [analyzer.candles[i].low for i in swing_lows[-5:]]
            },
            "order_blocks": [
                {
                    "index": ob.index,
                    "direction": ob.direction,
                    "level": ob.candle.low if ob.direction == 'bullish' else ob.candle.high,
                    "strength": ob.strength,
                    "is_fvg": ob.is_fair_value_gap
                }
                for ob in order_blocks[-5:]
            ],
            "liquidity_zones": [
                {
                    "level": lz.level,
                    "type": lz.zone_type,
                    "swept": lz.sweep_index is not None,
                    "returned": lz.returned
                }
                for lz in liquidity[-5:]
            ],
            "signals": [
                {
                    "type": s.signal_type,
                    "direction": s.direction,
                    "entry": s.entry,
                    "stop_loss": s.stop_loss,
                    "take_profit": s.take_profit,
                    "risk_reward": s.risk_reward,
                    "confidence": s.confidence,
                    "explanation": s.explanation
                }
                for s in signals
            ],
            "summary": self._generate_summary(signals, phase)
        }
    
    def _generate_summary(self, signals: List[SMCSignal], phase: MarketPhase) -> str:
        if not signals:
            return f"Phase: {phase.phase}. No clear signals."
        
        bullish = [s for s in signals if s.direction == 'bullish']
        bearish = [s for s in signals if s.direction == 'bearish']
        
        summary = f"Phase: {phase.phase.upper()} ({phase.confidence:.0%} confidence). "
        if bullish and bearish:
            summary += f"Bullish: {len(bullish)}, Bearish: {len(bearish)}."
        elif bullish:
            summary += f"Bullish bias: {len(bullish)} signals."
        elif bearish:
            summary += f"Bearish bias: {len(bearish)} signals."
        
        return summary

def get_smc_agent() -> SMCAgent:
    return SMCAgent()
