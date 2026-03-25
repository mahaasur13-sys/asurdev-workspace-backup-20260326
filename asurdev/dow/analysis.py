"""
Dow Theory — Trend Analysis for asurdev Sentinel
Based on Charles Dow's principles (1900-1902)
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class TrendResult:
    """Result of trend analysis"""
    trend_type: str  # "bullish", "bearish", "neutral"
    phase: str  # "accumulation", "participation", "distribution", "euphoria"
    strength: float  # 0.0 - 1.0
    confirmed: bool  # Price + Volume confirmation
    details: Dict


@dataclass
class DowSignal:
    """Dow Theory signal"""
    signal_type: str  # "primary_trend", "phase_change", "reversal"
    direction: str  # "bullish", "bearish"
    confidence: float  # 0-100
    description: str
    indices_confirm: bool


class DowTheoryAnalyzer:
    """
    Implements Dow Theory principles:
    1. Market discounts everything
    2. Three types of trends (Primary, Secondary, Minor)
    3. Three phases (Accumulation, Participation, Distribution)
    4. Indices must confirm each other
    5. Volume confirms trend
    6. Trend persists until reversal
    """
    
    def __init__(self):
        self.name = "DowTheory"
    
    def analyze(
        self,
        price_data: List[float],
        volumes: List[float],
        high_prices: List[float],
        low_prices: List[float],
        djia_prices: Optional[List[float]] = None,  # Optional confirmation index
        djta_prices: Optional[List[float]] = None   # Optional transport index
    ) -> TrendResult:
        """
        Analyze market using Dow Theory.
        
        Args:
            price_data: List of closing prices
            volumes: List of volumes
            high_prices: List of high prices
            low_prices: List of low prices
            djia_prices: Optional DJI prices for confirmation
            djta_prices: Optional DJTA prices for confirmation
        
        Returns:
            TrendResult with trend type, phase, and confirmation
        """
        if len(price_data) < 20:
            return TrendResult(
                trend_type="neutral",
                phase="unknown",
                strength=0.0,
                confirmed=False,
                details={"error": "Insufficient data (need 20+ points)"}
            )
        
        # Step 1: Calculate moving averages
        ma_20 = self._sma(price_data, 20)
        ma_50 = self._sma(price_data, 50) if len(price_data) >= 50 else price_data[-1]
        
        # Step 2: Identify swing highs/lows
        swings = self._identify_swings(high_prices, low_prices)
        
        # Step 3: Determine primary trend
        primary_trend = self._determine_trend(swings, price_data)
        
        # Step 4: Identify current phase
        phase = self._identify_phase(price_data, volumes, primary_trend)
        
        # Step 5: Check volume confirmation
        volume_confirmed = self._check_volume_confirmation(price_data, volumes, primary_trend)
        
        # Step 6: Check index confirmation (if available)
        indices_confirm = True
        if djia_prices and djta_prices:
            indices_confirm = self._check_indices_confirmation(djia_prices, djta_prices)
        
        # Overall confirmation
        confirmed = volume_confirmed and indices_confirm
        
        return TrendResult(
            trend_type=primary_trend,
            phase=phase,
            strength=self._calculate_strength(swings, price_data),
            confirmed=confirmed,
            details={
                "ma_20": ma_20,
                "ma_50": ma_50,
                "swing_highs": len([s for s in swings if s["type"] == "high"]),
                "swing_lows": len([s for s in swings if s["type"] == "low"]),
                "volume_confirmed": volume_confirmed,
                "indices_confirmed": indices_confirm
            }
        )
    
    def _sma(self, data: List[float], period: int) -> float:
        """Simple Moving Average"""
        if len(data) < period:
            return sum(data) / len(data)
        return sum(data[-period:]) / period
    
    def _identify_swings(self, highs: List[float], lows: List[float]) -> List[Dict]:
        """Identify swing highs and lows (local extrema)"""
        swings = []
        for i in range(2, len(highs) - 2):
            # Swing high: higher than 2 before and 2 after
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                swings.append({"type": "high", "index": i, "value": highs[i]})
            
            # Swing low
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                swings.append({"type": "low", "index": i, "value": lows[i]})
        
        return swings
    
    def _determine_trend(self, swings: List[Dict], prices: List[float]) -> str:
        """
        Determine primary trend using Dow Theory:
        - Bullish: Higher highs AND higher lows
        - Bearish: Lower highs AND lower lows
        - Neutral: Otherwise
        """
        if len(swings) < 4:
            return "neutral"
        
        # Get last 4 swings
        recent = swings[-4:]
        
        highs = [s for s in recent if s["type"] == "high"]
        lows = [s for s in recent if s["type"] == "low"]
        
        if len(highs) >= 2 and len(lows) >= 2:
            # Check for higher highs
            hh = highs[-1]["value"] > highs[0]["value"]
            # Check for higher lows
            hl = lows[-1]["value"] > lows[0]["value"]
            
            if hh and hl:
                return "bullish"
            
            # Check for lower highs
            lh = highs[-1]["value"] < highs[0]["value"]
            # Check for lower lows
            ll = lows[-1]["value"] < lows[0]["value"]
            
            if lh and ll:
                return "bearish"
        
        return "neutral"
    
    def _identify_phase(self, prices: List[float], volumes: List[float], trend: str) -> str:
        """
        Identify current phase based on price action and volume.
        
        Dow Theory phases:
        - Accumulation: Low volatility, smart money buying
        - Public Participation: Strong trending move, increasing volume
        - Distribution/Euphoria: Extreme moves, retail crowd entering
        """
        if len(prices) < 20:
            return "unknown"
        
        recent_20 = prices[-20:]
        recent_vol = volumes[-20:] if len(volumes) >= 20 else volumes
        
        # Calculate volatility
        returns = [abs(recent_20[i] - recent_20[i-1])/recent_20[i-1] for i in range(1, len(recent_20))]
        avg_volatility = sum(returns) / len(returns) if returns else 0
        
        # Calculate volume trend
        vol_trend = (sum(recent_vol[-5:]) / 5) / (sum(recent_vol[:5]) / 5) if len(recent_vol) >= 10 else 1.0
        
        # Phase identification
        if avg_volatility < 0.01:
            return "accumulation"
        elif vol_trend > 1.5 and trend != "neutral":
            return "participation"
        elif avg_volatility > 0.03 and vol_trend > 2.0:
            return "euphoria" if trend == "bullish" else "distribution"
        
        return "participation" if trend != "neutral" else "accumulation"
    
    def _check_volume_confirmation(self, prices: List[float], volumes: List[float], trend: str) -> bool:
        """
        Volume should increase in direction of trend.
        
        In bullish trend: volume increases on up days
        In bearish trend: volume increases on down days
        """
        if len(prices) < 10 or len(volumes) != len(prices):
            return True  # Neutral confirmation
        
        up_days = []
        down_days = []
        
        for i in range(1, len(prices)):
            if prices[i] > prices[i-1]:
                up_days.append(volumes[i])
            elif prices[i] < prices[i-1]:
                down_days.append(volumes[i])
        
        if not up_days or not down_days:
            return True
        
        avg_up_vol = sum(up_days) / len(up_days)
        avg_down_vol = sum(down_days) / len(down_days)
        
        if trend == "bullish":
            return avg_up_vol > avg_down_vol
        elif trend == "bearish":
            return avg_down_vol > avg_up_vol
        
        return True
    
    def _check_indices_confirmation(self, djia: List[float], djta: List[float]) -> bool:
        """
        According to Dow Theory: Both indices should confirm.
        Industrial (DJIA) and Transport (DJTA) should move together.
        """
        if len(djia) < 2 or len(djta) < 2:
            return True
        
        # Calculate direction of each
        djia_direction = djia[-1] > djia[0]
        djta_direction = djta[-1] > djta[0]
        
        # For confirmation, directions should align (both up or both down)
        # Small divergence is OK, but large divergence is a warning
        return djia_direction == djta_direction
    
    def _calculate_strength(self, swings: List[Dict], prices: List[float]) -> float:
        """Calculate trend strength based on swing consistency"""
        if len(swings) < 2:
            return 0.0
        
        # Calculate average swing magnitude
        magnitudes = []
        for i in range(1, len(swings)):
            diff = abs(swings[i]["value"] - swings[i-1]["value"])
            magnitudes.append(diff)
        
        avg_magnitude = sum(magnitudes) / len(magnitudes) if magnitudes else 0
        
        # Normalize to 0-1 range (rough approximation)
        current_price = prices[-1] if prices else 100
        strength = min(1.0, avg_magnitude / (current_price * 0.05))
        
        return strength
    
    def get_signal(self, result: TrendResult) -> DowSignal:
        """Generate a Dow Theory signal from analysis"""
        signal_type = "primary_trend"
        description = f"Primary {result.trend_type} trend"
        
        if result.phase == "accumulation":
            description += ", Phase: Accumulation (smart money buying)"
        elif result.phase == "participation":
            description += ", Phase: Public Participation"
        elif result.phase in ["distribution", "euphoria"]:
            description += f", Phase: {result.phase.capitalize()} (warning!)"
            signal_type = "phase_change"
        
        if not result.confirmed:
            description += " [WARNING: Not confirmed by volume/indices]"
        
        return DowSignal(
            signal_type=signal_type,
            direction=result.trend_type,
            confidence=int(result.strength * 100),
            description=description,
            indices_confirm=result.details.get("indices_confirmed", True)
        )


def get_dow_analysis(
    symbol: str,
    price_data: List[float],
    volumes: List[float],
    high_prices: List[float],
    low_prices: List[float],
    djia_prices: Optional[List[float]] = None,
    djta_prices: Optional[List[float]] = None
) -> Dict:
    """
    Quick Dow Theory analysis.
    
    Usage:
        dow_result = get_dow_analysis(
            "BTC",
            prices, volumes, highs, lows
        )
    """
    analyzer = DowTheoryAnalyzer()
    result = analyzer.analyze(price_data, volumes, high_prices, low_prices, djia_prices, djta_prices)
    signal = analyzer.get_signal(result)
    
    return {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "trend": result.trend_type,
        "phase": result.phase,
        "strength": round(result.strength, 2),
        "confirmed": result.confirmed,
        "signal": {
            "type": signal.signal_type,
            "direction": signal.direction,
            "confidence": signal.confidence,
            "description": signal.description,
            "indices_confirm": signal.indices_confirm
        },
        "details": result.details,
        "dow_postulates": {
            "1_market_discounts": "Price reflects all available information",
            "2_trend_types": f"Primary={result.trend_type}, Secondary=check charts",
            "3_phases": f"Current={result.phase}",
            "4_indices_confirm": result.details.get("indices_confirmed", True),
            "5_volume_confirms": result.details.get("volume_confirmed", True),
            "6_trend_persists": "Trend continues until clear reversal signal"
        }
    }
