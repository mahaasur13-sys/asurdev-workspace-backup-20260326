"""
Zodiac Wheel Visualization
===========================
Создаёт натальную карту (зодиакальное колесо) с планетами, знаками и домами.

Зависимости:
    pip install matplotlib numpy

Использование:
    from visualizations import ZodiacWheel

    wheel = ZodiacWheel()
    img_bytes = wheel.draw(
        positions={
            'Sun': {'sign': 0, 'degree': 15},      # Овен 15°
            'Moon': {'sign': 3, 'degree': 22},      # Рак 22°
            'Mars': {'sign': 5, 'degree': 10},      # Дева 10°
        },
        houses={1: 0, 2: 25, 3: 45, ...},  # Кухпи домов (от Асцендента)
        aspects=[
            {'planet1': 'Sun', 'planet2': 'Moon', 'type': 'Trine', 'orb': 7},
            {'planet1': 'Sun', 'planet2': 'Mars', 'type': 'Square', 'orb': 5},
        ]
    )
"""

import io
import math
from typing import Optional

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import Wedge, Circle, Arc
    import matplotlib.lines as mlines
except ImportError:
    raise ImportError("matplotlib required: pip install matplotlib")

# Знаки зодиака
ZODIAC_SIGNS = [
    'Aries', 'Taurus', 'Gemini', 'Cancer',
    'Leo', 'Virgo', 'Libra', 'Scorpio',
    'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
]

# Русские названия
ZODIAC_SIGNS_RU = [
    'Овен', 'Телец', 'Близнецы', 'Рак',
    'Лев', 'Дева', 'Весы', 'Скорпион',
    'Стрелец', 'Козерог', 'Водолей', 'Рыбы'
]

# Символы знаков (юникод)
ZODIAC_SYMBOLS = [
    '♈', '♉', '♊', '♋',
    '♌', '♍', '♎', '♏',
    '♐', '♑', '♒', '♓'
]

# Цвета планет
PLANET_COLORS = {
    'Sun': '#FFD700',      # Золото
    'Moon': '#C0C0C0',     # Серебро
    'Mercury': '#00BFFF',  # Голубой
    'Venus': '#FF69B4',    # Розовый
    'Mars': '#FF4500',     # Красно-оранжевый
    'Jupiter': '#DAA520',  # Золотисто-коричневый
    'Saturn': '#8B4513',   # Коричневый
    'Uranus': '#40E0D0',   # Бирюзовый
    'Neptune': '#4169E1',  # Синий
    'Pluto': '#800080',    # Фиолетовый
    'North Node': '#000000',  # Чёрный (Кету)
    'South Node': '#808080',  # Серый (Раху)
}

# Аспекты и их цвета
ASPECT_COLORS = {
    'Conjunction': '#FFD700',  # Соединение - золото
    'Sextile': '#00CED1',      # Секстиль - бирюза
    'Square': '#FF4500',       # Квадрат - красный
    'Trine': '#32CD32',        # Трин - зелёный
    'Opposition': '#FF1493',   # Оппонирование - розовый
}

# Символы аспектов
ASPECT_SYMBOLS = {
    'Conjunction': '☌',
    'Sextile': '⚹',
    'Square': '□',
    'Trine': '△',
    'Opposition': '☍',
}


