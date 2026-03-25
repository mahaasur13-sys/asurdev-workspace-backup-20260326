"""Smart Money Concepts - Order Blocks, FVG, Liquidity Sweeps"""
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np

@dataclass
class Candle:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class OrderBlock:
    index: int
    candle: Candle
    direction: str
    strength: float
    is_fair_value_gap: bool = False
    fvg_start: Optional[float] = None
    fvg_end: Optional[float] = None

@dataclass
class LiquidityZone:
    level: float
    zone_type: str
    sweep_index: Optional[int] = None
    returned: bool = False

@dataclass
class MarketPhase:
    phase: str
    confidence: float
    evidence: List[str]

@dataclass
class SMCSignal:
    signal_type: str
    direction: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    confidence: float
    explanation: str

class SmartMoneyAnalyzer:
    def __init__(self, candles: List[Candle]):
        self.candles = candles
        self.order_blocks: List[OrderBlock] = []
        self.liquidity_zones: List[LiquidityZone] = []
        self.swing_highs: List[int] = []
        self.swing_lows: List[int] = []
    
    def find_swing_points(self, lookback: int = 5) -> Tuple[List[int], List[int]]:
        swing_highs = []
        swing_lows = []
        for i in range(lookback, len(self.candles) - lookback):
            is_high = all(self.candles[j].high <= self.candles[i].high 
                         for j in range(max(0, i-lookback), min(len(self.candles), i+lookback+1)) if j != i)
            is_low = all(self.candles[j].low >= self.candles[i].low 
                        for j in range(max(0, i-lookback), min(len(self.candles), i+lookback+1)) if j != i)
            if is_high:
                swing_highs.append(i)
            if is_low:
                swing_lows.append(i)
        self.swing_highs = swing_highs
        self.swing_lows = swing_lows
        return swing_highs, swing_lows
    
    def detect_order_blocks(self, min_ratio: float = 1.5) -> List[OrderBlock]:
        self.order_blocks = []
        if len(self.candles) < 3:
            return self.order_blocks
        for i in range(2, len(self.candles)):
            c1, c2 = self.candles[i-1], self.candles[i]
            c1_range = c1.high - c1.low
            if c1.close > c1.open and c1_range > 0:
                move = c2.close - c2.open
                if move > c1_range * min_ratio:
                    self.order_blocks.append(OrderBlock(
                        index=i-1, candle=c1, direction='bullish',
                        strength=min(move / c1_range, 1.0)
                    ))
            elif c1.close < c1.open and c1_range > 0:
                move = c2.open - c2.close
                if move > c1_range * min_ratio:
                    self.order_blocks.append(OrderBlock(
                        index=i-1, candle=c1, direction='bearish',
                        strength=min(move / c1_range, 1.0)
                    ))
        return self.order_blocks
    
    def detect_fvg(self) -> List[OrderBlock]:
        fvg_list = []
        for i in range(1, len(self.candles) - 1):
            c_prev, c_curr = self.candles[i-1], self.candles[i]
            if c_curr.low > c_prev.high:
                gap = c_curr.low - c_prev.high
                self.order_blocks.append(OrderBlock(
                    index=i, candle=c_curr, direction='bullish',
                    strength=min(gap / c_curr.close * 10, 1.0),
                    is_fair_value_gap=True, fvg_start=c_prev.high, fvg_end=c_curr.low
                ))
            elif c_curr.high < c_prev.low:
                gap = c_prev.low - c_curr.high
                self.order_blocks.append(OrderBlock(
                    index=i, candle=c_curr, direction='bearish',
                    strength=min(gap / c_curr.close * 10, 1.0),
                    is_fair_value_gap=True, fvg_start=c_curr.high, fvg_end=c_prev.low
                ))
        return fvg_list
    
    def detect_liquidity_sweeps(self) -> List[LiquidityZone]:
        self.liquidity_zones = []
        self.find_swing_points()
        for i in range(len(self.candles)):
            c = self.candles[i]
            for sh in self.swing_highs[-5:]:
                if sh >= i:
                    continue
                level = self.candles[sh].high
                if c.high > level * 1.001:
                    returned = i + 1 < len(self.candles) and self.candles[i+1].close < level
                    self.liquidity_zones.append(LiquidityZone(level, 'swing_high', i, returned))
            for sl in self.swing_lows[-5:]:
                if sl >= i:
                    continue
                level = self.candles[sl].low
                if c.low < level * 0.999:
                    returned = i + 1 < len(self.candles) and self.candles[i+1].close > level
                    self.liquidity_zones.append(LiquidityZone(level, 'swing_low', i, returned))
        return self.liquidity_zones
    
    def detect_market_phase(self) -> MarketPhase:
        if len(self.candles) < 20:
            return MarketPhase('unknown', 0.0, ['Not enough data'])
        recent = self.candles[-20:]
        ranges = [c.high - c.low for c in recent]
        volumes = [c.volume for c in recent]
        avg_range = np.mean(ranges)
        price_change = (recent[-1].close - recent[0].open) / recent[0].open
        if abs(price_change) < 0.02:
            return MarketPhase('accumulation', 0.7, ['Range-bound', 'Low volatility'])
        elif price_change > 0.03:
            return MarketPhase('distribution', 0.6, ['Strong uptrend', 'Potential reversal'])
        elif price_change < -0.03:
            return MarketPhase('accumulation', 0.6, ['Strong downtrend', 'Potential accumulation'])
        return MarketPhase('manipulation', 0.5, ['Mixed signals'])
    
    def generate_signals(self) -> List[SMCSignal]:
        signals = []
        self.find_swing_points()
        self.detect_order_blocks()
        self.detect_fvg()
        self.detect_liquidity_sweeps()
        for ob in self.order_blocks[-3:]:
            if ob.direction == 'bullish':
                entry = ob.candle.low * 1.001
                stop = ob.candle.low * 0.99
                target = entry + (entry - stop) * 2
                signals.append(SMCSignal(
                    'order_block', 'bullish', entry, stop, target, 2.0, ob.strength * 0.8,
                    f"Bullish OB at {ob.candle.low:.2f}"
                ))
            else:
                entry = ob.candle.high * 0.999
                stop = ob.candle.high * 1.01
                target = entry - (stop - entry) * 2
                signals.append(SMCSignal(
                    'order_block', 'bearish', entry, stop, target, 2.0, ob.strength * 0.8,
                    f"Bearish OB at {ob.candle.high:.2f}"
                ))
        for lz in self.liquidity_zones[-2:]:
            if lz.returned:
                if lz.zone_type == 'swing_high':
                    signals.append(SMCSignal(
                        'liquidity_sweep', 'bearish', lz.level * 0.998, lz.level * 1.005, lz.level * 0.97, 1.5, 0.7,
                        f"Swing high sweep at {lz.level:.2f}"
                    ))
                else:
                    signals.append(SMCSignal(
                        'liquidity_sweep', 'bullish', lz.level * 1.002, lz.level * 0.995, lz.level * 1.03, 1.5, 0.7,
                        f"Swing low sweep at {lz.level:.2f}"
                    ))
        return signals
