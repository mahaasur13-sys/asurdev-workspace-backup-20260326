"""
Meridian Agent - B. Meridian Financial Astrology Methods
Based on "Planets and Stocks" by Brandy Meridian

Key methods:
1. Planetary Lines (Direct + Mirror)
2. Elongation Analysis  
3. Lunar Nodes and Finance
4. Aspect patterns to Natal positions
"""
import math
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from .base_agent import BaseAgent, AgentResponse


@dataclass
class PlanetaryLine:
    planet: str
    direct_line: float  # Price level for direct transit
    mirror_line: float  # Price level for mirror transit
    strength: int  # 0-100
    interpretation: str


@dataclass
class ElongationInfo:
    planet: str
    elongation_angle: float  # Degrees from Sun
    eastern_morning: bool  # True = eastern (morning), False = western (evening)
    market_signal: str
    strength: int


# Zodiac signs and their market characteristics
ZODIAC_SIGNALS = {
    "Aries": ("BULLISH", 60, "Initiative, new positions"),
    "Taurus": ("BEARISH", 55, "Caution, consolidation"),
    "Gemini": ("NEUTRAL", 50, "Volatility, mixed signals"),
    "Cancer": ("BULLISH", 65, "Safe haven flows"),
    "Leo": ("BULLISH", 60, "Confidence, speculation"),
    "Virgo": ("NEUTRAL", 50, "Analysis, correction"),
    "Libra": ("BEARISH", 55, "Balance, indecision"),
    "Scorpio": ("BEARISH", 60, "Transformation, deep changes"),
    "Sagittarius": ("BULLISH", 65, "Expansion, optimism"),
    "Capricorn": ("BEARISH", 55, "Structures, profit-taking"),
    "Aquarius": ("NEUTRAL", 55, "Innovation, disruption"),
    "Pisces": ("BULLISH", 60, "Spiritual, intuitive flows"),
}