class ZodiacWheel:
    """
    Класс для рисования зодиакального колеса (натальной карты).
    
    Параметры:
        figsize (tuple): Размер фигуры (по умолчанию 12x12)
        style (str): Стиль ('modern', 'classic', 'astroprint')
        show_aspects (bool): Показывать аспекты между планетами
        show_houses (bool): Показывать дома
        sign_names (str): Язык названий знаков ('en', 'ru', 'symbols')
    """
    
    def __init__(
        self,
        figsize: tuple = (12, 12),
        style: str = 'modern',
        show_aspects: bool = True,
        show_houses: bool = True,
        sign_names: str = 'ru'
    ):
        self.figsize = figsize
        self.style = style
        self.show_aspects = show_aspects
        self.show_houses = show_houses
        self.sign_names = sign_names
        
        # Настройка стиля
        self._setup_style()
    
    def _setup_style(self):
        """Настраивает цвета и стили в зависимости от выбранного режима."""
        if self.style == 'modern':
            self.bg_color = '#1a1a2e'
            self.sign_color = '#e0e0e0'
            self.line_color = '#404060'
            self.house_color = '#606080'
        elif self.style == 'classic':
            self.bg_color = '#f5f5dc'
            self.sign_color = '#333333'
            self.line_color = '#8b4513'
            self.house_color = '#a0522d'
        elif self.style == 'astroprint':
            self.bg_color = '#0d0d0d'
            self.sign_color = '#ffffff'
            self.line_color = '#666666'
            self.house_color = '#888888'
        else:
            self.bg_color = '#1a1a2e'
            self.sign_color = '#e0e0e0'
            self.line_color = '#404060'
            self.house_color = '#606080'
    
    def _get_sign_name(self, sign_index: int) -> str:
        """Возвращает название знака в зависимости от настройки."""
        if self.sign_names == 'en':
            return ZODIAC_SIGNS[sign_index]
        elif self.sign_names == 'ru':
            return ZODIAC_SIGNS_RU[sign_index]
        elif self.sign_names == 'symbols':
            return ZODIAC_SYMBOLS[sign_index]
        else:
            return ZODIAC_SIGNS[sign_index]
    
    def _degree_to_rad(self, degree: float) -> float:
        """Конвертирует градусы в радианы (отсчёт от севера, по часовой)."""
        # 0° = Север (верх), отсчёт по часовой стрелке
        return math.radians(90 - degree)
    
    def _sign_start_degree(self, sign_index: int) -> float:
        """Возвращает начальный градус знака зодиака."""
        return sign_index * 30
    
    def draw(
        self,
        positions: dict,
        houses: Optional[dict] = None,
        aspects: Optional[list] = None,
        title: Optional[str] = None
    ) -> bytes:
        """
        Рисует зодиакальное колесо и возвращает как PNG bytes.
        
        Args:
            positions: Словарь позиций планет {
                'Sun': {'sign': 0, 'degree': 15},  # Овен 15°
                'Moon': {'sign': 3, 'degree': 22},
                ...
            }
            houses: Словарь домов {1: 0, 2: 25, ...} (градусы от Асцендента)
            aspects: Список аспектов [
                {'planet1': 'Sun', 'planet2': 'Moon', 'type': 'Trine', 'orb': 7},
                ...
            ]
            title: Заголовок графика
            
        Returns:
            bytes: PNG изображение колеса
        """
        fig, ax = plt.subplots(figsize=self.figsize, subplot_kw={'projection': 'polar'})
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)  # По часовой стрелке
        
        # Фон
        ax.set_facecolor(self.bg_color)
        fig.patch.set_facecolor(self.bg_color)
        
        # Отключаем стандартные деления
        ax.set_yticklabels([])
        ax.set_xticklabels([])
        ax.spines['polar'].set_visible(False)
        ax.grid(False)
        
        # Рисуем сегменты знаков зодиака
        self._draw_signs(ax)
        
        # Рисуем дома
        if self.show_houses and houses:
            self._draw_houses(ax, houses)
        
        # Рисуем аспекты
        if self.show_aspects and aspects:
            self._draw_aspects(ax, positions, aspects)
        
        # Рисуем планеты
        self._draw_planets(ax, positions)
        
        # Заголовок
        if title:
            plt.title(title, color=self.sign_color, fontsize=14, pad=20)
        
        # Убираем поля
        plt.tight_layout()
        
        # Сохраняем в bytes
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight',
                   facecolor=self.bg_color, edgecolor='none')
        buf.seek(0)
        img_bytes = buf.read()
        plt.close(fig)
        
        return img_bytes
    
    def _draw_signs(self, ax):
        """Рисует 12 сегментов знаков зодиака."""
        for i in range(12):
            start_rad = self._degree_to_rad(self._sign_start_degree(i))
            end_rad = self._degree_to_rad(self._sign_start_degree(i + 1))
            
            # Цвета чередуются
            if i % 2 == 0:
                color = self.bg_color
            else:
                color = '#2a2a4e'
            
            # Рисуем сегмент
            wedge = Wedge((0, 0), 1.0, 
                         math.degrees(start_rad), 
                         math.degrees(end_rad),
                         width=0.15, facecolor=color, 
                         edgecolor=self.line_color, linewidth=0.5)
            ax.add_patch(wedge)
            
            # Подписываем знак на внешнем краю
            mid_rad = (start_rad + end_rad) / 2
            mid_deg = 90 - math.degrees(mid_rad)
            sign_index = int(mid_deg / 30) % 12
            
            ax.text(mid_rad, 0.88, self._get_sign_name(sign_index),
                   ha='center', va='center', fontsize=9,
                   color=self.sign_color, fontweight='bold',
                   rotation=mid_deg - 90)
            
            # Символ на внутреннем краю
            ax.text(mid_rad, 0.62, ZODIAC_SYMBOLS[sign_index],
                   ha='center', va='center', fontsize=12,
                   color=self.sign_color)
    
    def _draw_houses(self, ax, houses: dict):
        """Рисует дома (куспиды домов)."""
        # Рисуем радиальные линии домов
        for house_num, degree in houses.items():
            rad = self._degree_to_rad(degree)
            ax.plot([rad, rad], [0.15, 0.85], 
                   color=self.house_color, linewidth=1, alpha=0.7)
            
            # Номер дома на внешнем краю
            ax.text(rad, 0.92, str(house_num),
                   ha='center', va='center', fontsize=7,
                   color=self.house_color, fontweight='bold')
    
    def _draw_planets(self, ax, positions: dict):
        """Рисует планеты на колесе."""
        planet_symbols = {
            'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀',
            'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '⛢',
            'Neptune': '♆', 'Pluto': '♇', 'North Node': '☊', 'South Node': '☋'
        }
        
        for planet, data in positions.items():
            sign_index = data.get('sign', 0)
            degree = data.get('degree', 0)
            
            # Позиция на колесе
            total_deg = sign_index * 30 + degree
            rad = self._degree_to_rad(total_deg)
            
            # Планета на орбисе (0.5-0.7 от центра)
            orbit = 0.65
            color = PLANET_COLORS.get(planet, '#ffffff')
            
            # Рисуем круг планеты
            circle = Circle((math.cos(rad) * orbit, math.sin(rad) * orbit),
                           0.03, color=color, zorder=10)
            ax.add_patch(circle)
            
            # Символ планеты внутри
            symbol = planet_symbols.get(planet, '✦')
            ax.text(math.cos(rad) * orbit, math.sin(rad) * orbit,
                   symbol, ha='center', va='center', fontsize=8,
                   color=self.bg_color, fontweight='bold', zorder=11)
            
            # Название планеты снаружи
            ax.text(math.cos(rad) * (orbit + 0.08), math.sin(rad) * (orbit + 0.08),
                   planet[:3], ha='center', va='center', fontsize=6,
                   color=color, zorder=11)
    
    def _draw_aspects(self, ax, positions: dict, aspects: list):
        """Рисует аспекты (линии между планетами)."""
        for aspect in aspects:
            p1 = aspect.get('planet1')
            p2 = aspect.get('planet2')
            aspect_type = aspect.get('type', 'Conjunction')
            orb = aspect.get('orb', 0)
            
            if p1 not in positions or p2 not in positions:
                continue
            
            # Получаем координаты планет
            def get_planet_pos(name):
                data = positions[name]
                sign_index = data.get('sign', 0)
                degree = data.get('degree', 0)
                total_deg = sign_index * 30 + degree
                rad = self._degree_to_rad(total_deg)
                orbit = 0.65
                return (math.cos(rad) * orbit, math.sin(rad) * orbit)
            
            pos1 = get_planet_pos(p1)
            pos2 = get_planet_pos(p2)
            
            # Цвет линии аспекта
            color = ASPECT_COLORS.get(aspect_type, '#888888')
            linewidth = 1.5 if orb < 3 else 1.0
            alpha = 1.0 if orb < 2 else 0.7
            
            # Рисуем линию
            ax.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]],
                   color=color, linewidth=linewidth, alpha=alpha,
                   linestyle='-' if aspect_type in ['Conjunction', 'Trine', 'Sextile'] else '--',
                   zorder=5)
    
    def save(self, filepath: str, **kwargs) -> None:
        """Сохраняет колесо в файл."""
        img_bytes = self.draw(**kwargs)
        with open(filepath, 'wb') as f:
            f.write(img_bytes)


def create_wheel_image(
    positions: dict,
    houses: Optional[dict] = None,
    aspects: Optional[list] = None,
    style: str = 'modern'
) -> bytes:
    """
    Удобная функция для быстрого создания колеса.
    
    Example:
        >>> positions = {
        ...     'Sun': {'sign': 0, 'degree': 15},
        ...     'Moon': {'sign': 3, 'degree': 22},
        ... }
        >>> img = create_wheel_image(positions, style='astroprint')
        >>> with open('wheel.png', 'wb') as f:
        ...     f.write(img)
    """
    wheel = ZodiacWheel(style=style)
    return wheel.draw(positions, houses, aspects)
