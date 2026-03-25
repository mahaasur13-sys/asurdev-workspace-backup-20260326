"""
Death Zones — Gann's Catastrophe Cycles
Based on musical octaves and planetary cycles
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class DeathZone:
    """Зона смерти"""
    day: int
    name: str
    severity: str  # minor, medium, major, critical
    description: str
    bitcoin_relevance: Optional[str] = None


class DeathZones:
    """
    Зоны смерти по Ганну.
    
    Ганн выделял периоды, когда рынок или жизнь подвержены "катастрофам":
    - 7-10 дней: первый опасный период
    - 21-28 дней: второй (месячный цикл)
    - 43 дня: третий (key reversal)
    - 73 дней: четвёртый (полный цикл)
    - 79-81 дней: Биткоин-specific (проверено на графиках)
    - 144 дня: Квадрат 12
    - 154 дня: от минимума 7 ноября до 13 апреля
    
    Музыкальная аналогия: 8 октав, после которых шкала сбрасывается.
    """
    
    # Основные зоны смерти
    PRIMARY_ZONES = [
        (7, "7 days", "minor", "Первый опасный период"),
        (10, "10 days", "minor", "Конец первой недели"),
        (21, "21 days", "medium", "Месяц (3 недели)"),
        (28, "28 days", "medium", "Лунный цикл"),
        (43, "43 days", "major", "Key reversal window"),
        (73, "73 days", "major", "Полный цикл"),
        (79, "79 days", "critical", "Биткоин cycle top"),
        (81, "81 days", "critical", "Биткоин cycle confirmation"),
    ]
    
    # Расширенные зоны (второй-четвёртый круг)
    EXTENDED_ZONES = [
        (108, "108 days", "medium", "Квадрат 144 в градусах"),
        (120, "120 days", "major", "Солнечный цикл"),
        (144, "144 days", "major", "Квадрат 12"),
        (154, "154 days", "critical", "BTC Nov-Apr cycle"),
        (180, "180 days", "major", "Полугодие"),
        (216, "216 days", "medium", "3/4 года"),
        (260, "260 days", "major", "Тропический год × 5/7"),
        (288, "288 days", "medium", "Квадрат 144 + 2 октавы"),
        (360, "360 days", "critical", "Полный круг"),
    ]
    
    # Все зоны
    ALL_ZONES = PRIMARY_ZONES + EXTENDED_ZONES
    
    @classmethod
    def get_zones(cls, up_to_day: int = 360) -> List[DeathZone]:
        """Получить все зоны до указанного дня."""
        zones = []
        for day, name, severity, desc in cls.ALL_ZONES:
            if day <= up_to_day:
                # Bitcoin relevance
                btc_rel = None
                if day == 79:
                    btc_rel = "От вершины до смены тренда ~79 дней"
                elif day == 81:
                    btc_rel = "Подтверждение цикла Биткоина"
                elif day == 154:
                    btc_rel = "От минимума 7 ноября до 13 апреля"
                
                zones.append(DeathZone(
                    day=day,
                    name=name,
                    severity=severity,
                    description=desc,
                    bitcoin_relevance=btc_rel
                ))
        return zones
    
    @classmethod
    def calculate_windows(
        cls, 
        start_date: str, 
        zones: List[Tuple[int, str, str, str]] = None
    ) -> List[Dict]:
        """
        Рассчитывает даты временных окон от start_date.
        
        Args:
            start_date: ISO format date string
            zones: Optional custom zones list
        
        Returns:
            List of {day, date, severity, description}
        """
        if zones is None:
            zones = cls.ALL_ZONES
        
        # Parse start date
        try:
            start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            if start.tzinfo:
                start = start.replace(tzinfo=None)
        except:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        
        windows = []
        for day, name, severity, desc in zones:
            window_date = start + timedelta(days=day)
            windows.append({
                "day": day,
                "date": window_date.strftime("%Y-%m-%d"),
                "date_obj": window_date,
                "name": name,
                "severity": severity,
                "description": desc,
                "is_past": window_date < datetime.now()
            })
        
        return windows
    
    @classmethod
    def get_upcoming(cls, start_date: str, days_ahead: int = 90) -> List[Dict]:
        """Получить предстоящие зоны смерти."""
        windows = cls.calculate_windows(start_date)
        return [w for w in windows if not w["is_past"]][:days_ahead]
    
    @classmethod
    def get_btc_cycles(cls) -> Dict:
        """
        Биткоин-специфичные циклы.
        Проверено на графиках последних трёх циклов.
        """
        return {
            "top_to_trend_change": {
                "days": [79, 81],
                "description": "От вершины до смены тренда",
                "confirmed": True
            },
            "nov_apr_cycle": {
                "from_date": "2025-11-07",
                "to_date": "2026-04-13", 
                "days": 154,
                "description": "От минимума 7 ноября до 13 апреля",
                "confirmed": True
            },
            "correction_targets": {
                "levels": [
                    (0.72, "72%", "Первая цель"),
                    (0.77, "77%", "Историческая коррекция"),
                    (0.82, "82%", "Максимальная коррекция")
                ],
                "note": "BTC исторически корректируется на 77-82% от вершины"
            }
        }
    
    @classmethod
    def calculate_btc_targets(
        cls, 
        top_price: float, 
        correction_pct: float = 0.77
    ) -> Dict:
        """
        Рассчитывает цели Биткоина на основе коррекции.
        
        Args:
            top_price: Цена вершины (например, 126000)
            correction_pct: Процент коррекции (0.77 = 77%)
        
        Returns:
            Dict с целями
        """
        targets = {}
        for pct in [0.72, 0.75, 0.77, 0.80, 0.82]:
            target = top_price * (1 - pct)
            targets[f"{int(pct*100)}%"] = round(target, 0)
        
        return {
            "top": top_price,
            "targets": targets,
            "main_target": round(top_price * (1 - correction_pct), 0),
            "extremes": {
                "optimistic": round(top_price * 0.72, 0),   # 72%
                "base": round(top_price * 0.77, 0),         # 77%
                "pessimistic": round(top_price * 0.82, 0)   # 82%
            }
        }


# Singleton
_death_zones = None

def get_death_zones() -> DeathZones:
    global _death_zones
    if _death_zones is None:
        _death_zones = DeathZones()
    return _death_zones
