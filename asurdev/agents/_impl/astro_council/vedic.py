"""
Vedic Astrologer — Nakshatras, Choghadiya, Muhurta
===================================================
v3.2 — ENFORCEMENT: All data from Swiss Ephemeris only

NIKSHATRA, CHOGHADIYA, KARANA, TITHI, YOGA
MUST be calculated by swiss_ephemeris, NOT by this agent.
"""

from datetime import datetime
from typing import Dict, Optional, Tuple

# Trading scores for Nakshatras (Parashara)
NAKSHATRA_TRADING_SCORES = {
    "Ashwini": {"signal": "BULLISH", "score": 65},
    "Bharani": {"signal": "BULLISH", "score": 60},
    "Krittika": {"signal": "NEUTRAL", "score": 55},
    "Rohini": {"signal": "STRONG_BULLISH", "score": 85},
    "Mrigashira": {"signal": "BULLISH", "score": 75},
    "Ardra": {"signal": "VOLATILE", "score": 40},
    "Punarvasu": {"signal": "NEUTRAL", "score": 60},
    "Pushya": {"signal": "BULLISH", "score": 70},
    "Ashlesha": {"signal": "BEARISH", "score": 30},  # Deceptive
    "Magha": {"signal": "NEUTRAL", "score": 50},
    "Purva Phalguni": {"signal": "BULLISH", "score": 70},
    "Uttara Phalguni": {"signal": "BULLISH", "score": 75},
    "Hasta": {"signal": "BULLISH", "score": 75},
    "Chitra": {"signal": "VOLATILE", "score": 55},
    "Swati": {"signal": "STRONG_BULLISH", "score": 80},
    "Vishakha": {"signal": "VOLATILE", "score": 50},
    "Anuradha": {"signal": "BULLISH", "score": 70},
    "Jyeshtha": {"signal": "BEARISH", "score": 35},
    "Mula": {"signal": "BEARISH", "score": 35},
    "Purva Ashadha": {"signal": "NEUTRAL", "score": 55},
    "Uttara Ashadha": {"signal": "BULLISH", "score": 75},
    "Shravana": {"signal": "BULLISH", "score": 70},
    "Dhanishta": {"signal": "NEUTRAL", "score": 55},
    "Shatabhisha": {"signal": "VOLATILE", "score": 45},
    "Purva Bhadrapada": {"signal": "NEUTRAL", "score": 50},
    "Uttara Bhadrapada": {"signal": "BULLISH", "score": 65},
    "Revati": {"signal": "BULLISH", "score": 70},
}

# Choghadiya trading scores
CHOGHADIYA_SCORES = {
    "Amrit": 100,
    "Shubh": 75,
    "Labh": 80,
    "Char": 70,
    "Udveg": 50,
    "Kaal": 20,
    "Rog": 15,
}

# Yoga trading scores
YOGA_SCORES = {
    "Vishkambha": 40,
    "Priti": 60,
    "Ayushman": 75,
    "Saubhagya": 70,
    "Shobhana": 65,
    "Atiganda": 25,
    "Sukarma": 70,
    "Dhriti": 55,
    "Shula": 30,
    "Ganda": 25,
    "Vriddhi": 65,
    "Dhruva": 75,
    "Vyaghata": 35,
    "Harshana": 70,
    "Vajra": 30,
    "Siddhi": 75,
    "Vyatipata": 25,
    "Variyan": 55,
    "Parigha": 35,
    "Shiva": 80,
    "Siddha": 75,
    "Sadhya": 65,
    "Shubha": 70,
    "Shukla": 75,
    "Brahma": 80,
    "Indra": 75,
    "Vaidhriti": 25,
}

# Signs for Moon
BULL_SIGNS = ["Taurus", "Cancer", "Libra", "Capricorn", "Aquarius"]
BEAR_SIGNS = ["Aries", "Leo", "Scorpio", "Sagittarius"]

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


