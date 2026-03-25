"""AstroAgent с интеграцией Obsidian Knowledge Base"""
import sys
import json
from datetime import datetime
from typing import Dict, Optional

# Try to import vault_client
try:
    from obsidian.vault_client import get_knowledge_base
    HAS_KB = True
except ImportError:
    HAS_KB = False

#Ephemeris constants
ZODIAC = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
          "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

CHOGHADIYA = [
    ("Amrut", "Благоприятно для всего"), 
    ("Kaal", "Неблагоприятно"),
    ("Rog", "Болезни, конфликты"),
    ("Uday", "Утреннее процветание"),
    ("Jay", "Победа, успех"),
    ("Naidh", "Нейтральное"),
    ("Kal", "Беды, потери"),
    ("Shubh", "Добрые дела")
]

ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water"
}


class AstroExpert:
    """Классический астролог с интеграцией Obsidian Knowledge Base"""
    
    def __init__(self, vault_path: str = "/home/workspace/obsidian-sync"):
        self.vault_path = vault_path
        self.kb = None
        if HAS_KB:
            try:
                self.kb = get_knowledge_base()
                print(f"Knowledge base loaded: {len(self.kb.blocks)} blocks")
            except Exception as e:
                print(f"Warning: Could not load knowledge base: {e}")
    
    def calculate_zodiac_position(self, degrees: float) -> Dict:
        """Расчёт позиции в знаке зодиака"""
        sign_index = int(degrees // 30)
        degree_in_sign = degrees % 30
        return {
            "sign": ZODIAC[sign_index],
            "degree": round(degree_in_sign, 2),
            "full_position": f"{int(degree_in_sign)}°{int((degree_in_sign % 1) * 60)}'"
        }
    
    def get_nakshatra(self, moon_longitude: float) -> Dict:
        """Накшатра (лунный дом)"""
        pada = int((moon_longitude % 27) // 3.75)
        nak_index = int(moon_longitude // 13.3333)
        nak_index = min(nak_index, 26)
        return {
            "name": NAKSHATRAS[nak_index],
            "pada": pada + 1,
            "pada_name": ["Pratham", "Dwitiya", "Tritiya", "Chaturtha"][pada]
        }
    
    def get_choghadiya(self, dt: datetime, sunrise: float = 6.5) -> Dict:
        """Чагда (мухурта)"""
        solar_time = (dt.hour + dt.minute/60 + dt.second/3600 - sunrise) % 24
        index = int(solar_time * 8 // 24) % 8
        name, desc = CHOGHADIYA[index]
        return {
            "name": name,
            "type": "Auspicious" if name in ["Amrut", "Jay", "Shubh", "Uday"] else "Inauspicious",
            "description": desc
        }
    
    def get_planetary_relationships(self, moon_sign: str) -> Dict:
        """Планетарные отношения"""
        moon_element = ELEMENTS.get(moon_sign, "Unknown")
        
        friendly = ["Sun", "Mars", "Jupiter"] if moon_element == "Fire" else \
                   ["Venus", "Saturn", "Moon"] if moon_element == "Earth" else \
                   ["Mercury", "Venus"] if moon_element == "Air" else ["Moon", "Venus"]
        
        return {
            "moon_sign": moon_sign,
            "element": moon_element,
            "friendly_planets": friendly
        }
    
    def get_knowledge_context(self, topic: str) -> str:
        """Получить контекст из Obsidian vault"""
        if not self.kb:
            return f"[Obsidian vault not loaded - topic: {topic}]"
        return self.kb.get_context(topic, max_chars=1000)
    
    def analyze(self, symbol: str, action: str = "hold") -> Dict:
        """Полный астрологический анализ"""
        now = datetime.utcnow()
        
        # Эфемериды (упрощённые)
        jd = self._julian_day(now)
        T = (jd - 2451545.0) / 36525
        
        moon_longitude = (218.32 + 481267.883 * T) % 360
        sun_longitude = (280.47 + 36000.77 * T) % 360
        
        moon_pos = self.calculate_zodiac_position(moon_longitude)
        nakshatra = self.get_nakshatra(moon_longitude)
        choghadiya = self.get_choghadiya(now)
        relationships = self.get_planetary_relationships(moon_pos["sign"])
        
        # Знания из vault
        knowledge = self.get_knowledge_context(f"{symbol} {action} {nakshatra['name']}")
        
        # Сигнал
        if choghadiya["type"] == "Auspicious" and action.lower() == "buy":
            signal, confidence = "BULLISH", 70
        elif choghadiya["type"] == "Inauspicious" and action.lower() == "sell":
            signal, confidence = "BEARISH", 70
        else:
            signal, confidence = "NEUTRAL", 50
        
        return {
            "signal": signal,
            "confidence": confidence,
            "summary": f"Moon in {moon_pos['sign']}, {nakshatra['name']}, {choghadiya['name']} Muhurta",
            "details": {
                "moon": moon_pos,
                "nakshatra": nakshatra,
                "choghadiya": choghadiya,
                "relationships": relationships,
                "knowledge": knowledge[:500]
            }
        }
    
    def _julian_day(self, dt: datetime) -> float:
        """Юлианская дата"""
        Y, M, D = dt.year, dt.month, dt.day + (dt.hour + dt.minute/60 + dt.second/3600) / 24
        if M <= 2:
            Y, M = Y - 1, M + 12
        A_ = int(Y / 100)
        B_ = 2 - A_ + int(A_ / 4)
        return int(365.25 * (Y + 4716)) + int(30.6001 * (M + 1)) + D + B_ - 1524.5


if __name__ == "__main__":
    print("=== AstroExpert with Obsidian Integration ===")
    expert = AstroExpert()
    result = expert.analyze("BTC", "buy")
    print(f"Signal: {result['signal']} ({result['confidence']}%)")
    print(f"Summary: {result['summary']}")
    print(f"Muhurta: {result['details']['choghadiya']['name']}")
    print(f"Nakshatra: {result['details']['nakshatra']['name']}")
    print(f"\nKnowledge: {result['details']['knowledge'][:200]}...")
