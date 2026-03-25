"""
AstroAgent v2.0 — Classical Horary Astrology for Financial Decisions
Based on William Lilly "Christian Astrology" & John Froli "Horary Textbook"
"""

from datetime import datetime
from typing import Dict, Tuple, Any
from agents.base import BaseAgent, AgentResponse
from config.system_prompts import ASTROLOGER_PROMPT

EXALTATION = {"Sun": "Aries", "Moon": "Taurus", "Mercury": "Virgo", "Venus": "Pisces", "Mars": "Capricorn", "Jupiter": "Cancer", "Saturn": "Libra"}
FALL = {"Aries": "Sun", "Taurus": "Moon", "Virgo": "Mercury", "Pisces": "Venus", "Capricorn": "Mars", "Cancer": "Jupiter", "Libra": "Saturn"}

NAKSHATRAS = [
    {"name": "Ashwini", "gana": "Deva"}, {"name": "Bharani", "gana": "Manushya"}, {"name": "Krittika", "gana": "Deva"}, {"name": "Rohini", "gana": "Deva"},
    {"name": "Mrigashira", "gana": "Deva"}, {"name": "Ardra", "gana": "Manushya"}, {"name": "Punarvasu", "gana": "Deva"}, {"name": "Pushya", "gana": "Deva"},
    {"name": "Ashlesha", "gana": "Naga"}, {"name": "Magha", "gana": "Naga"}, {"name": "Purva Phalguni", "gana": "Manushya"}, {"name": "Uttara Phalguni", "gana": "Manushya"},
    {"name": "Hasta", "gana": "Deva"}, {"name": "Chitra", "gana": "Naga"}, {"name": "Swati", "gana": "Deva"}, {"name": "Vishakha", "gana": "Naga"},
    {"name": "Anuradha", "gana": "Deva"}, {"name": "Jyeshtha", "gana": "Naga"}, {"name": "Mula", "gana": "Naga"}, {"name": "Purva Ashadha", "gana": "Manushya"},
    {"name": "Uttara Ashadha", "gana": "Manushya"}, {"name": "Shravana", "gana": "Manushya"}, {"name": "Dhanishtha", "gana": "Manushya"}, {"name": "Shatabhisha", "gana": "Naga"},
    {"name": "Purva Bhadrapada", "gana": "Naga"}, {"name": "Uttara Bhadrapada", "gana": "Manushya"}, {"name": "Revati", "gana": "Deva"},
]

BULLISH_NAK = ["Rohini", "Mrigashira", "Swati", "Hasta", "Ashlesha", "Jyeshtha", "Anuradha"]
BEARISH_NAK = ["Ardra", "Magha", "Mula", "Purva Bhadrapada"]

CHOGHADIYA = [
    {"name": "Udveg", "type": "neutral", "icon": "🟡", "trade": 50}, {"name": "Char", "type": "good", "icon": "🟢", "trade": 75},
    {"name": "Labh", "type": "good", "icon": "🟢", "trade": 85}, {"name": "Amrit", "type": "best", "icon": "💚", "trade": 100},
    {"name": "Kaal", "type": "bad", "icon": "🔴", "trade": 20}, {"name": "Shubh", "type": "good", "icon": "🟢", "trade": 80},
    {"name": "Rog", "type": "bad", "icon": "🔴", "trade": 15}, {"name": "Ari", "type": "bad", "icon": "🔴", "trade": 10},
]

CHOGHADIYA_SEQ = {
    "Sun": ["Amrit", "Kaal", "Rog", "Udveg", "Char", "Labh", "Shubh", "Ari"],
    "Moon": ["Shubh", "Ari", "Udveg", "Rog", "Kaal", "Amrit", "Char", "Labh"],
    "Mars": ["Labh", "Char", "Amrit", "Kaal", "Rog", "Udveg", "Ari", "Shubh"],
    "Mercury": ["Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal", "Rog", "Udveg"],
    "Jupiter": ["Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal", "Rog"],
    "Venus": ["Rog", "Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal"],
    "Saturn": ["Kaal", "Rog", "Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit"],
}