class VedicAstrologerAgent:
    """
    Vedic Astrologer — ENFORCEMENT version.
    
    All calculations MUST come from swiss_ephemeris tool.
    This agent interprets the data, does NOT calculate it.
    
    Inputs (from Swiss Ephemeris):
    - Nakshatra (from Moon longitude)
    - Tithi (from Sun-Moon difference)
    - Yoga (from Sun+Moon sum)
    - Karana (from Tithi half)
    - Choghadiya (from weekday + time of day)
    - Moon sign (from Moon longitude)
    
    Outputs:
    - Muhurta score (0-100)
    - Trading signal
    """

    def __init__(self):
        pass

    def analyze(
        self,
        eph: Dict,
        moon_longitude: Optional[float] = None
    ) -> Dict:
        """
        Analyze Vedic astrology data from Swiss Ephemeris.
        
        Args:
            eph: Full ephemeris result from swiss_ephemeris tool
            moon_longitude: Optional, can also come from eph["positions"]["Moon"]["lon"]
        
        Returns:
            Dict with nakshatra, choghadiya, muhurta_score, signal
        """
        # ENFORCEMENT: Get data from ephemeris
        panchanga = eph.get("panchanga", {})
        current_chogh = eph.get("current_choghadiya", {})
        positions = eph.get("positions", {})
        
        # Get values from ephemeris (NOT calculated here)
        nakshatra = panchanga.get("nakshatra", "Unknown")
        nakshatra_pada = panchanga.get("nakshatra_pada", 1)
        yoga = panchanga.get("yoga", "Unknown")
        yoga_category = panchanga.get("yoga_category", "Neutral")
        tithi = panchanga.get("tithi", "Unknown")
        karana = panchanga.get("karana", "Unknown")
        vara = panchanga.get("vara", "Unknown")
        
        choghadiya_type = current_chogh.get("type", "Unknown")
        chogh_auspicious = current_chogh.get("auspicious", False)
        
        # Moon sign from positions
        moon_lon = moon_longitude or positions.get("Moon", {}).get("lon", 0)
        moon_sign_num = int(moon_lon / 30) % 12
        moon_sign = SIGNS[moon_sign_num]
        
        # Calculate Muhurta Score (0-100)
        score, factors = self._calculate_muhurta_score(
            nakshatra=nakshatra,
            yoga=yoga,
            yoga_category=yoga_category,
            moon_sign=moon_sign,
            choghadiya_type=choghadiya_type,
            vara=vara,
        )
        
        # Determine signal
        signal = self._score_to_signal(score)
        
        return {
            "nakshatra": nakshatra,
            "nakshatra_pada": nakshatra_pada,
            "moon_sign": moon_sign,
            "tithi": tithi,
            "karana": karana,
            "yoga": yoga,
            "yoga_category": yoga_category,
            "vara": vara,
            "choghadiya": choghadiya_type,
            "choghadiya_auspicious": chogh_auspicious,
            "muhurta_score": score,
            "factors": factors,
            "signal": signal,
            "confidence": min(85, 50 + abs(score - 50)),
        }

    def _calculate_muhurta_score(
        self,
        nakshatra: str,
        yoga: str,
        yoga_category: str,
        moon_sign: str,
        choghadiya_type: str,
        vara: str,
    ) -> Tuple[float, Dict]:
        """
        Calculate Muhurta score (0-100) based on Vedic factors.
        
        Weights:
        - Nakshatra: 30%
        - Yoga: 20%
        - Moon sign: 20%
        - Choghadiya: 20%
        - Day (vara): 10%
        """
        factors = {}
        
        # Nakshatra (30%)
        nak_data = NAKSHATRA_TRADING_SCORES.get(nakshatra, {"score": 50})
        nak_score = nak_data["score"]
        factors["nakshatra"] = {"value": nak_score, "detail": nakshatra}
        
        # Yoga (20%)
        yoga_score = YOGA_SCORES.get(yoga, 50)
        if yoga_category == "Inauspicious":
            yoga_score = min(yoga_score, 30)
        elif yoga_category == "Auspicious":
            yoga_score = max(yoga_score, 70)
        factors["yoga"] = {"value": yoga_score, "detail": yoga}
        
        # Moon sign (20%)
        if moon_sign in BULL_SIGNS:
            sign_score = 80
        elif moon_sign in BEAR_SIGNS:
            sign_score = 30
        else:
            sign_score = 55
        factors["moon_sign"] = {"value": sign_score, "detail": moon_sign}
        
        # Choghadiya (20%)
        chogh_score = CHOGHADIYA_SCORES.get(choghadiya_type, 50)
        factors["choghadiya"] = {"value": chogh_score, "detail": choghadiya_type}
        
        # Day of week (10%)
        favorable_days = {"Monday": 80, "Wednesday": 75, "Thursday": 80, "Friday": 70}
        day_score = favorable_days.get(vara, 50)
        factors["vara"] = {"value": day_score, "detail": vara}
        
        # Weighted total
        total = (
            nak_score * 0.30 +
            yoga_score * 0.20 +
            sign_score * 0.20 +
            chogh_score * 0.20 +
            day_score * 0.10
        )
        
        return round(total, 1), factors

    @staticmethod
    def _score_to_signal(score: float) -> str:
        """Convert Muhurta score to trading signal."""
        if score >= 75:
            return "STRONG_BULLISH"
        elif score >= 60:
            return "BULLISH"
        elif score >= 45:
            return "NEUTRAL"
        elif score >= 30:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"

    @staticmethod
    def format_interpretation(analysis: Dict) -> str:
        """Format analysis into readable string."""
        lines = ["📿 Vedic Astrology Analysis:"]
        lines.append(f"   Nakshatra: {analysis['nakshatra']} (Pada {analysis['nakshatra_pada']})")
        lines.append(f"   Moon Sign: {analysis['moon_sign']}")
        lines.append(f"   Tithi: {analysis['tithi']}, Karana: {analysis['karana']}")
        lines.append(f"   Yoga: {analysis['yoga']} ({analysis['yoga_category']})")
        lines.append(f"   Choghadiya: {analysis['choghadiya']}")
        lines.append(f"   Day: {analysis['vara']}")
        lines.append(f"   ─────────────────────")
        lines.append(f"   Muhurta Score: {analysis['muhurta_score']}/100")
        lines.append(f"   Signal: {analysis['signal']}")
        return "\n".join(lines)
