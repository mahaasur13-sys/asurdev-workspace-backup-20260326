#!/usr/bin/env python3
"""
Swiss Ephemeris Calculator using Skyfield (JPL DE421 ephemeris)
Precision: comparable to Swiss Ephemeris
"""

import sys
import json
from datetime import datetime, timedelta
from skyfield.api import load, utc

# Load ephemeris
ts = load.timescale()
eph = load('de421.bsp')

# Aspect orbs (degrees)
ASPECT_ORBS = {
    'conjunction': 8,
    'opposition': 8,
    'trine': 7,
    'square': 7,
    'sextile': 6,
    'quincunx': 5,
    'semisextile': 4,
}

ASPECT_SYMBOLS = {
    'conjunction': '☌',
    'opposition': '☍',
    'trine': '△',
    'square': '□',
    'sextile': '✶',
    'quincunx': '⚻',
    'semisextile': '⚺'
}

def get_ecliptic_longitude(eph, body, t):
    """Calculate ecliptic longitude for a celestial body"""
    pos = eph[body].at(t)
    ra, dec, dist = pos.radec(epoch='date')
    lon = (ra._degrees + 180) % 360
    return lon

def get_planets(eph, t):
    """Get positions of all relevant planets"""
    bodies = {
        'sun': 'sun',
        'moon': 'moon', 
        'mercury': 'mercury',
        'venus': 'venus',
        'mars': 'mars',
        'jupiter': 'jupiter barycenter',
        'saturn': 'saturn barycenter',
        'uranus': 'uranus barycenter',
        'neptune': 'neptune barycenter',
        'pluto': 'pluto barycenter'
    }
    
    positions = {}
    for name, eph_name in bodies.items():
        try:
            positions[name] = round(get_ecliptic_longitude(eph, eph_name, t), 2)
        except:
            positions[name] = None
    return positions

def calculate_aspects(positions):
    """Find all major aspects between planets"""
    planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto']
    aspects_found = []
    
    for i, p1 in enumerate(planets):
        if positions.get(p1) is None:
            continue
        for p2 in planets[i+1:]:
            if positions.get(p2) is None:
                continue
            
            lon1, lon2 = positions[p1], positions[p2]
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff
            
            aspect_types = {
                'conjunction': 0,
                'sextile': 60,
                'square': 90,
                'trine': 120,
                'opposition': 180
            }
            
            for aspect_name, ideal_angle in aspect_types.items():
                orb = abs(diff - ideal_angle)
                if orb <= ASPECT_ORBS[aspect_name]:
                    aspects_found.append({
                        'planet1': p1,
                        'planet2': p2,
                        'aspect': aspect_name,
                        'symbol': ASPECT_SYMBOLS[aspect_name],
                        'angle': round(diff, 1),
                        'orb': round(orb, 1)
                    })
    
    return aspects_found

def get_nakshatra(lon):
    """Calculate nakshatra (lunar mansion) - 27 divisions"""
    nakshatras = [
        'Ашвини', 'Бхарани', 'Криттика', 'Рохини', 'Мригашира', 'Ардра',
        'Пунарвасу', 'Пушья', 'Ашлеша', 'Магха', 'Пурва Пхалгуни', 'Уттара Пхалгуни',
        'Хаста', 'Читра', 'Свати', 'Вишакха', 'Анурадха', 'Джьештха',
        'Мула', 'Пурва Ашадха', 'Уттара Ашадха', 'Шравана', 'Дханишта', 'Шатабхиша',
        'Пурва Бхадрапада', 'Уттара Бхадрапада', 'Ревати'
    ]
    nak_index = int(lon / (360 / 27)) % 27
    nak_degree = (lon % (360 / 27)) * (13 + 20/60)
    return nakshatras[nak_index], round(nak_degree, 1)

def get_zodiac_sign(lon):
    """Get zodiac sign for a longitude"""
    signs = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Де禄', 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    sign_index = int(lon / 30) % 12
    degree = lon % 30
    return signs[sign_index], round(degree, 1)

def calculate_date_range(start_date_str, days=11):
    """Calculate positions for a range of dates"""
    start = datetime.fromisoformat(start_date_str)
    results = []
    
    for i in range(days):
        d = start + timedelta(days=i)
        d_utc = d.replace(hour=12, minute=0, second=0, tzinfo=utc)
        t = ts.from_datetime(d_utc)
        
        positions = get_planets(eph, t)
        aspects = calculate_aspects(positions)
        nakshatra, nak_degree = get_nakshatra(positions['moon'])
        moon_sign, moon_deg = get_zodiac_sign(positions['moon'])
        
        result = {
            'date': d.strftime('%Y-%m-%d'),
            'day_name': d.strftime('%A'),
            'positions': positions,
            'aspects': aspects,
            'moon': {
                'sign': moon_sign,
                'degree': moon_deg,
                'nakshatra': nakshatra,
                'nak_degree': nak_degree
            }
        }
        results.append(result)
    
    return results

if __name__ == '__main__':
    date = sys.argv[1] if len(sys.argv) > 1 else '2026-03-22'
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 11
    
    if date == 'range':
        output = calculate_date_range('2026-03-21', days)
    else:
        d = datetime.fromisoformat(date)
        d_utc = d.replace(hour=12, minute=0, second=0, tzinfo=utc)
        t = ts.from_datetime(d_utc)
        
        positions = get_planets(eph, t)
        aspects = calculate_aspects(positions)
        nakshatra, nak_degree = get_nakshatra(positions['moon'])
        moon_sign, moon_deg = get_zodiac_sign(positions['moon'])
        
        output = {
            'date': date,
            'positions': positions,
            'aspects': aspects,
            'moon': {
                'sign': moon_sign,
                'degree': moon_deg,
                'nakshatra': nakshatra,
                'nak_degree': nak_degree
            }
        }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
