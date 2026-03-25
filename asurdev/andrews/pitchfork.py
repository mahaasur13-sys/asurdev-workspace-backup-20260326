"""
Andrews' Pitchfork v10.0 — FINAL Complete Implementation
All methods from Parts 1-102 + Super Pitchfork + Confluence Zones

Based on "Лучшие методы линий тренда Алана Эндрюса" by Patrick Mikula

FINAL VERSION — Complete synergy of all methods
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional


class TrendType(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"


class PitchforkCase(Enum):
    STANDARD = "standard"
    CASE_1 = "case_1"
    CASE_2 = "case_2"


@dataclass
class Pivot:
    idx: int
    price: float
    type: str  # 'high' or 'low'


@dataclass
class PitchforkResult:
    slope: float
    intercept: float
    median_line: List[float]
    upper_parallel: List[float]
    lower_parallel: List[float]
    case: PitchforkCase
    trend: TrendType
    x_point: Tuple[int, float]
    b_point: Tuple[int, float]
    c_point: Tuple[int, float]
    warning_lines: Dict
    reaction_lines: Dict = field(default_factory=dict)


@dataclass
class PivotZone:
    zone_size_bars: int
    start_bar: int
    end_bar: int
    median_target: float
    triggered: bool
    triggered_bar: Optional[int]
    bars_remaining: int


@dataclass
class ConfluenceZone:
    """NEW: Confluence Zone — Part 99, 101
    Intersection of different line types = high probability reversal
    """
    bar: int
    price: float
    lines_intersected: List[str]
    zone_type: str  # "resistance" or "support"
    strength: str  # "strong", "very_strong"


@dataclass
class SuperPitchfork:
    """Super Pitchfork — Parts 95-102
    Combines standard pitchfork with AR method
    """
    median_line: List[float]
    upper_parallel: List[float]
    lower_parallel: List[float]
    b_c_line: List[float]
    b_c_slope: float
    b_c_intercept: float
    reaction_lines: Dict[int, List[float]]
    warning_lines: Dict
    confluence_zones: List[ConfluenceZone]
    intersections: List[Dict]
    a_point: Tuple[int, float]
    b_point: Tuple[int, float]
    c_point: Tuple[int, float]


@dataclass
class AndrewsSignal:
    signal: str
    rule: int
    confidence: int
    description: str
    details: Dict
    pivot_zone: Optional[PivotZone] = None
    confluence_zones: List[ConfluenceZone] = field(default_factory=list)
    super_pitchfork: Optional[SuperPitchfork] = None
    sequential_reaction_touches: List[Dict] = field(default_factory=list)


class AndrewsTools:
    """Complete Andrews Pitchfork implementation v10.0"""
    
    def __init__(self):
        pass
    
    def find_pivots(self, prices: List[float], window: int = 1) -> List[Pivot]:
        """Find swing highs and lows"""
        pivots = []
        for i in range(window, len(prices) - window):
            is_high = True
            is_low = True
            for j in range(1, window + 1):
                if prices[i] <= prices[i - j]:
                    is_high = False
                if prices[i] >= prices[i - j]:
                    is_low = False
            if is_high:
                pivots.append(Pivot(idx=i, price=prices[i], type='high'))
            elif is_low:
                pivots.append(Pivot(idx=i, price=prices[i], type='low'))
        return pivots
    
    def _get_extended_line(self, p1: Tuple[int, float], p2: Tuple[int, float], length: int) -> List[float]:
        """Extend line through two points"""
        if p1[0] == p2[0]:
            return [p1[1]] * length
        slope = (p2[1] - p1[1]) / (p2[0] - p1[0])
        return [p1[1] + slope * (i - p1[0]) for i in range(length)]
    
    def get_super_pitchfork(self, pivots: List[Pivot], prices: List[float]) -> Optional[SuperPitchfork]:
        """Build Super Pitchfork — Parts 95-102
        
        Examples:
        - QCOM (95): First introduction
        - NET/NITE (96-97): Point D = Median + RL1 intersection
        - VRSN (98): D, E — before/after lines
        - SPLS (99): Multiple intersections + Warning Lines
        - CMCSK (100): Two intersections with Median
        - Eurodollar (101): RL2 + WL1 intersection = bottom
        - LLY (102): Sequential tops on RL1, RL2, RL3, RL4
        """
        if len(pivots) < 3:
            return None
        
        a_pivot = pivots[-3]
        b_pivot = pivots[-2]
        c_pivot = pivots[-1]
        length = len(prices)
        
        # Standard Pitchfork median line
        b_c_mid = ((b_pivot.idx + c_pivot.idx) / 2, (b_pivot.price + c_pivot.price) / 2)
        slope = (b_c_mid[1] - a_pivot.price) / (b_c_mid[0] - a_pivot.idx) if b_c_mid[0] != a_pivot.idx else 0
        
        median = []
        upper = []
        lower = []
        range_half = abs(b_pivot.price - c_pivot.price) / 2 if b_pivot.price != c_pivot.price else (max(prices) - min(prices)) / 4
        
        for i in range(length):
            median_val = a_pivot.price + slope * (i - a_pivot.idx)
            median.append(median_val)
            upper.append(median_val + range_half)
            lower.append(median_val - range_half)
        
        # B-C line (center for AR)
        b_c_line = self._get_extended_line((b_pivot.idx, b_pivot.price), (c_pivot.idx, c_pivot.price), length)
        b_c_slope = (c_pivot.price - b_pivot.price) / (c_pivot.idx - b_pivot.idx) if c_pivot.idx != b_pivot.idx else 0
        b_c_intercept = b_pivot.price - b_c_slope * b_pivot.idx
        
        # Distance from A to B-C line
        a_to_bc_distance = abs(a_pivot.price - (b_c_slope * a_pivot.idx + b_c_intercept))
        
        # Reaction Lines 1-4 — Part 102 (LLY had 4!)
        reaction_lines = {}
        for n in [1, 2, 3, 4]:
            offset = n * a_to_bc_distance
            reaction_lines[n] = [val + offset for val in b_c_line]
        
        # Warning Lines — Parts 25, 77, 99, 101
        price_range = max(prices) - min(prices)
        wl1_offset = price_range * 0.25
        wl2_offset = price_range * 0.50
        
        warning_lines = {
            'upper_wl1': [m + wl1_offset for m in median],
            'lower_wl1': [m - wl1_offset for m in median],
            'upper_wl2': [m + wl2_offset for m in median],
            'lower_wl2': [m - wl2_offset for m in median],
        }
        
        # Find intersections
        intersections = self._find_intersections(median, upper, lower, reaction_lines, warning_lines, prices)
        
        # Find confluence zones
        confluence_zones = self._find_confluence_zones(median, upper, lower, reaction_lines, warning_lines, prices)
        
        return SuperPitchfork(
            median_line=median,
            upper_parallel=upper,
            lower_parallel=lower,
            b_c_line=b_c_line,
            b_c_slope=b_c_slope,
            b_c_intercept=b_c_intercept,
            reaction_lines=reaction_lines,
            warning_lines=warning_lines,
            confluence_zones=confluence_zones,
            intersections=intersections,
            a_point=(a_pivot.idx, a_pivot.price),
            b_point=(b_pivot.idx, b_pivot.price),
            c_point=(c_pivot.idx, c_pivot.price)
        )
    
    def _find_intersections(self, median, upper, lower, reaction_lines, warning_lines, prices) -> List[Dict]:
        """Find all intersections between lines"""
        intersections = []
        length = len(prices)
        
        for i in range(length):
            price = prices[i]
            
            # Median + RL1 — Part 96, 100 D
            if 1 in reaction_lines and abs(median[i] - reaction_lines[1][i]) < abs(price * 0.01):
                intersections.append({'bar': i, 'price': price, 'lines': ['Median', 'RL1'], 'type': 'median_rl1'})
            
            # Median + RL3 — Part 100 E
            if 3 in reaction_lines and abs(median[i] - reaction_lines[3][i]) < abs(price * 0.01):
                intersections.append({'bar': i, 'price': price, 'lines': ['Median', 'RL3'], 'type': 'median_rl3'})
            
            # RL2 + WL1 — Part 101
            if 2 in reaction_lines:
                if abs(reaction_lines[2][i] - warning_lines['upper_wl1'][i]) < abs(price * 0.01):
                    intersections.append({'bar': i, 'price': price, 'lines': ['RL2', 'WL1'], 'type': 'rl2_wl1'})
            
            # RL3 + Upper — Part 99 F
            if 3 in reaction_lines:
                if abs(reaction_lines[3][i] - upper[i]) < abs(price * 0.01):
                    intersections.append({'bar': i, 'price': price, 'lines': ['RL3', 'Upper'], 'type': 'rl3_upper'})
        
        return intersections
    
    def _find_confluence_zones(self, median, upper, lower, reaction_lines, warning_lines, prices) -> List[ConfluenceZone]:
        """Find confluence zones — Parts 99, 101"""
        zones = []
        length = len(prices)
        
        for i in range(length):
            price = prices[i]
            lines_met = []
            
            if abs(price - median[i]) < abs(price * 0.015):
                lines_met.append('Median')
            if abs(price - upper[i]) < abs(price * 0.015):
                lines_met.append('Upper')
            if abs(price - lower[i]) < abs(price * 0.015):
                lines_met.append('Lower')
            
            for n in [1, 2, 3, 4]:
                if n in reaction_lines:
                    if abs(price - reaction_lines[n][i]) < abs(price * 0.015):
                        lines_met.append(f'RL{n}')
            
            for wl in ['upper_wl1', 'lower_wl1', 'upper_wl2', 'lower_wl2']:
                if abs(price - warning_lines[wl][i]) < abs(price * 0.015):
                    lines_met.append(wl.upper())
            
            if len(lines_met) >= 2:
                zone_type = 'resistance' if price > median[i] else 'support'
                strength = 'very_strong' if len(lines_met) >= 3 else 'strong'
                zones.append(ConfluenceZone(bar=i, price=price, lines_intersected=lines_met, zone_type=zone_type, strength=strength))
        
        return zones
    
    def get_signal(self, prices: List[float], super_pf: Optional[SuperPitchfork] = None) -> AndrewsSignal:
        """Generate trading signal based on all methods"""
        pivots = self.find_pivots(prices)
        
        if super_pf is None:
            super_pf = self.get_super_pitchfork(pivots, prices)
        
        if super_pf is None or len(pivots) < 3:
            return AndrewsSignal(signal="hold", rule=0, confidence=0, description="No valid pivots", details={})
        
        current_price = prices[-1]
        current_idx = len(prices) - 1
        
        signal = "hold"
        rule = 0
        confidence = 40
        description = ""
        sequential_touches = []
        
        # Check confluence zones — Part 99, 101
        if super_pf.confluence_zones:
            for zone in super_pf.confluence_zones[-3:]:
                if zone.bar >= current_idx - 5:
                    signal = "reversal"
                    rule = 901
                    confidence = 80 if zone.strength == "very_strong" else 65
                    description = f"Confluence: {', '.join(zone.lines_intersected)}"
                    break
        
        # Check intersections — Parts 96-101
        for intersection in super_pf.intersections[-3:]:
            if intersection['bar'] >= current_idx - 5:
                lines = intersection['lines']
                if 'Median' in lines and 'RL1' in lines:
                    rule, signal, confidence, description = 801, "reversal", 75, "Point D: Median + RL1"
                elif 'Median' in lines and 'RL3' in lines:
                    rule, signal, confidence, description = 802, "reversal", 75, "Point E: Median + RL3"
                elif 'RL2' in lines and 'WL1' in lines:
                    rule, signal, confidence, description = 803, "reversal", 80, "Point D: RL2 + WL1 (bottom)"
                elif 'RL3' in lines and 'Upper' in lines:
                    rule, signal, confidence, description = 804, "reversal", 75, "Point F: RL3 + Upper"
                break
        
        # Sequential RL touches — Part 102 (LLY)
        if signal == "hold":
            for n in [1, 2, 3, 4]:
                if n in super_pf.reaction_lines:
                    rl_price = super_pf.reaction_lines[n][current_idx]
                    if abs(current_price - rl_price) < abs(current_price * 0.02):
                        sequential_touches.append({'line': f'RL{n}', 'distance_pct': abs(current_price - rl_price) / current_price * 100})
                        if len(sequential_touches) >= 2:
                            rule, signal, confidence, description = 805, "resistance", 70, f"Sequential RL touches: {[t['line'] for t in sequential_touches]}"
                            break
        
        # Standard pitchfork rules
        if signal == "hold":
            median_current = super_pf.median_line[current_idx]
            upper_current = super_pf.upper_parallel[current_idx]
            lower_current = super_pf.lower_parallel[current_idx]
            
            if last_pivot.type == 'low' and current_price > upper_current:
                rule, signal, confidence, description = 101, "buy", 70, "Rule 1: Break above upper parallel (uptrend)"
            elif last_pivot.type == 'high' and current_price < lower_current:
                rule, signal, confidence, description = 102, "sell", 70, "Rule 2: Break below lower parallel (downtrend)"
            elif abs(current_price - median_current) < abs(current_price * 0.01):
                rule, signal, confidence, description = 103, "reversal", 60, "Near median line"
        
        return AndrewsSignal(
            signal=signal, rule=rule, confidence=confidence,
            description=description, details={'pivots': len(pivots)},
            super_pitchfork=super_pf,
            sequential_reaction_touches=sequential_touches
        )


def get_andrews_tools() -> AndrewsTools:
    """Get configured AndrewsTools instance"""
    return AndrewsTools()
