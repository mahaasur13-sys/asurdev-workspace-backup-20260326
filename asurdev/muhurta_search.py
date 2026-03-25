"""
Muhurta Search Module — Finding Auspicious Time for Actions
============================================================

Functions:
- find_muhurta(date, action, location)
- get_matching_rules(action)
- calculate_muhurta_windows(ephemeris_data, rules)

Requires: swiss_ephemeris, knowledge base in knowledge/vedic/
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

# Knowledge base path
KNOWLEDGE_PATH = os.path.join(
    os.path.dirname(__file__), 
    "knowledge", "vedic"
)

# Action to knowledge file mapping
ACTION_KNOWLEDGE_MAP = {
    "брак": "muhurta_marriage_rules.md",
    "свадьба": "muhurta_marriage_rules.md",
    "виаха": "muhurta_marriage_rules.md",
    "путешествие": "muhurta_travel_rules.md",
    "поездка": "muhurta_travel_rules.md",
    "бизнес": "muhurta_business_rules.md",
    "начало": "muhurta_business_rules.md",
    "ритуал": "muhurta_rituals_sacred.md",
    "инициация": "muhurta_rituals_sacred.md",
    "стрижка": "muhurta_rituals_sacred.md",
    "обряд": "muhurta_rituals_sacred.md",
}


@dataclass
class MuhurtaWindow:
    """A time window suitable for an action."""
    start_time: datetime
    end_time: datetime
    score: int  # 0-100
    reasons: List[str]
    applied_rules: List[str]
    nakshatra: str
    yoga: str
    tithi: str
    choghadiya_type: Optional[str] = None


class MuhurtaSearcher:
    """
    Search for auspicious time windows based on Vedic astrology rules.
    
    Usage:
        searcher = MuhurtaSearcher()
        windows = searcher.find_muhurta(
            date=datetime(2026, 3, 22),
            action="брак",
            lat=55.7558,
            lon=37.6173
        )
    """
    
    def __init__(self, knowledge_path: str = KNOWLEDGE_PATH):
        self.knowledge_path = knowledge_path
        self._rules_cache: Dict[str, str] = {}
    
    def find_muhurta(
        self,
        date: datetime,
        action: str,
        lat: float = 28.6139,
        lon: float = 77.2090,
        days_ahead: int = 7
    ) -> List[MuhurtaWindow]:
        """
        Find auspicious time windows for an action.
        
        Args:
            date: Start date for search
            action: Type of action (брак, путешествие, бизнес, etc.)
            lat, lon: Location coordinates
            days_ahead: Number of days to search
            
        Returns:
            List of MuhurtaWindow objects, sorted by score
        """
        # Get matching rules from knowledge base
        rules = self._get_rules_for_action(action)
        
        # Get ephemeris data for date range
        ephemeris_data = self._get_ephemeris_range(date, days_ahead, lat, lon)
        
        # Calculate windows
        windows = []
        for eph in ephemeris_data:
            window_score = self._evaluate_window(eph, rules, action)
            if window_score["score"] >= 50:
                windows.append(MuhurtaWindow(
                    start_time=window_score["start"],
                    end_time=window_score["end"],
                    score=window_score["score"],
                    reasons=window_score["reasons"],
                    applied_rules=window_score["rules_applied"],
                    nakshatra=eph.get("nakshatra", "Unknown"),
                    yoga=eph.get("yoga", "Unknown"),
                    tithi=eph.get("tithi", "Unknown"),
                    choghadiya_type=eph.get("choghadiya_type"),
                ))
        
        # Sort by score descending
        windows.sort(key=lambda w: w.score, reverse=True)
        return windows
    
    def _get_rules_for_action(self, action: str) -> List[str]:
        """Get rules from knowledge base matching the action."""
        rules = []
        action_lower = action.lower()
        
        # Find matching knowledge file
        for key, filename in ACTION_KNOWLEDGE_MAP.items():
            if key in action_lower:
                filepath = os.path.join(self.knowledge_path, filename)
                if os.path.exists(filepath):
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    rules.append(content)
        
        # Also scan all knowledge files for # tags
        if not rules:
            for filename in os.listdir(self.knowledge_path):
                if filename.endswith(".md"):
                    filepath = os.path.join(self.knowledge_path, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                    if any(tag in content.lower() for tag in [action_lower, f"#{action_lower}"]):
                        rules.append(content)
        
        return rules
    
    def _get_ephemeris_range(
        self, 
        start_date: datetime, 
        days: int,
        lat: float,
        lon: float
    ) -> List[Dict]:
        """Get ephemeris data for a date range using Swiss Ephemeris."""
        try:
            from swiss_ephemeris import swiss_ephemeris
            
            results = []
            for i in range(days):
                d = start_date + timedelta(days=i)
                date_str = d.strftime("%Y-%m-%d")
                time_str = d.strftime("%H:%M:%S")
                
                eph = swiss_ephemeris(
                    date=date_str,
                    time=time_str,
                    lat=lat,
                    lon=lon,
                    compute_panchanga=True,
                    compute_choghadiya=True,
                )
                
                if not eph.get("error"):
                    results.append({
                        "date": date_str,
                        "time": time_str,
                        "nakshatra": eph.get("panchanga", {}).get("nakshatra", "Unknown"),
                        "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
                        "tithi": eph.get("panchanga", {}).get("tithi", "Unknown"),
                        "vara": eph.get("panchanga", {}).get("vara", "Unknown"),
                        "karana": eph.get("panchanga", {}).get("karana", "Unknown"),
                        "choghadiya_type": eph.get("current_choghadiya", {}).get("type"),
                        "positions": eph.get("positions", {}),
                    })
            
            return results
            
        except ImportError:
            # Fallback: return empty list
            return []
    
    def _evaluate_window(
        self, 
        eph: Dict, 
        rules: List[str],
        action: str
    ) -> Dict:
        """
        Evaluate if an ephemeris moment is auspicious for the action.
        
        Returns:
            Dict with score, reasons, rules_applied, start, end
        """
        score = 50  # Base score
        reasons = []
        rules_applied = []
        
        # Check nakshatra
        nakshatra = eph.get("nakshatra", "")
        action_lower = action.lower()
        
        # Positive nakshatras for most actions
        good_nakshatras = [
            "Rohini", "Mrigashira", "Punarvasu", "Pushya",
            "Hasta", "Swati", "Uttara Phalguni", "Shravana",
            "Uttara Ashadha", "Uttara Bhadrapada", "Revati"
        ]
        
        # Translate to Russian if needed
        nakshatra_ru = {
            "Rohini": "Рохини", "Mrigashira": "Мригашира",
            "Punarvasu": "Пунарвасу", "Pushya": "Пушья",
            "Hasta": "Хаста", "Swati": "Свати",
            "Uttara Phalguni": "Уттара Пхалгуни", "Shravana": "Шравана",
            "Uttara Ashadha": "Уттара Ашадха",
            "Uttara Bhadrapada": "Уттара Бхадрапада", "Revati": "Ревати"
        }
        
        for good_nak, good_nak_ru in nakshatra_ru.items():
            if good_nak in nakshatra or good_nak_ru in nakshatra:
                score += 15
                reasons.append(f"Благоприятная накшатра: {nakshatra}")
                rules_applied.append(f"Накшатра: {nakshatra}")
                break
        
        # Check yoga
        yoga = eph.get("yoga", "")
        good_yogas = ["Siddhi", "Saubhagya", "Shobhana", "Priti"]
        bad_yogas = ["Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra", "Vyatipata"]
        
        for gy in good_yogas:
            if gy in yoga:
                score += 10
                reasons.append(f"Благоприятная йога: {yoga}")
                rules_applied.append(f"Йога: {yoga}")
                break
        
        for by in bad_yogas:
            if by in yoga:
                score -= 20
                reasons.append(f"Неблагоприятная йога: {yoga}")
                rules_applied.append(f"Йога: {yoga}")
                break
        
        # Check Choghadiya
        chogh = eph.get("choghadiya_type", "")
        good_chogh = ["Amrit", "Siddha", "Shubha", "Labha"]
        if chogh in good_chogh:
            score += 10
            reasons.append(f"Благоприятная Чогадия: {chogh}")
            rules_applied.append(f"Чогадия: {chogh}")
        
        # Check rules from knowledge base
        rules_text = "\n".join(rules)
        if "Виваха" in rules_text or "брак" in action_lower:
            # Check for nakshatra dosha
            bad_nakshatras = ["Ashlesha", "Mula", "Jyeshtha", "Vishakha"]
            for bn in bad_nakshatras:
                if bn in nakshatra or nakshatra_ru.get(bn, "") in nakshatra:
                    score -= 25
                    reasons.append(f"Накшатра-доша: {nakshatra}")
                    rules_applied.append(f"Доша: {bn}")
                    break
        
        # Day of week adjustments
        day_scores = {
            "Sunday": 0, "Monday": 5, "Tuesday": -10,
            "Wednesday": 5, "Thursday": 15, "Friday": 10, "Saturday": -5
        }
        vara = eph.get("vara", "")
        if vara in day_scores:
            score += day_scores[vara]
            if day_scores[vara] > 0:
                reasons.append(f"Благоприятный день: {vara}")
            rules_applied.append(f"День недели: {vara}")
        
        # Parse datetime
        dt = datetime.fromisoformat(f"{eph['date']} {eph['time']}")
        
        return {
            "score": max(0, min(100, score)),
            "reasons": reasons,
            "rules_applied": rules_applied,
            "start": dt,
            "end": dt + timedelta(hours=1),
        }
    
    def get_best_muhurta(
        self,
        date: datetime,
        action: str,
        lat: float = 28.6139,
        lon: float = 77.2090
    ) -> Optional[MuhurtaWindow]:
        """Get the single best muhurta for an action."""
        windows = self.find_muhurta(date, action, lat, lon)
        return windows[0] if windows else None


# Convenience function
def find_muhurta(
    date: datetime,
    action: str,
    lat: float = 28.6139,
    lon: float = 77.2090,
    days_ahead: int = 7
) -> List[Dict]:
    """
    Find auspicious time windows for an action.
    
    Returns list of dicts with: start_time, end_time, score, reasons, nakshatra, yoga, tithi
    """
    searcher = MuhurtaSearcher()
    windows = searcher.find_muhurta(date, action, lat, lon, days_ahead)
    
    return [
        {
            "start_time": w.start_time.isoformat(),
            "end_time": w.end_time.isoformat(),
            "score": w.score,
            "reasons": w.reasons,
            "applied_rules": w.applied_rules,
            "nakshatra": w.nakshatra,
            "yoga": w.yoga,
            "tithi": w.tithi,
            "choghadiya": w.choghadiya_type,
        }
        for w in windows
    ]


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python muhurta_search.py <date> <action> [lat] [lon]")
        print("Example: python muhurta_search.py 2026-03-22 брак 55.7558 37.6173")
        sys.exit(1)
    
    date_str = sys.argv[1]
    action = sys.argv[2]
    lat = float(sys.argv[3]) if len(sys.argv) > 3 else 28.6139
    lon = float(sys.argv[4]) if len(sys.argv) > 4 else 77.2090
    
    date = datetime.fromisoformat(date_str)
    
    print(f"Поиск благоприятной мухурты для: {action}")
    print(f"Дата: {date_str}, Координаты: ({lat}, {lon})")
    print("=" * 60)
    
    windows = find_muhurta(date, action, lat, lon)
    
    if not windows:
        print("Не найдено благоприятных окон. Попробуйте расширить диапазон поиска.")
    else:
        for i, w in enumerate(windows[:5], 1):
            print(f"\n{i}. {w['start_time'][:16]} — {w['end_time'][11:16]}")
            print(f"   Оценка: {w['score']}/100")
            print(f"   Накшатра: {w['nakshatra']} | Йога: {w['yoga']} | Титхи: {w['tithi']}")
            if w['choghadiya']:
                print(f"   Чогадия: {w['choghadiya']}")
            print(f"   Причины: {', '.join(w['reasons'])}")
