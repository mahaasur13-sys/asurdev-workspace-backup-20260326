#!/usr/bin/env python3
"""asurdev Sentinel — Multi-Agent System (Swiss Ephemeris Only)"""
from core import SwissEphemerisCore, asurdevAgent

class PlanetaryCalculatorAgent(asurdevAgent):
    def __init__(self):
        super().__init__()
        self.name = "PlanetaryCalculator"
        
    def run(self, date: str, time: str, lat: float, lon: float) -> dict:
        planets = self.call_swiss_ephemeris(date=date, time=time, lat=lat, lon=lon)
        houses = self.core.calculate_houses(date, time, lat, lon)
        aspects = self.core.calculate_aspects(planets['planets'])
        return {'agent': self.name, 'source': 'Swiss Ephemeris 2.10.03', 'raw_planets': planets, 'houses': houses, 'aspects': aspects}

class PanchangaAgent(asurdevAgent):
    def __init__(self):
        super().__init__()
        self.name = "Panchanga"
        
    def run(self, date: str, time: str, lat: float, lon: float) -> dict:
        self.call_swiss_ephemeris(date=date, time=time, lat=lat, lon=lon)
        panchang = self.core.calculate_panchanga(date, time, lat, lon)
        return {'agent': self.name, 'source': 'Swiss Ephemeris 2.10.03', 'panchang': panchang}

class MuhurtaAgent(asurdevAgent):
    def __init__(self):
        super().__init__()
        self.name = "Muhurta"
        self.choghadiya = [('Amrita', 'Бесплатные подарки, лекарства', 'Благоприятно'),
            ('Shubha', 'Свадьба, образование, творчество', 'Хорошо'),
            ('Labha', 'Финансы, инвестиции', 'Выгодно'),
            ('Shubh', 'Деловые начинания, путешествия', 'Хорошо'),
            ('Rog', 'Лечение', 'Избегать'),
            ('Kala', 'Серьёзные решения', 'Неблагоприятно'),
            ('Udveg', 'Контракты, переговоры', 'Рискованно')]
        
    def run(self, date: str, time: str, lat: float, lon: float) -> dict:
        self.call_swiss_ephemeris(date=date, time=time, lat=lat, lon=lon)
        panchang = self.core.calculate_panchanga(date, time, lat, lon)
        idx = panchang['tithi']['index'] % 7
        chogh = self.choghadiya[idx]
        return {'agent': self.name, 'source': 'Swiss Ephemeris 2.10.03', 'panchang': panchang, 
                'choghadiya_today': {'type': chogh[0], 'description': chogh[1], 'verdict': chogh[2]}}

class AstrologerAgent(asurdevAgent):
    def __init__(self):
        super().__init__()
        self.name = "Astrologer"
        self.sign_themes = {
            'Aries': 'Начало, действие, энергия', 'Taurus': 'Финансы, стабильность, ресурсы',
            'Gemini': 'Коммуникация, данные, анализ', 'Cancer': 'Эмоции, дом, семья',
            'Leo': 'Творчество, лидерство, гордость', 'Virgo': 'Работа, здоровье, детали',
            'Libra': 'Партнёрства, баланс, справедливость', 'Scorpio': 'Трансформация, глубина, секреты',
            'Sagittarius': 'Расширение, путешествия, философия', 'Capricorn': 'Структура, карьера, амбиции',
            'Aquarius': 'Инновации, сообщество, технологии', 'Pisces': 'Духовность, интуиция, мечты'}
        
    def interpret(self, planetary_data: dict, panchang_data: dict) -> dict:
        planets = planetary_data['raw_planets']['planets']
        moon = planets['Moon']
        return {'agent': self.name, 'interpretation': {
            'moon_sign': moon['sign'], 'moon_nakshatra': moon['nakshatra'],
            'moon_degree': moon['degree_in_sign'], 'theme': self.sign_themes.get(moon['sign'], 'Unknown'),
            'advice': f"Луна в {moon['sign']} ({moon['nakshatra']}) — {self.sign_themes.get(moon['sign'], '')}"}}

class SynthesizerAgent(asurdevAgent):
    def __init__(self):
        super().__init__()
        self.name = "Synthesizer"
        self.nakshatra_actions = {
            'Ashwini': 'Быстрые действия, старт проектов', 'Rohini': 'Долгосрочное планирование, инвестиции',
            'Mrigashira': 'Исследование, поиск возможностей', 'Pushya': 'Ритуалы, образование, духовные практики',
            'Hasta': 'Творчество, ремёсла, медитация', 'Swati': 'Торговля, обмен, гибкость',
            'Anuradha': 'Партнёрства, сотрудничество', 'Jyeshtha': 'Трансформация, избавление от старого',
            'Mula': 'Глубинные исследования, корневая работа', 'Purva Ashadha': 'Честь, победа',
            'Uttara Ashadha': 'Справедливость, дхарма', 'Shravana': 'Обучение, слушание',
            'Dhanishtha': 'Изобилие, богатство', 'Shatabhisha': 'Целительство, тайные знания',
            'Purva Bhadrapada': 'Инициация, сила воли', 'Uttara Bhadrapada': 'Энергия, трансформация',
            'Revati': 'Путешествия, защита'}
        
    def synthesize(self, planetary_data: dict, panchang_data: dict, interpretation: dict) -> dict:
        planets = planetary_data['raw_planets']['planets']
        moon = planets['Moon']
        aspects = planetary_data['aspects']
        moon_aspects = [a for a in aspects if a['planet1'] == 'Moon' or a['planet2'] == 'Moon']
        nakshatra = panchang_data['panchang']['nakshatra']['name']
        is_difficult_day = any(a['aspect'] in ['Square', 'Opposition'] for a in moon_aspects)
        tithi_name = panchang_data['panchang']['tithi']['name']
        avoid = 'Важных решений, операций' if 'Chaturdashi' in tithi_name or 'Trayodashi' in tithi_name else 'Импульсивных действий'
        return {'agent': self.name, 'final_recommendation': {
            'mood': '⚠️ Аналитический период — требуется осторожность' if is_difficult_day else '✨ Продуктивный период — действуйте',
            'key_focus': nakshatra, 
            'action': self.nakshatra_actions.get(nakshatra, 'Общие благоприятные дела'),
            'avoid': avoid}}
