"""
Vedic Astrologer Agent (Mankashi) for AstroFin Sentinel

Analyzes astrological factors for trading decisions.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from tools.mankashi import get_astrology_tool


@dataclass
class AstroReport:
    """Output from Vedic Astrologer Agent."""
    muhurta: dict  # overall, best_time, worst_time, reasoning
    favorable: list  # [{"activity": "...", "reasoning": "..."}]
    unfavorable: list
    planetary_yoga: dict  # active, interpretation
    transits: dict  # benefic, malefic
    dasha: dict  # current, sub_current, effect_on_finance
    signal: str  # BUY, SELL, HOLD, WAIT, STRONG_BUY, STRONG_SELL
    confidence: float  # 0.0 - 1.0
    reasoning: str
    forecast_text: str = ""
    # NEW: Extended fields for nuance
    planet_strength: dict = None  # {planet: "exalted|normal|fallen"}
    nakshatra_influence: str = ""
    moon_phase: str = ""
    eclipse_risk: bool = False


class VedicAstrologerAgent:
    """
    Vedic Astrologer Agent using Mankashi system.
    
    Analyzes:
    - Daily Muhurta (auspicious timing)
    - Planetary yogas
    - Planetary strength (exaltation/fall)
    - Nakshatra influences
    - Transits
    - Dasha periods
    - Eclipse risks
    """
    
    # Planet strength indicators in text
    EXALTATION_KEYWORDS = ["экзальтация", "экзальтирован", "✱", "сильн", "сильная"]
    FALL_KEYWORDS = ["падение", "ослаблен", "⚠️", "слаб"]
    
    # Nakshatra influences on finance
    NAKSHATRA_FINANCE_MAP = {
        "ashwini": "fast_gains",
        "bharani": "transformation",
        "krittika": "intensity",
        "rohini": "growth",
        "mrigashira": "search",
        "ardra": "upheaval",
        "punarvasu": "recovery",
        "pushya": "nurturing",
        "ashlesha": "hidden",
        "magha": "ancestral",
        "purva_phalguni": "pleasure",
        "utta_phalguni": "friendship",
        "hasta": "skill",
        "chitra": "creativity",
        "swati": "independence",
        "vishakha": "expansion",
        "anuradha": "loyalty",
        "jyeshtha": "priority",
        "mula": "roots",
        "purva_ashadha": "victory",
        "utta_ashadha": "courage",
        "shravana": "learning",
        "dhanishta": "wealth",
        "shatabhisha": "uniqueness",
        "purva_bhadrapada": "transformation",
        "uttara_bhadrapada": "service",
        "revati": "prosperity"
    }
    
    def __init__(self, birth_date: str = None, birth_time: str = None,
                 location: tuple = None):
        """
        Initialize astrologer.
        
        Args:
            birth_date: Birth date (DD.MM.YYYY)
            birth_time: Birth time (HH:MM)
            location: (latitude, longitude) tuple
        """
        self.astrology_tool = get_astrology_tool()
        self.birth_date = birth_date
        self.birth_time = birth_time
        self.location = location or (53.2, 50.15)  # Samara, Russia default
        
        # Load birth chart if date provided
        self.birth_chart = None
        if birth_date and birth_time:
            self.birth_chart = self.astrology_tool.get_birth_chart(
                birth_date, birth_time,
                self.location[0], self.location[1]
            )
    
    def analyze(self, symbol: str = None, side: str = "buy",
                date: str = None) -> AstroReport:
        """
        Perform astrological analysis with extended nuance.
        
        Args:
            symbol: Trading pair (optional)
            side: "buy" or "sell"
            date: Date for analysis (YYYY-MM-DD, default today)
            
        Returns:
            AstroReport with astrological analysis
        """
        # Get Mankashi forecast
        forecast = self.astrology_tool.get_daily_forecast(date)
        
        # Parse forecast text
        forecast_text = forecast.get("forecast", "")
        
        # Extract astrological data from forecast
        muhurta = self._extract_muhurta(forecast_text)
        favorable = self._extract_favorable(forecast_text)
        unfavorable = self._extract_unfavorable(forecast_text)
        yogas = self._extract_yogas(forecast_text)
        transits = self._extract_transits(forecast_text)
        
        # NEW: Extract planet strength
        planet_strength = self._analyze_planet_strength(forecast_text)
        
        # NEW: Extract nakshatra influence
        nakshatra = self._extract_nakshatra(forecast_text)
        
        # NEW: Extract moon phase
        moon_phase = self._extract_moon_phase(forecast_text)
        
        # NEW: Check eclipse risk
        eclipse_risk = self._check_eclipse_risk(forecast_text)
        
        # Determine signal with extended nuance
        signal, confidence = self._determine_signal_nuanced(
            muhurta, favorable, unfavorable, planet_strength, 
            nakshatra, eclipse_risk, side
        )
        
        # Generate reasoning with extended details
        reasoning = self._generate_reasoning_nuanced(
            signal, muhurta, yogas, transits, planet_strength, 
            nakshatra, eclipse_risk, side
        )
        
        return AstroReport(
            muhurta=muhurta,
            favorable=favorable,
            unfavorable=unfavorable,
            planetary_yoga=yogas,
            transits=transits,
            dasha=self._get_dasha_placeholder(),
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            forecast_text=forecast_text[:500] if forecast_text else "",
            planet_strength=planet_strength,
            nakshatra_influence=nakshatra,
            moon_phase=moon_phase,
            eclipse_risk=eclipse_risk
        )
    
    # NEW: Planet strength analysis
    def _analyze_planet_strength(self, text: str) -> dict:
        """
        Analyze planetary strength (exaltation vs fall).
        
        Returns:
            dict with planet names and their strength status
        """
        strength = {}
        
        planets = {
            "Солнце": ["Солнце", "Сурья"],
            "Луна": ["Луна", "Чандра"],
            "Марс": ["Марс", "Мангал"],
            "Меркурий": ["Меркурий", "Буддха"],
            "Юпитер": ["Юпитер", "Брихаспати", "Гуру"],
            "Венера": ["Венера", "Шукра"],
            "Сатурн": ["Сатурн", "Шани"]
        }
        
        for planet_name, aliases in planets.items():
            # Check for exaltation
            for alias in aliases:
                if alias in text:
                    if any(kw in text.lower() for kw in self.EXALTATION_KEYWORDS):
                        strength[planet_name] = "exalted"
                    elif any(kw in text for kw in self.FALL_KEYWORDS):
                        strength[planet_name] = "fallen"
                    else:
                        strength[planet_name] = "normal"
                    break
        
        return strength
    
    # NEW: Nakshatra influence extraction
    def _extract_nakshatra(self, text: str) -> str:
        """Extract nakshatra (lunar mansion) influence."""
        # Check for nakshatra mentions
        nakshatras = list(self.NAKSHATRA_FINANCE_MAP.keys())
        
        for nak in nakshatras:
            if nak.lower() in text.lower():
                influence = self.NAKSHATRA_FINANCE_MAP.get(nak, "neutral")
                return f"{nak}: {influence}"
        
        # Check for common nakshatra names in Russian
        russian_nakshatras = {
            "Рохини": "growth",
            "Ашвини": "fast_gains",
            "Мула": "roots",
            "Шравана": "learning",
            "Ревати": "prosperity"
        }
        
        for rus_name, influence in russian_nakshatras.items():
            if rus_name in text:
                return f"{rus_name}: {influence}"
        
        return "Не определено"
    
    # NEW: Moon phase extraction
    def _extract_moon_phase(self, text: str) -> str:
        """Extract moon phase from text."""
        if "полнолуние" in text.lower() or "пурнима" in text.lower():
            return "FULL_MOON"
        elif "новолуние" in text.lower() or "амавасья" in text.lower():
            return "NEW_MOON"
        elif "первая четверть" in text.lower():
            return "FIRST_QUARTER"
        elif "последняя четверть" in text.lower():
            return "LAST_QUARTER"
        return "Не определено"
    
    # NEW: Eclipse risk check
    def _check_eclipse_risk(self, text: str) -> bool:
        """Check if there's eclipse risk mentioned."""
        eclipse_keywords = ["затмение", "эклипс", "грахана", "sun eclipse", "lunar eclipse"]
        return any(kw in text.lower() for kw in eclipse_keywords)
    
    # NEW: Nuanced signal determination
    def _determine_signal_nuanced(self, muhurta: dict, favorable: list,
                                 unfavorable: list, planet_strength: dict,
                                 nakshatra: str, eclipse_risk: bool,
                                 side: str) -> tuple:
        """
        Determine trading signal with more nuance.
        
        Considers:
        - Muhurta quality
        - Planet strength (exalted vs fallen)
        - Specific yogas
        - Eclipse risk
        - Activity match (buy/sell side)
        - Moon phase
        """
        score = 0.50  # Neutral baseline
        
        # 1. Muhurta influence (main factor)
        muhurta_scores = {
            "HIGHLY_FAVORABLE": 0.30,
            "FAVORABLE": 0.18,
            "NEUTRAL": 0.00,
            "UNFAVORABLE": -0.25,
            "HIGHLY_UNFAVORABLE": -0.40
        }
        score += muhurta_scores.get(muhurta.get("overall", "NEUTRAL"), 0.00)
        
        # 2. Planet strength influence
        exalted_count = sum(1 for s in planet_strength.values() if s == "exalted")
        fallen_count = sum(1 for s in planet_strength.values() if s == "fallen")
        score += (exalted_count * 0.07) - (fallen_count * 0.10)
        
        # 3. Eclipse risk - major negative
        if eclipse_risk:
            score -= 0.20
        
        # 4. Favorable/unfavorable activity match
        side_lower = side.lower()
        side_map = {
            "buy": ["покупка", "накоплен", "инвестиц", "долгосрочн"],
            "sell": ["продажа", "реализац", "спекуляц"]
        }
        
        for f in favorable:
            if any(kw in f["activity"].lower() for kw in side_map.get(side_lower, [])):
                score += 0.06
        
        for u in unfavorable:
            if any(kw in u["activity"].lower() for kw in side_map.get(side_lower, [])):
                score -= 0.12
        
        # 5. Moon phase modifier
        if nakshatra == "revati" or "prosperity" in nakshatra:
            score += 0.05
        elif nakshatra == "mula" or "roots" in nakshatra:
            score += 0.03
        
        # Cap score
        score = max(0.15, min(0.92, score))
        
        # Determine signal with STRONG variants
        if score >= 0.72:
            signal = "STRONG_BUY" if side.lower() == "buy" else "STRONG_SELL"
        elif score >= 0.58:
            signal = "BUY" if side.lower() == "buy" else "SELL"
        elif score <= 0.38:
            signal = "WAIT"
        else:
            signal = "HOLD"
        
        # Confidence reflects score magnitude
        confidence = min(score, 0.88)
        
        return signal, confidence
    
    # NEW: Generate nuanced reasoning
    def _generate_reasoning_nuanced(self, signal: str, muhurta: dict,
                                   yogas: dict, transits: dict,
                                   planet_strength: dict, nakshatra: str,
                                   eclipse_risk: bool, side: str) -> str:
        """Generate detailed reasoning summary."""
        reasoning = f"Сигнал: {signal} ({side.upper()}). "
        reasoning += f"Мухурта: {muhurta.get('overall', 'NEUTRAL')}."
        
        # Planet strength details
        if planet_strength:
            exalted = [p for p, s in planet_strength.items() if s == "exalted"]
            fallen = [p for p, s in planet_strength.items() if s == "fallen"]
            if exalted:
                reasoning += f" В экзальтации: {', '.join(exalted)}."
            if fallen:
                reasoning += f" В падении: {', '.join(fallen)}."
        
        # Muhurta timing
        if muhurta.get("best_time"):
            reasoning += f" Лучшее время: {muhurta['best_time']}."
        
        # Yogas
        if yogas.get("active"):
            reasoning += f" Йоги: {', '.join(yogas['active'][:2])}."
        
        # Nakshatra
        if nakshatra and nakshatra != "Не определено":
            reasoning += f" Накшатра: {nakshatra}."
        
        # Eclipse warning
        if eclipse_risk:
            reasoning += " ⚠️ ВНИМАНИЕ: Риск затмения!"
        
        return reasoning
    
    # Keep legacy method for backward compatibility
    def _determine_signal(self, muhurta: dict, favorable: list,
                         unfavorable: list, side: str) -> tuple:
        """Legacy signal determination (calls new method)."""
        return self._determine_signal_nuanced(
            muhurta, favorable, unfavorable, {}, "", False, side
        )
    
    def _generate_reasoning(self, signal: str, muhurta: dict,
                           yogas: dict, transits: dict, side: str) -> str:
        """Legacy reasoning generation."""
        return self._generate_reasoning_nuanced(
            signal, muhurta, yogas, transits, {}, "", False, side
        )
    
    def _extract_muhurta(self, text: str) -> dict:
        """Extract Muhurta (timing) information from forecast text."""
        muhurta = {
            "overall": "NEUTRAL",
            "best_time": None,
            "worst_time": None,
            "reasoning": ""
        }
        
        # Check for favorable indicators
        if "БЛАГОПРИЯТНО" in text or "благоприятно" in text:
            muhurta["overall"] = "FAVORABLE"
            muhurta["reasoning"] = "Астрологические показатели благоприятны"
        
        if "✱" in text or "ЭКЗАЛЬТАЦИЯ" in text:
            muhurta["overall"] = "HIGHLY_FAVORABLE"
            muhurta["reasoning"] = "Планеты в экзальтации - сильное время"
        
        if "⚠️" in text or "ПАДЕНИЕ" in text:
            muhurta["overall"] = "UNFAVORABLE"
            muhurta["reasoning"] = "Неблагоприятные планетные влияния"
        
        # Extract times
        time_pattern = r'(\d{1,2}:\d{2})'
        times = re.findall(time_pattern, text)
        if len(times) >= 2:
            muhurta["best_time"] = f"{times[0]} - {times[1]}"
        
        # Check for specific time mentions
        if "14:00" in text:
            muhurta["best_time"] = "14:00 - 17:00"
        if "15:00" in text:
            muhurta["worst_time"] = "15:00 - 18:00"
        
        return muhurta
    
    def _extract_favorable(self, text: str) -> list:
        """Extract favorable activities from forecast."""
        favorable = []
        
        favorable_keywords = {
            "покупка": "Покупка активов",
            "долгосрочное": "Долгосрочные инвестиции",
            " духовн": "Духовные практики",
            "образование": "Образование и исследования",
            "путешеств": "Путешествия",
            "творчеств": "Творчество"
        }
        
        for keyword, activity in favorable_keywords.items():
            if keyword in text.lower():
                favorable.append({
                    "activity": activity,
                    "reasoning": f"Найдено в прогнозе: {keyword}"
                })
        
        return favorable
    
    def _extract_unfavorable(self, text: str) -> list:
        """Extract unfavorable activities from forecast."""
        unfavorable = []
        
        unfavorable_keywords = {
            "продажа": "Агрессивная продажа",
            "контракт": "Подписание контрактов",
            "спекуляц": "Спекуляции",
            "слух": "Ложные слухи"
        }
        
        for keyword, activity in unfavorable_keywords.items():
            if keyword in text.lower():
                unfavorable.append({
                    "activity": activity,
                    "reasoning": f"Найдено в прогнозе: {keyword}"
                })
        
        return unfavorable
    
    def _extract_yogas(self, text: str) -> dict:
        """Extract planetary yogas from forecast."""
        yogas = {"active": [], "interpretation": ""}
        
        # Check for specific yogas mentioned
        yoga_patterns = [
            "Дхана Йога",
            "Ханса Йога",
            "Махапарджара",
            "Арапарвая",
            "Бханди"
        ]
        
        for yoga in yoga_patterns:
            if yoga in text:
                yogas["active"].append(yoga)
        
        if yogas["active"]:
            yogas["interpretation"] = f"Активны йоги: {', '.join(yogas['active'])}"
        else:
            yogas["interpretation"] = "Специфических йог не выявлено"
        
        return yogas
    
    def _extract_transits(self, text: str) -> dict:
        """Extract transit information from forecast."""
        transits = {"benefic": [], "malefic": []}
        
        # Check for planet mentions with context
        planets_benefic = ["Юпитер", "Венера", "Меркурий"]
        planets_malefic = ["Сатурн", "Марс"]
        
        for planet in planets_benefic:
            if planet in text:
                transits["benefic"].append(f"{planet} активен")
        
        for planet in planets_malefic:
            if planet in text:
                transits["malefic"].append(f"{planet} требует осторожности")
        
        return transits
    
    def _get_dasha_placeholder(self) -> dict:
        """Get current dasha (placeholder - would use actual calculation)."""
        return {
            "current": "Меркурий Маха Даша",
            "sub_current": "Кету Антара Даша",
            "effect_on_finance": "Период трансформации, осторожность в спекуляциях"
        }
    
    def to_dict(self, report: AstroReport) -> dict:
        """Convert report to dictionary."""
        return asdict(report)


# Global instance
_astrologer_agent = None

def get_astrologer(birth_date: str = None, birth_time: str = None) -> VedicAstrologerAgent:
    global _astrologer_agent
    if _astrologer_agent is None:
        _astrologer_agent = VedicAstrologerAgent(birth_date, birth_time)
    return _astrologer_agent
