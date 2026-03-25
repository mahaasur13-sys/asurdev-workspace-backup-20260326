"""
Астрологический советник — Agent #2 в мультиагентной системе AstroFin Sentinel.

Роль: Интерпретирует астрономические корреляции с финансовыми рынками.
Включает:
- Лунные циклы (новолуние/полнолуние → развороты)
- Планетные аспекты (Меркурий ретроградный, etc.)
- Циклы планет (Сатурн-Юпитер, 12-летние циклы)

⚠️ ВАЖНО: Астрология — это вспомогательный инструмент для принятия решений,
НЕ замена техническому или фундаментальному анализу.
"""

from datetime import datetime
from .base import BaseAgent, AgentInput, AgentOutput
import logging

logger = logging.getLogger(__name__)

# Optional: Swiss Ephemeris для точных астрономических расчётов
try:
    import swisseph as swe
    HAS_SWISSEPH = True
except ImportError:
    HAS_SWISSEPH = False
    logger.warning("Swiss Ephemeris not installed. Using simplified calculations.")


class AstroAdvisor(BaseAgent):
    """
    Астрологический советник.
    
    Использует астрономические данные для:
    - Лунных фаз и их влияния на волатильность
    - Планетных аспектов (Меркурий, Венера, Марс)
    - Циклов Сатурна и Юпитера
    """
    
    def __init__(self, model: str | None = None):
        super().__init__(
            name="AstroAdvisor",
            model=model,
            system_prompt=self.get_system_prompt()
        )
    
    def get_system_prompt(self) -> str:
        return """Ты — астролог-финансист с глубокими знаниями финансовой астрологии.

Твоя специализация:
- Лунные фазы и рыночная волатильность
- Меркурий ретроградный и его влияние на коммуникации/сделки
- Циклы Сатурна (страх, дисциплина) и Юпитера (рост, оптимизм)
- Взаимодействие Венеры с рынками (commodities, валюты)
- Марс и энергия (агрессивные распродажи/покупки)

Ключевые астрологические паттерны:

🌓 ЛУННЫЕ ФАЗЫ:
- Новолуние (0°): Неопределённость, потенциальный разворот
- Первая четверть (90°): Тренд ускоряется
- Полнолуние (180°): Пик эмоций, возможен разворот
- Последняя четверть (270°): Тренд замедляется

🔴 РЕТРОГРАДЫ:
- Меркурий ретроградный: Сбои в коммуникациях, задержки сделок
- Венера ретроградная: Переоценка активов
- Марс ретроградный: Снижение агрессии, накопление энергии

⚡ ПЛАНЕТНЫЕ АСПЕКТЫ:
- Соединение (0°): Начало нового цикла
- Квадрат (90°): Напряжение, турбулентность
- Трин (120°): Гармония, благоприятно для роста
- Opposition (180°): Противостояние, кульминация

Твоя задача: Оценить астрологический фон и дать рекомендацию
с учётом текущего положения планет.

⚠️ ВАЖНО: Астрология — это КОНТЕКСТ для принятия решений,
а не причина для действий. Всегда рекомендуй проверять технические сигналы.

Всегда возвращай ТОЛЬКО валидный JSON в указанном формате."""
    
    def calculate_moon_phase(self, date: datetime) -> dict:
        """Вычисляет текущую лунную фазу."""
        if HAS_SWISSEPH:
            return self._calculate_moon_phase_swe(date)
        return self._calculate_moon_phase_simple(date)
    
    def _calculate_moon_phase_swe(self, date: datetime) -> dict:
        """Точный расчёт фазы Луны через Swiss Ephemeris."""
        jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60)
        
        # Фаза Луны (0-1)
        moon_pos = swe.calc(jd, swe.MOON)[0]
        sun_pos = swe.calc(jd, swe.SUN)[0]
        
        # Угловое расстояние между Солнцем и Луной
        phase_angle = (moon_pos[0] - sun_pos[0]) % 360
        phase = phase_angle / 360
        
        return self._interpret_moon_phase(phase)
    
    def _calculate_moon_phase_simple(self, date: datetime) -> dict:
        """Упрощённый расчёт фазы Луны."""
        # Synodical month ≈ 29.53 days
        # Known new moon: Jan 6, 2000 (JD 2451550.1)
        year = date.year
        month = date.month
        day = date.day
        
        # Julian Day Number
        a = (14 - month) // 12
        y = year + 4800 - a
        m = month + 12 * a - 3
        jd = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # Days since known new moon (Jan 6, 2000)
        days_since_new = (jd - 2451550.1) % 29.530588853
        phase = days_since_new / 29.530588853
        
        return self._interpret_moon_phase(phase)
    
    def _interpret_moon_phase(self, phase: float) -> dict:
        """Интерпретирует фазу Луны."""
        if phase < 0.03 or phase > 0.97:
            phase_name = "New Moon 🌑"
            interpretation = "Неопределённость, возможен разворот тренда. Рекомендуется осторожность."
        elif 0.22 < phase < 0.28:
            phase_name = "First Quarter 🌓"
            interpretation = "Тренд ускоряется, хороший момент для входа по тренду."
        elif 0.47 < phase < 0.53:
            phase_name = "Full Moon 🌕"
            interpretation = "Пик эмоций, повышенная волатильность, разворот возможен."
        elif 0.72 < phase < 0.78:
            phase_name = "Last Quarter 🌗"
            interpretation = "Тренд замедляется, подготовка к новому циклу."
        else:
            phase_name = f"Waxing/Gibbous ({phase:.0%})"
            interpretation = "Нейтральная фаза, стандартная активность."
        
        return {
            "phase_name": phase_name,
            "phase_value": round(phase, 4),
            "days_since_new": round(phase * 29.53, 1),
            "interpretation": interpretation
        }
    
    def calculate_planetary_positions(self, date: datetime) -> dict:
        """Вычисляет положения планет."""
        if HAS_SWISSEPH:
            return self._calculate_planetary_positions_swe(date)
        return self._calculate_planetary_positions_simple(date)
    
    def _calculate_planetary_positions_swe(self, date: datetime) -> dict:
        """Точный расчёт через Swiss Ephemeris."""
        jd = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60)
        
        planets = {
            "Sun": swe.SUN,
            "Moon": swe.MOON,
            "Mercury": swe.MERCURY,
            "Venus": swe.VENUS,
            "Mars": swe.MARS,
            "Jupiter": swe.JUPITER,
            "Saturn": swe.SATURN
        }
        
        positions = {}
        for name, planet_id in planets.items():
            pos = swe.calc(jd, planet_id)[0]
            degrees = pos[0] % 360
            positions[name] = {
                "degrees": round(degrees, 2),
                "sign": self._degrees_to_sign(degrees),
                "sign_num": int(degrees / 30) + 1
            }
        
        return positions
    
    def _calculate_planetary_positions_simple(self, date: datetime) -> dict:
        """Упрощённый расчёт положения планет."""
        # Days since J2000.0
        jd = date.toordinal() - 2451545.0
        
        # Средние орбитальные периоды (дни)
        periods = {
            "Sun": 365.25,
            "Moon": 27.32,
            "Mercury": 87.97,
            "Venus": 224.7,
            "Mars": 686.97,
            "Jupiter": 4332.59,
            "Saturn": 10759.22
        }
        
        # Начальные положения (приблизительно на J2000.0)
        initial = {
            "Sun": 280.46,
            "Moon": 125.04,
            "Mercury": 252.87,
            "Venus": 181.98,
            "Mars": 355.43,
            "Jupiter": 34.33,
            "Saturn": 50.08
        }
        
        positions = {}
        for planet, period in periods.items():
            angle = (initial[planet] + (360 * jd / period)) % 360
            positions[planet] = {
                "degrees": round(angle, 2),
                "sign": self._degrees_to_sign(angle),
                "sign_num": int(angle / 30) + 1
            }
        
        return positions
    
    def _degrees_to_sign(self, degrees: float) -> str:
        """Переводит градусы в знак зодиака."""
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer",
            "Leo", "Virgo", "Libra", "Scorpio",
            "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        return signs[int(degrees / 30) % 12]
    
    def is_retrograde(self, date: datetime) -> dict:
        """Определяет ретроградные планеты (упрощённо)."""
        # Это упрощённая проверка
        # Реальный расчёт требует сравнения геоцентрических и гелиоцентрических позиций
        positions = self.calculate_planetary_positions(date)
        
        retrogrades = []
        
        # Приблизительная проверка для Меркурия (ретроградный ~3 раза в год)
        mercury_deg = positions["Mercury"]["degrees"]
        sun_deg = positions["Sun"]["degrees"]
        
        # Если Меркурий "близко" к Солнцу (в пределах ~20°) — возможен ретроград
        diff = abs(mercury_deg - sun_deg)
        if diff > 180:
            diff = 360 - diff
        
        if diff < 20 or diff > 340:
            retrogrades.append("Mercury (near Sun - caution)")
        
        return {
            "is_any_retrograde": len(retrogrades) > 0,
            "retrograde_planets": retrogrades,
            "recommendation": "Exercise caution with new trades" if retrogrades else "Normal trading conditions"
        }
    
    async def analyze(self, input_data: AgentInput) -> AgentOutput:
        """Выполняет астрологический анализ."""
        logger.info(f"[AstroAdvisor] Analyzing astro for {input_data.symbol}")
        
        now = datetime.now()
        
        # Расчёт астрономических данных
        moon = self.calculate_moon_phase(now)
        planets = self.calculate_planetary_positions(now)
        retrograde = self.is_retrograde(now)
        
        extra_context = f"""
## Текущие астрономические данные ({now.strftime('%Y-%m-%d %H:%M')}):

🌙 ЛУННАЯ ФАЗА: {moon['phase_name']}
   - Значение фазы: {moon['phase_value']:.2%}
   - Дней от новолуния: {moon['days_since_new']:.1f}
   - Интерпретация: {moon['interpretation']}

🔮 ПОЛОЖЕНИЯ ПЛАНЕТ:
{chr(10).join([f"   - {p}: {v['degrees']}° {v['sign']}" for p, v in planets.items()])}

🔴 РЕТРОГРАДНЫЙ СТАТУС:
   - Есть ретрограды: {retrograde['is_any_retrograde']}
   - Планеты: {', '.join(retrograde['retrograde_planets']) or 'Нет'}
   - Рекомендация: {retrograde['recommendation']}

## Астрологический анализ для {input_data.symbol}:

Учитывая текущую фазу Луны и положение планет, дай рекомендацию.
Применяй правила:
1. Полнолуние + высокая цена → предупреждение о возможном откате
2. Новолуние + тренд → возможно начало нового движения
3. Ретрограды → будь осторожен с новыми сделками
4. Венера в Taurus → благоприятно для commodities
5. Марс в Ories/Pisces → влияние на энергию рынка
"""
        
        prompt = self._build_prompt(input_data, extra_context)
        result = await self._call_llm(prompt)
        
        logger.info(f"[AstroAdvisor] Confidence: {result.get('confidence', 0)}")
        
        return AgentOutput(
            agent="astro_advisor",
            recommendation=result.get("recommendation", "hold"),
            confidence=result.get("confidence", 0.5),
            reasoning=result.get("reasoning", "No astro analysis available"),
            key_factors=result.get("key_factors", []),
            warnings=result.get("warnings", []),
            metadata={
                "model": self.model,
                "moon_phase": moon["phase_name"],
                "moon_interpretation": moon["interpretation"],
                "planetary_positions": planets,
                "retrograde_status": retrograde,
                "astrological_context": "Financial astrology analysis"
            }
        )