class AstroAgent(BaseAgent):
    """AstroAgent v2.0 — Classical Horary Astrology for Financial Decisions
    
    Based on:
    - William Lilly "Christian Astrology" (1647)
    - John Froli "Horary Textbook"
    
    KEY CONCEPTS:
    1. Essential Dignities: Exaltation (+5), Fall (-4), Triplicity (+3)
    2. Accidental Dignities: Joy, Stationary, Combustion, Cazimi
    3. Aspects: Trine (good), Square (bad), Opposition (bad)
    4. Financial Significators: 2nd=Money, 8th=Debt, 10th=Career, 11th=Gains
    5. Arabic Parts: Part of Fortune = ASC + Moon - Sun
    """
    
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090, **kwargs):
        super().__init__(name="Astrologer", system_prompt=ASTROLOGER_PROMPT, temperature=0.1, **kwargs)
        self.lat = lat
        self.lon = lon
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        dt = datetime.now()
        symbol = context.get("symbol", "BTC")
        positions = self._calc_positions(dt)
        dignities = self._analyze_dignities(positions)
        nakshatra, pada = self._get_nakshatra(dt)
        chogh = self._get_choghadiya(dt)
        muhurta = self._calc_muhurta(dt, nakshatra)
        aspects = self._get_aspects(positions)
        financial = self._analyze_financial(positions, dignities)
        signal, confidence = self._get_verdict(muhurta, chogh, aspects, financial)
        
        return AgentResponse(
            agent_name="Astrologer", signal=signal, confidence=confidence,
            summary=f"Classical: {nakshatra} + Choghadiya: {chogh['name']} {chogh['icon']}",
            details={
                "vedic": {
                    "nakshatra": nakshatra, "nak_pada": pada,
                    "nak_trade": "BULLISH" if nakshatra in BULLISH_NAK else "BEARISH" if nakshatra in BEARISH_NAK else "NEUTRAL",
                    "choghadiya": chogh["name"], "chogh_icon": chogh["icon"], "chogh_score": chogh["trade"],
                    "muhurta_score": muhurta["score"], "muhurta_verdict": muhurta["verdict"],
                },
                "western": {
                    "moon_phase": self._moon_phase(dt),
                    "jupiter_sign": positions.get("Jupiter", {}).get("sign", "N/A"),
                    "aspect_score": aspects["score"],
                },
                "classical": {
                    "jupiter_dignity": dignities.get("Jupiter", {}).get("total", 0),
                    "venus_dignity": dignities.get("Venus", {}).get("total", 0),
                    "strongest_planet": dignities.get("strongest", "Moon"),
                    "financial_score": financial["score"],
                    "part_of_fortune": financial.get("part_of_fortune", "N/A"),
                },
                "best_time": chogh.get("start", "N/A"),
            }
        )
    
    def _parse_response(self, text: str) -> Dict:
        return {"text": text}
    
    async def analyze_impl(self, prompt: str) -> str:
        return "Classical analysis"
    
    def _calc_positions(self, dt: datetime) -> Dict:
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        base = {"Sun": 0, "Moon": 45, "Mercury": 120, "Venus": 200, "Mars": 310, "Jupiter": 85, "Saturn": 270}
        motion = {"Sun": 1, "Moon": 13, "Mercury": 1.5, "Venus": 1.2, "Mars": 0.5, "Jupiter": 0.08, "Saturn": 0.03}
        jd = self._julian_day(dt)
        positions = {}
        for planet, base_deg in base.items():
            deg = (base_deg + motion.get(planet, 1) * (jd % 365)) % 360
            positions[planet] = {"sign": signs[int(deg // 30)], "degree": deg % 30, "speed": motion.get(planet, 1)}
        return positions
    
    def _julian_day(self, dt: datetime) -> float:
        Y, M, D = dt.year, dt.month, dt.day + (dt.hour + dt.minute / 60) / 24
        if M <= 2: Y, M = Y - 1, M + 12
        A_ = int(Y / 100); B = 2 - A_ + int(A_ / 4)
        return int(365.25 * (Y + 4716)) + int(30.6001 * (M + 1)) + D + B - 1524.5
    
    def _get_nakshatra(self, dt: datetime) -> Tuple[str, int]:
        jd = self._julian_day(dt)
        sun_mean = (280.46 + 0.9856474 * (jd - 2451545)) % 360
        moon_mean = (218.32 + 13.176396 * (jd - 2451545)) % 360
        moon_sun = (moon_mean - sun_mean) % 360
        nak_index = int(moon_sun * 27 / 360) % 27
        return NAKSHATRAS[nak_index]["name"], int((moon_sun * 27 % 360) / 90) + 1
    
    def _get_choghadiya(self, dt: datetime) -> Dict:
        day_lords = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 4: "Jupiter", 5: "Venus", 6: "Saturn"}
        lord = day_lords[dt.weekday()]
        seq = CHOGHADIYA_SEQ[lord]
        hour_index = int((dt.hour - 6) // 1.5) % 8
        chogh_name = seq[hour_index]
        chogh = next(c for c in CHOGHADIYA if c["name"] == chogh_name)
        return {"name": chogh_name, "type": chogh["type"], "icon": chogh["icon"], "trade": chogh["trade"], "start": f"{(6 + hour_index * 1.5) % 24:.0f}:00"}
    
    def _calc_muhurta(self, dt: datetime, nakshatra: str) -> Dict:
        score = 50
        if nakshatra in BULLISH_NAK: score += 30
        elif nakshatra in BEARISH_NAK: score -= 20
        if dt.weekday() in [2, 4, 5]: score += 15
        elif dt.weekday() in [0, 6]: score -= 10
        verdict = "🟢 EXCELLENT" if score >= 80 else "🟡 GOOD" if score >= 60 else "🟠 CAUTION" if score >= 40 else "🔴 AVOID"
        return {"score": min(100, max(0, score)), "verdict": verdict}
    
    def _analyze_dignities(self, positions: Dict) -> Dict:
        dignities, max_score, strongest = {}, -100, "Moon"
        for planet, pos in positions.items():
            sign, score, notes = pos["sign"], 0, []
            if sign == EXALTATION.get(planet): score += 5; notes.append("Exaltation")
            elif sign == FALL.get(planet): score -= 4; notes.append("Fall")
            dignities[planet] = {"sign": sign, "total": score, "notes": notes}
            if score > max_score: max_score, strongest = score, planet
        dignities["strongest"] = strongest
        return dignities
    
    def _get_aspects(self, positions: Dict) -> Dict:
        score = 50
        moon = positions.get("Moon", {}).get("sign", "")
        jupiter = positions.get("Jupiter", {}).get("sign", "")
        trines = {"Aries": ["Leo", "Sagittarius"], "Cancer": ["Scorpio", "Pisces"], "Libra": ["Aquarius", "Gemini"]}
        for base, trine_list in trines.items():
            if moon in trine_list or jupiter in trine_list: score += 15
        squares = {"Aries": ["Cancer", "Capricorn"], "Taurus": ["Leo", "Aquarius"]}
        for base, square_list in squares.items():
            if moon in square_list or jupiter in square_list: score -= 10
        return {"score": min(100, max(0, score))}
    
    def _analyze_financial(self, positions: Dict, dignities: Dict) -> Dict:
        jupiter = dignities.get("Jupiter", {}).get("total", 0)
        venus = dignities.get("Venus", {}).get("total", 0)
        score = 50 + jupiter * 3 + venus * 3
        jd = self._julian_day(datetime.now())
        asc = jd % 360
        sun = positions.get("Sun", {}).get("degree", 0)
        moon = positions.get("Moon", {}).get("degree", 0)
        part_of_fortune = int((asc + moon - sun) % 360)
        return {"score": min(100, max(0, score)), "part_of_fortune": part_of_fortune}
    
    def _moon_phase(self, dt: datetime) -> str:
        jd = self._julian_day(dt)
        days = (jd - 2451550.1) % 29.530588853
        phases = ["New Moon 🌑", "Waxing Crescent 🌒", "First Quarter 🌓", "Waxing Gibbous 🌔", "Full Moon 🌕", "Waning Gibbous 🌖", "Last Quarter 🌗", "Waning Crescent 🌘"]
        return phases[int(days / 3.7) % 8]
    
    def _get_verdict(self, muhurta: Dict, chogh: Dict, aspects: Dict, financial: Dict) -> Tuple[str, int]:
        vedic = muhurta["score"] * 0.4 + chogh["trade"] * 0.3
        classical = financial["score"] * 0.2 + aspects["score"] * 0.1
        total = (vedic + classical)
        if total >= 65: return "BULLISH", int(total)
        elif total <= 35: return "BEARISH", int(100 - total)
        else: return "NEUTRAL", 50


def get_astro_agent(lat: float = 28.6139, lon: float = 77.2090, **kwargs) -> AstroAgent:
    return AstroAgent(lat=lat, lon=lon, **kwargs)
