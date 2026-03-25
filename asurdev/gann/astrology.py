"""
Gann Astrology — Planetary Cycles and Zodiac Integration
Connects W.D. Gann's methods with astronomical data
"""
import ephem
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class PlanetaryAspect:
    """Планетарный аспект"""
    planet1: str
    planet2: str
    aspect_type: str  # conjunction, opposition, square, trine
    degrees: float
    exact_date: datetime
    orb: float  # орб (расхождение в градусах)
    gann_significance: str


@dataclass
class ZodiacDegree:
    """Зодиакальный градус"""
    sign: str
    degree: float  # 0-30
    total_degrees: float  # 0-360
    interpretation: str


class GannAstrology:
    """
    Астрология Ганна — интеграция планетарных циклов с рыночным анализом.
    
    Ганн использовал:
    - Геоцентрические и гелиоцентрические координаты
    - Планетарные аспекты (соединения, оппозиции, квадратуры)
    - Фазы Луны (новолуния, полнолуния)
    - Затмения
    - Зодиакальные градусы как ценовые уровни
    """
    
    # Планеты и их символическое значение
    PLANET_MEANINGS = {
        "Sun": "Общий тренд, жизненная сила рынка",
        "Moon": "Краткосрочные колебания, эмоции толпы",
        "Mercury": "Коммуникации, новости, скорость",
        "Venus": "Гармония, стабильность, рост",
        "Mars": "Агрессия, волатильность, прорывы",
        "Jupiter": "Расширение, оптимизм, бычий тренд",
        "Saturn": "Сжатие, пессимизм, медвежий тренд",
        "Uranus": "Внезапные скачки, непредсказуемость",
        "Neptune": "Иллюзии, пузыри, неопределённость",
        "Pluto": "Трансформация, крупные игроки"
    }
    
    # Аспекты и их значения
    ASPECTS = {
        0: ("conjunction", "Соединение", "Усиление, кульминация"),
        60: ("sextile", "Секстиль", "Гармоя"),
        90: ("square", "Квадратура", "Напряжение, кризис"),
        120: ("trine", "Тригон", "Гармония, продолжение"),
        180: ("opposition", "Оппозиция", "Конфликт, разворот")
    }
    
    # Критические градусы Ганна
    CRITICAL_DEGREES = [
        0, 15, 30, 52, 60, 72, 90, 108, 120, 144, 180, 216, 240, 270, 288, 306, 360
    ]
    
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090):
        self.lat = lat
        self.lon = lon
    
    def get_planet_positions(self, date: datetime) -> Dict[str, float]:
        """Получить положение планет в градусах (0-360)."""
        positions = {}
        planets = [
            ("Sun", ephem.Sun()),
            ("Moon", ephem.Moon()),
            ("Mercury", ephem.Mercury()),
            ("Venus", ephem.Venus()),
            ("Mars", ephem.Mars()),
            ("Jupiter", ephem.Jupiter()),
            ("Saturn", ephem.Saturn()),
            ("Uranus", ephem.Uranus()),
            ("Neptune", ephem.Neptune()),
            ("Pluto", ephem.Pluto())
        ]
        
        date_str = date.strftime("%Y/%m/%d %H:%M:%S")
        
        for name, body in planets:
            body.compute(date_str)
            lon = float(body.hlong) % 360
            positions[name] = lon
        
        return positions
    
    def get_zodiac_degree(self, total_degrees: float) -> ZodiacDegree:
        """Конвертировать 0-360 в знак зодиака и градус."""
        sign_index = int(total_degrees // 30)
        degree_in_sign = total_degrees % 30
        
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", 
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        
        sign = signs[sign_index]
        
        if degree_in_sign < 10:
            interp = "early degree — формирование"
        elif degree_in_sign < 20:
            interp = "middle degree — развитие"
        else:
            interp = "late degree — завершение"
        
        return ZodiacDegree(
            sign=sign,
            degree=degree_in_sign,
            total_degrees=total_degrees,
            interpretation=interp
        )
    
    def find_aspects(
        self, 
        date: datetime, 
        orb: float = 2.0,
        include_major: bool = True
    ) -> List[PlanetaryAspect]:
        """Найти все планетарные аспекты на дату."""
        positions = self.get_planet_positions(date)
        aspects = []
        
        planets = list(positions.keys())
        
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                diff = abs(positions[p1] - positions[p2])
                if diff > 180:
                    diff = 360 - diff
                
                for asp_deg, (asp_name, asp_rus, asp_desc) in self.ASPECTS.items():
                    if include_major and asp_deg not in [0, 90, 120, 180]:
                        continue
                    
                    if abs(diff - asp_deg) <= orb:
                        aspects.append(PlanetaryAspect(
                            planet1=p1,
                            planet2=p2,
                            aspect_type=asp_name,
                            degrees=round(diff, 2),
                            exact_date=date,
                            orb=round(abs(diff - asp_deg), 2),
                            gann_significance=asp_desc
                        ))
        
        return aspects
    
    def get_moon_phases(self, start_date: datetime, days: int = 30) -> List[Dict]:
        """Получить фазы Луны на период."""
        phases = []
        date = start_date
        
        for _ in range(days):
            try:
                next_new = ephem.next_new_moon(date.strftime("%Y/%m/%d")).datetime()
                next_full = ephem.next_full_moon(date.strftime("%Y/%m/%d")).datetime()
                
                if next_new <= date + timedelta(days=1):
                    phases.append({
                        "type": "new_moon",
                        "date": next_new.strftime("%Y-%m-%d"),
                        "days_until": (next_new - date).days
                    })
                
                if next_full <= date + timedelta(days=1):
                    phases.append({
                        "type": "full_moon",
                        "date": next_full.strftime("%Y-%m-%d"),
                        "days_until": (next_full - date).days
                    })
                    
            except Exception:
                pass
            
            date += timedelta(days=1)
            if len(phases) >= 8:
                break
        
        return phases[:8]
    
    def convert_degree_to_price(
        self, 
        degree: float, 
        base_price: float,
        scale: str = "linear"
    ) -> float:
        """Конвертировать зодиакальный градус в ценовой уровень."""
        if scale == "log":
            return base_price * (1 + degree / 360)
        else:
            return base_price * degree / 360
    
    def get_pluto_position(self, date: datetime) -> Dict:
        """Плутон и великая перезарядка."""
        positions = self.get_planet_positions(date)
        pluto_deg = positions.get("Pluto", 0)
        zodiac = self.get_zodiac_degree(pluto_deg)
        
        return {
            "degree": round(pluto_deg, 2),
            "sign": zodiac.sign,
            "degree_in_sign": round(zodiac.degree, 2),
            "interpretation": "Plutonic reset cycle" if zodiac.sign == "Aquarius" else "Normal",
            "cycle_progress": round(pluto_deg / 360 * 100, 1)
        }


_gann_astro = None

def get_gann_astrology(lat: float = 28.6139, lon: float = 77.2090) -> GannAstrology:
    global _gann_astro
    if _gann_astro is None:
        _gann_astro = GannAstrology(lat, lon)
    return _gann_astro