class MeridianAgent(BaseAgent):
    """
    Implements B. Meridian's financial astrology methods.
    
    Key principles:
    1. Planetary Lines - direct and mirror price levels
    2. Elongation - angular distance from Sun indicates market phase
    3. Lunar Nodes - financial turning points
    4. Natal aspects - birth chart patterns
    """
    
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090, **kwargs):
        super().__init__(
            name="MeridianAgent",
            system_prompt="Финансовая астрология по методу Б. Меридиан. Анализируй планетные линии и элонгацию.",
            temperature=0.3,
            **kwargs
        )
        self.lat = lat
        self.lon = lon
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Main analysis using Meridian methods.
        """
        now = datetime.now()
        
        # Get symbol for natal reference (if available)
        symbol = context.get("symbol", "BTC")
        current_price = context.get("market_data", {}).get("current_price", 100)
        
        # Calculate planetary positions
        positions = self._calculate_positions(now)
        
        # Calculate planetary lines
        planetary_lines = self._calculate_planetary_lines(positions, current_price)
        
        # Calculate elongations
        elongations = self._calculate_elongations(positions)
        
        # Lunar node analysis
        lunar_node_signal = self._analyze_lunar_nodes(now)
        
        # Zodiac current position signal
        sun_position = positions.get("Sun", 0)
        zodiac_signal = self._get_zodiac_signal(sun_position)
        
        # Composite Meridian signal
        composite = self._composite_meridian_signal(
            planetary_lines, elongations, zodiac_signal
        )
        
        # Build summary
        summary_parts = [
            f"☉ {zodiac_signal[0]}({zodiac_signal[1]}%)",
            f"☊ {lunar_node_signal[0]}({lunar_node_signal[1]}%)",
        ]
        
        # Add top planetary lines
        strongest_lines = sorted(planetary_lines, key=lambda x: x.strength, reverse=True)[:2]
        for line in strongest_lines:
            summary_parts.append(f"{line.planet}:{line.strength}%")
        
        return AgentResponse(
            agent_name="MeridianAgent",
            signal=composite,
            confidence=self._calculate_confidence(elongations, planetary_lines),
            summary=" | ".join(summary_parts),
            details={
                "method": "B. Meridian Financial Astrology",
                "zodiac_position": {
                    "sign": zodiac_signal[2],
                    "degree": round(sun_position % 30, 2),
                    "interpretation": zodiac_signal[3]
                },
                "planetary_lines": [{
                    "planet": pl.planet,
                    "direct_line": round(pl.direct_line, 2),
                    "mirror_line": round(pl.mirror_line, 2),
                    "strength": pl.strength,
                    "interpretation": pl.interpretation
                } for pl in planetary_lines],
                "elongations": [{
                    "planet": e.planet,
                    "angle": round(e.elongation_angle, 1),
                    "type": "morning" if e.eastern_morning else "evening",
                    "signal": e.market_signal,
                    "strength": e.strength
                } for e in elongations],
                "lunar_nodes": {
                    "north_node": lunar_node_signal[0],
                    "strength": lunar_node_signal[1],
                    "interpretation": lunar_node_signal[2]
                }
            }
        )
    
    def _calculate_positions(self, dt: datetime) -> Dict[str, float]:
        """
        Calculate planetary longitudes (simplified).
        In production, use Swiss Ephemeris.
        """
        # Days since J2000.0
        j2000 = datetime(2000, 1, 1, 12, 0, 0)
        days = (dt - j2000).total_seconds() / 86400.0
        
        # Mean longitudes at J2000 and daily motions
        base_longitudes = {
            "Sun": 280.47,
            "Moon": 218.32,
            "Mercury": 252.87,
            "Venus": 181.97,
            "Mars": 355.43,
            "Jupiter": 34.40,
            "Saturn": 50.08,
        }
        
        speeds = {
            "Sun": 0.9856,
            "Moon": 13.18,
            "Mercury": 4.15,
            "Venus": 1.60,
            "Mars": 0.52,
            "Jupiter": 0.083,
            "Saturn": 0.034,
        }
        
        positions = {}
        for planet, base in base_longitudes.items():
            positions[planet] = (base + speeds[planet] * days) % 360
        
        return positions
    
    def _calculate_planetary_lines(
        self, 
        positions: Dict[str, float], 
        current_price: float
    ) -> List[PlanetaryLine]:
        """
        Calculate planetary direct and mirror lines.
        
        Method: Map planetary longitude (0-360°) to price range.
        - Direct line: planet in direct motion sign
        - Mirror line: planet in mirrored position (180° opposite)
        """
        lines = []
        
        for planet, longitude in positions.items():
            if planet not in ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
                continue
            
            # Map 0-360° to price range (simplified)
            # In production, use historical data to calibrate
            
            # Direct line: current longitude
            direct_pct = longitude / 360
            direct_line = current_price * (0.9 + direct_pct * 0.2)  # ±10% range
            
            # Mirror line: 180° opposite
            mirror_pct = ((longitude + 180) % 360) / 360
            mirror_line = current_price * (0.9 + mirror_pct * 0.2)
            
            # Determine strength based on planet
            planet_weights = {
                "Sun": 70,
                "Moon": 60,
                "Mercury": 55,
                "Venus": 65,
                "Mars": 60,
                "Jupiter": 75,
                "Saturn": 80,
            }
            strength = planet_weights.get(planet, 50)
            
            # Interpretation
            if planet == "Jupiter":
                interpretation = "Expansion, optimism, Bullish for risk assets"
            elif planet == "Saturn":
                interpretation = "Restriction, caution, Bearish pressure"
            elif planet == "Venus":
                interpretation = "Harmony, profit-taking, Neutral"
            elif planet == "Mars":
                interpretation = "Aggression, momentum, Potential breakout"
            else:
                interpretation = "Standard transit influence"
            
            lines.append(PlanetaryLine(
                planet=planet,
                direct_line=direct_line,
                mirror_line=mirror_line,
                strength=strength,
                interpretation=interpretation
            ))
        
        return lines
    
    def _calculate_elongations(self, positions: Dict[str, float]) -> List[ElongationInfo]:
        """
        Calculate elongation (angular distance from Sun).
        
        Eastern elongation: planet rises before Sun (morning)
        Western elongation: planet sets after Sun (evening)
        
        Market interpretation:
        - Maximum eastern elongation: Potential high
        - Maximum western elongation: Potential low
        """
        elongations = []
        sun_long = positions["Sun"]
        
        for planet, long in positions.items():
            if planet == "Sun":
                continue
            
            # Calculate angular distance from Sun
            diff = (long - sun_long) % 360
            if diff > 180:
                diff = 360 - diff
            
            elongation = diff
            
            # Eastern (morning) if planet is ahead of Sun
            eastern = (long - sun_long) % 360 < 180
            
            # Signal based on elongation
            if elongation > 45:
                if eastern:
                    signal, strength = "BULLISH", 65
                else:
                    signal, strength = "BEARISH", 65
            elif elongation > 25:
                signal, strength = "NEUTRAL", 55
            else:
                signal, strength = "NEUTRAL", 50
            
            elongations.append(ElongationInfo(
                planet=planet,
                elongation_angle=elongation,
                eastern_morning=eastern,
                market_signal=signal,
                strength=strength
            ))
        
        return elongations
    
    def _analyze_lunar_nodes(self, dt: datetime) -> Tuple[str, int, str]:
        """
        Lunar Nodes (True Node) analysis.
        
        North Node: Direction of growth, new opportunities
        South Node: Past patterns, release points
        
        Fast transits: Nodes move backwards ~3 min per day
        """
        # Simplified: calculate approximate node position
        j2000 = datetime(2000, 1, 1, 12, 0, 0)
        days = (dt - j2000).total_seconds() / 86400.0
        
        # Mean motion of North Node (retrograde)
        node_long = (125.08 - 0.052 * days) % 360
        
        # Determine sign
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        sign_idx = int(node_long // 30) % 12
        sign = signs[sign_idx]
        
        # Signal based on sign
        bullish_signs = ["Aries", "Cancer", "Leo", "Sagittarius", "Pisces"]
        bearish_signs = ["Taurus", "Virgo", "Libra", "Capricorn"]
        
        if sign in bullish_signs:
            return "BULLISH", 60, f"North Node in {sign}: Growth direction"
        elif sign in bearish_signs:
            return "BEARISH", 60, f"North Node in {sign}: Caution warranted"
        else:
            return "NEUTRAL", 50, f"North Node in {sign}: Mixed energy"
    
    def _get_zodiac_signal(self, sun_longitude: float) -> Tuple[str, int, str, str]:
        """
        Get market signal based on Sun's zodiac position.
        """
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        sign_idx = int(sun_longitude // 30) % 12
        sign = signs[sign_idx]
        
        signal, confidence, desc = ZODIAC_SIGNALS.get(sign, ("NEUTRAL", 50, ""))
        
        return signal, confidence, sign, desc
    
    def _composite_meridian_signal(
        self,
        lines: List[PlanetaryLine],
        elongations: List[ElongationInfo],
        zodiac: Tuple[str, int, str, str]
    ) -> str:
        """Composite signal from all Meridian methods."""
        scores = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
        
        # Planetary lines (weighted by strength)
        for line in lines:
            if line.strength > 60:
                if "Jupiter" in line.planet or "Venus" in line.planet:
                    scores["BULLISH"] += line.strength
                elif "Saturn" in line.planet:
                    scores["BEARISH"] += line.strength
        
        # Elongations
        for elong in elongations:
            if elong.strength > 60:
                scores[elong.market_signal] += elong.strength
        
        # Zodiac
        scores[zodiac[0]] += zodiac[1]
        
        if scores["BULLISH"] > scores["BEARISH"]:
            return "BULLISH"
        elif scores["BEARISH"] > scores["BULLISH"]:
            return "BEARISH"
        return "NEUTRAL"
    
    def _calculate_confidence(
        self, 
        elongations: List[ElongationInfo], 
        lines: List[PlanetaryLine]
    ) -> int:
        """Calculate overall confidence."""
        # Base confidence
        conf = 50
        
        # Add for strong elongations
        strong_elong = sum(1 for e in elongations if e.strength > 60)
        conf += strong_elong * 5
        
        # Add for strong planetary lines
        strong_lines = sum(1 for l in lines if l.strength > 70)
        conf += strong_lines * 5
        
        return min(85, conf)


class MeridianNatalChart:
    """
    Handle natal chart aspects for a symbol's "birth".
    e.g., BTC birth date: 3 Jan 2009
    """
    
    BTC_BIRTH = datetime(2009, 1, 3, 18, 15, 0)  # Genesis block
    
    @staticmethod
    def get_natal_planets(birth_date: datetime) -> Dict[str, float]:
        """
        Get natal planetary positions at birth.
        In production, use Swiss Ephemeris for exact positions.
        """
        # Simplified calculation
        j2000 = datetime(2000, 1, 1, 12, 0, 0)
        days = (birth_date - j2000).total_seconds() / 86400.0
        
        base = {
            "Sun": 282.5,
            "Moon": 122.3,
            "Mercury": 290.1,
            "Venus": 315.2,
            "Mars": 200.8,
        }
        
        return {k: (v + 1.0 * days) % 360 for k, v in base.items()}
    
    @staticmethod
    def get_transit_natal_aspects(
        transit_date: datetime,
        birth_date: datetime
    ) -> List[Dict]:
        """
        Calculate aspects between current transits and natal positions.
        Major aspects: conjunction (0°), opposition (180°), trine (120°), square (90°)
        """
        transits = MeridianNatalChart.get_natal_planets(transit_date)
        natal = MeridianNatalChart.get_natal_planets(birth_date)
        
        aspects = []
        orb = 5  # degrees of orb
        
        for planet, transit_long in transits.items():
            if planet not in natal:
                continue
            
            natal_long = natal[planet]
            diff = abs(transit_long - natal_long) % 360
            
            # Check major aspects
            aspect_types = {
                0: "conjunction",
                90: "square", 
                120: "trine",
                180: "opposition"
            }
            
            for angle, name in aspect_types.items():
                if abs(diff - angle) < orb:
                    aspects.append({
                        "planet": planet,
                        "aspect": name,
                        "orb": round(abs(diff - angle), 2),
                        "natal": round(natal_long, 2),
                        "transit": round(transit_long, 2)
                    })
        
        return aspects
