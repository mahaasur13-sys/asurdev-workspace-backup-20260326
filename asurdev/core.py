#!/usr/bin/env python3
"""asurdev Sentinel — Swiss Ephemeris Core v2.10.03"""
import swisseph as swe
from datetime import datetime, timezone
from typing import Dict, List
import json

AYANAMSA_LAHIRI = swe.SIDM_LAHIRI

NAKSHATRAS = ['Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra',
    'Punarvasu', 'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni',
    'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishtha', 'Shatabhisha',
    'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati']

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
    'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

TITHIS = ['Shukla Prathama', 'Shukla Dvitiya', 'Shukla Tritiya', 'Shukla Chaturthi', 'Shukla Panchami',
    'Shukla Shashti', 'Shukla Saptami', 'Shukla Ashtami', 'Shukla Navami', 'Shukla Dashami',
    'Shukla Ekadashi', 'Shukla Dvadashi', 'Shukla Trayodashi', 'Shukla Chaturdashi', 'Poornima',
    'Krishna Prathama', 'Krishna Dvitiya', 'Krishna Tritiya', 'Krishna Chaturthi', 'Krishna Panchami',
    'Krishna Shashti', 'Krishna Saptami', 'Krishna Ashtami', 'Krishna Navami', 'Krishna Dashami',
    'Krishna Ekadashi', 'Krishna Dvadashi', 'Krishna Trayodashi', 'Krishna Chaturdashi', 'Amavasya']

YOGAS = ['Vishkumbha', 'Priti', 'Ayushman', 'Saubhagya', 'Shobhana', 'Atiganda', 'Sukarma', 'Dhriti', 'Shula', 'Ganda',
    'Vriddhi', 'Dhruva', 'Vyaghata', 'Harshana', 'Vajra', 'Siddhi', 'Vyatipata', 'Variyana', 'Parigha', 'Shiva',
    'Siddha', 'Sadhya', 'Shubha', 'Shukla', 'Brahma', 'Indra', 'Vaidhriti']

VARAS = ['Ravivara (Sunday)', 'Somavara (Monday)', 'Mangalavara (Tuesday)', 
    'Budhawara (Wednesday)', 'Guruvara (Thursday)', 'Shukravara (Friday)', 'Schanivara (Saturday)']

KARANAS = ['Bava', 'Balava', 'Kaulava', 'Taitila', 'Garija', 'Vanija', 'Vishti', 'Bhadra', 'Kinstughna', 'Sakuna']

def normalize_angle(angle):
    while angle < 0: angle += 360
    while angle >= 360: angle -= 360
    return angle

def calculate_tithi(sun_lon, moon_lon) -> int:
    """Tithi = (Moon - Sun) mod 30"""
    diff = normalize_angle(moon_lon - sun_lon)
    return int(diff // 12)

def calculate_nakshatra(lon) -> int:
    """27 Nakshatras, each 13°20' (13.3333°)"""
    return int(lon // 13.3333) % 27

def calculate_yoga(sun_lon, moon_lon) -> int:
    """Yoga = (Sun + Moon) mod 27"""
    total = normalize_angle(sun_lon + moon_lon)
    return int(total // 13.3333) % 27

def calculate_karana(sun_lon, moon_lon) -> int:
    """Karana = (Moon - Sun) mod 11"""
    diff = normalize_angle(moon_lon - sun_lon)
    return int(diff // 3.2727) % 11

class SwissEphemerisCore:
    def __init__(self, ayanamsa: int = AYANAMSA_LAHIRI):
        swe.set_ephe_path('/home/workspace/asurdevSentinel/ephemeris/')
        swe.set_sid_mode(ayanamsa)
        self.ayanamsa = ayanamsa
        self.last_raw_data = {}

    def calculate_planets(self, date: str, time: str, lat: float, lon: float, utc: bool = True) -> Dict:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        dt = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc) if utc else datetime(year, month, day, hour, minute, second)
        jd = swe.julday(year, month, day, hour + minute/60 + second/3600)
        
        planet_ids = [(swe.SUN, 'Sun'), (swe.MOON, 'Moon'), (swe.MERCURY, 'Mercury'),
            (swe.VENUS, 'Venus'), (swe.MARS, 'Mars'), (swe.JUPITER, 'Jupiter'),
            (swe.SATURN, 'Saturn'), (swe.URANUS, 'Uranus'), (swe.NEPTUNE, 'Neptune'),
            (swe.PLUTO, 'Pluto'), (swe.MEAN_NODE, 'North_Node')]
        
        planets = {}
        for pid, name in planet_ids:
            pos = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
            speed = swe.calc_ut(jd, pid, swe.FLG_SPEED)
            lon_val = pos[0][0]
            planets[name] = {
                'longitude': round(lon_val, 6),
                'latitude': round(pos[0][1], 6),
                'distance': round(pos[0][2], 6),
                'speed_longitude': round(speed[0][3], 6),
                'retrograde': speed[0][3] < 0,
                'nakshatra': NAKSHATRAS[int(lon_val // 13.3333) % 27],
                'sign': SIGNS[int(lon_val // 30)],
                'degree_in_sign': round(lon_val % 30, 4)
            }
            
        self.last_raw_data = {'jd': jd, 'datetime_utc': dt.isoformat(), 'latitude': lat, 'longitude': lon,
            'ayanamsa': self.ayanamsa, 'ayanamsa_name': 'Lahiri', 'source': 'Swiss Ephemeris 2.10.03', 'planets': planets}
        return self.last_raw_data

    def calculate_houses(self, date: str, time: str, lat: float, lon: float, system: str = 'placidus') -> Dict:
        year, month, day = map(int, date.split('-'))
        hour, minute, second = map(int, time.split(':'))
        jd = swe.julday(year, month, day, hour + minute/60 + second/3600)
        houses = swe.houses(jd, lat, lon, b'P')
        house_cusps = [round(h, 4) for h in houses[0][:12]]
        house_signs = [SIGNS[int(h // 30)] for h in house_cusps]
        return {'ascendant': round(houses[0][0], 4), 'midheaven': round(houses[0][1], 4), 'house_cusps': house_cusps, 'house_signs': house_signs}

    def calculate_aspects(self, planets: Dict) -> List[Dict]:
        aspects_config = [(0, 'Conjunction', 0, 10), (60, 'Sextile', 50, 70), (90, 'Square', 80, 100), (120, 'Trine', 110, 130), (180, 'Opposition', 170, 190)]
        planet_list = list(planets.keys())
        aspects = []
        for i, p1 in enumerate(planet_list):
            for p2 in planet_list[i+1:]:
                diff = abs(planets[p1]['longitude'] - planets[p2]['longitude'])
                if diff > 180: diff = 360 - diff
                for asp_angle, asp_name, orb_min, orb_max in aspects_config:
                    if orb_min <= diff <= orb_max:
                        aspects.append({'planet1': p1, 'planet2': p2, 'aspect': asp_name, 'angle': round(diff, 4), 'orb': round(abs(diff - asp_angle), 4)})
                        break
        return aspects

    def calculate_panchanga(self, date: str, time: str, lat: float, lon: float) -> Dict:
        data = self.calculate_planets(date, time, lat, lon)
        sun_lon = data['planets']['Sun']['longitude']
        moon_lon = data['planets']['Moon']['longitude']
        year, month, day = map(int, date.split('-'))
        
        tithi = calculate_tithi(sun_lon, moon_lon)
        nakshatra_idx = calculate_nakshatra(moon_lon)
        yoga_idx = calculate_yoga(sun_lon, moon_lon)
        karana_idx = calculate_karana(sun_lon, moon_lon)
        
        return {'tithi': {'index': tithi, 'name': TITHIS[tithi % 30]},
            'nakshatra': {'index': nakshatra_idx, 'name': NAKSHATRAS[nakshatra_idx % 27]},
            'yoga': {'index': yoga_idx, 'name': YOGAS[yoga_idx % 27]},
            'karana': {'index': karana_idx, 'name': KARANAS[karana_idx % 11 if karana_idx < 10 else karana_idx - 1]},
            'vara': {'index': (day - 1) % 7, 'name': VARAS[day % 7]}}

    def get_raw_data(self) -> Dict:
        return self.last_raw_data

class asurdevAgent:
    def __init__(self):
        self.core = SwissEphemerisCore()
        self.name = "BaseAgent"
        
    def call_swiss_ephemeris(self, **kwargs) -> Dict:
        return self.core.calculate_planets(**kwargs)
        
    def run(self, **kwargs) -> Dict:
        raise NotImplementedError("Subclass must implement run()")
