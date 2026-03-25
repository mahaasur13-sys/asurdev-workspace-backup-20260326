"""
Astro Overlay Visualization
===========================
Накладывает астрологические события на финансовые графики.

Типы событий:
- Лунные фазы (New Moon, Full Moon, etc.)
- Планетарные аспекты (Mars Square Saturn, etc.)
- Планетарные движения (Mercury Rx, Venus Entering, etc.)
- Развороты дирекций (Jupiter Direct, etc.)

Зависимости:
    pip install plotly pandas kaleido

Использование:
    from visualizations import AstroOverlay

    overlay = AstroOverlay()
    
    # Определяем события
    events = [
        {'date': '2026-03-22', 'type': 'New Moon', 'planet': 'Moon', 'sign': 'Aries'},
        {'date': '2026-03-25', 'type': 'Square', 'planet1': 'Mars', 'planet2': 'Saturn', 'orb': 1},
        {'date': '2026-03-28', 'type': 'Full Moon', 'planet': 'Libra'},
    ]
    
    # Добавляем на график
    fig = overlay.add_to_figure(
        base_fig,  # plotly Figure
        events,
        x_range=[dates[0], dates[-1]]
    )
"""

from typing import Optional, Literal
from dataclasses import dataclass
from datetime import datetime

try:
    import plotly.graph_objects as go
except ImportError:
    raise ImportError("plotly required: pip install plotly")


# Символы планет
PLANET_SYMBOLS = {
    'Sun': '☉', 'Moon': '☽', 'Mercury': '☿', 'Venus': '♀',
    'Mars': '♂', 'Jupiter': '♃', 'Saturn': '♄', 'Uranus': '⛢',
    'Neptune': '♆', 'Pluto': '♇', 'North Node': '☊', 'South Node': '☋'
}

# Цвета событий
EVENT_COLORS = {
    'New Moon': '#2C3E50',       # Тёмно-синий
    'Full Moon': '#F1C40F',      # Золотой
    'First Quarter': '#E67E22',  # Оранжевый
    'Last Quarter': '#9B59B6',   # Фиолетовый
    'Waxing': '#27AE60',         # Зелёный (растущая)
    'Waning': '#E74C3C',         # Красный (убывающая)
    'Mars': '#E74C3C',           # Красный
    'Venus': '#E91E63',          # Розовый
    'Jupiter': '#3498DB',        # Синий
    'Saturn': '#95A5A6',         # Серый
    'Mercury': '#00BCD4',        # Голубой
    'Retrograde': '#9C27B0',     # Фиолетовый
    'Direct': '#4CAF50',         # Зелёный
    'Entering': '#FF9800',       # Оранжевый
    'Aspect': '#7B68EE',         # Серо-синий
}

# Русские названия фаз Луны
MOON_PHASE_RU = {
    'New Moon': 'Новолуние',
    'Waxing Crescent': 'Молодая Луна',
    'First Quarter': 'Первая четверть',
    'Waxing Gibbous': 'Прибывающая Луна',
    'Full Moon': 'Полнолуние',
    'Waning Gibbous': 'Убывающая Луна',
    'Last Quarter': 'Последняя четверть',
    'Waning Crescent': 'Старая Луна',
}


@dataclass
class AstroEvent:
    """Астрологическое событие."""
    date: str
    event_type: str  # 'moon_phase', 'aspect', 'planet_move', 'station'
    planet: Optional[str] = None
    planet2: Optional[str] = None
    sign: Optional[str] = None
    aspect_type: Optional[str] = None
    orb: float = 0.0
    description: str = ""
    
    @property
    def color(self) -> str:
        """Возвращает цвет события."""
        if self.event_type == 'moon_phase':
            return EVENT_COLORS.get(self.event_type.replace(' ', ''), '#888888')
        elif self.planet:
            return EVENT_COLORS.get(self.planet, '#888888')
        return '#888888'
    
    @property
    def symbol(self) -> str:
        """Возвращает символ события."""
        if self.event_type == 'moon_phase':
            symbols = {
                'New Moon': '🌑', 'Waxing Crescent': '🌒',
                'First Quarter': '🌓', 'Waxing Gibbous': '🌔',
                'Full Moon': '🌕', 'Waning Gibbous': '🌖',
                'Last Quarter': '🌗', 'Waning Crescent': '🌘',
            }
            return symbols.get(self.event_type, '☾')
        elif self.planet:
            return PLANET_SYMBOLS.get(self.planet, '✦')
        return '✦'
    
    @property
    def label(self) -> str:
        """Краткая метка для графика."""
        if self.event_type == 'moon_phase':
            return f"{self.symbol} {self.event_type}"
        elif self.event_type == 'aspect':
            p1 = PLANET_SYMBOLS.get(self.planet, self.planet[:3]) if self.planet else ''
            p2 = PLANET_SYMBOLS.get(self.planet2, self.planet2[:3]) if self.planet2 else ''
            return f"{p1}-{p2} {self.aspect_type}"
        elif self.event_type == 'planet_move':
            return f"{self.symbol} {self.planet} {self.sign}"
        elif self.event_type == 'station':
            direction = 'R' if 'Retrograde' in self.description else 'D'
            return f"{self.symbol} {self.planet} {direction}"
        return f"{self.symbol} {self.event_type}"


class AstroOverlay:
    """
    Класс для добавления астрологических меток на финансовые графики.
    
    Usage:
        overlay = AstroOverlay()
        fig = overlay.add_to_figure(base_figure, events)
    """
    
    def __init__(
        self,
        show_labels: bool = True,
        label_position: Literal['top', 'bottom', 'auto'] = 'auto',
        show_legend: bool = True,
        moon_phases_opacity: float = 0.15,
        aspect_line_style: str = 'dash'
    ):
        self.show_labels = show_labels
        self.label_position = label_position
        self.show_legend = show_legend
        self.moon_phases_opacity = moon_phases_opacity
        self.aspect_line_style = aspect_line_style
    
    def add_to_figure(
        self,
        fig: go.Figure,
        events: list,
        x_range: Optional[tuple] = None,
        price_range: Optional[tuple] = None
    ) -> go.Figure:
        """
        Добавляет астрологические события на график.
        
        Args:
            fig: Базовая plotly Figure
            events: Список событий в формате dict или AstroEvent
            x_range: Диапазон дат (start, end) для определения позиции меток
            price_range: Диапазон цен для позиционирования (y_min, y_max)
            
        Returns:
            Обновлённая Figure
        """
        # Определяем ценовой диапазон если не задан
        if price_range is None:
            price_range = self._get_price_range(fig)
        
        y_min, y_max = price_range
        
        # Разделяем события по типам
        moon_events = []
        aspect_events = []
        planet_events = []
        
        for event_data in events:
            if isinstance(event_data, dict):
                event = self._parse_event_dict(event_data)
            else:
                event = event_data
            
            if event.event_type == 'moon_phase':
                moon_events.append(event)
            elif event.event_type == 'aspect':
                aspect_events.append(event)
            else:
                planet_events.append(event)
        
        # Добавляем слои
        for event in moon_events:
            fig = self._add_moon_phase(fig, event, x_range, y_min, y_max)
        
        for event in aspect_events:
            fig = self._add_aspect_line(fig, event, y_min, y_max)
        
        for event in planet_events:
            fig = self._add_planet_marker(fig, event, y_min, y_max)
        
        # Обновляем легенду
        if self.show_legend:
            fig = self._update_legend(fig)
        
        return fig
    
    def _parse_event_dict(self, data: dict) -> AstroEvent:
        """Парсит словарь в AstroEvent."""
        event_type = data.get('type', '')
        
        if 'Moon' in event_type or 'moon' in data:
            return AstroEvent(
                date=data['date'],
                event_type='moon_phase',
                description=event_type
            )
        elif 'Square' in event_type or 'Trine' in event_type or 'Conjunction' in event_type:
            return AstroEvent(
                date=data['date'],
                event_type='aspect',
                planet=data.get('planet1'),
                planet2=data.get('planet2'),
                aspect_type=event_type,
                orb=data.get('orb', 0)
            )
        else:
            return AstroEvent(
                date=data['date'],
                event_type=data.get('event_type', 'planet_move'),
                planet=data.get('planet'),
                sign=data.get('sign'),
                description=event_type
            )
    
    def _get_price_range(self, fig: go.Figure) -> tuple:
        """Получает ценовой диапазон из графика."""
        y_min = float('inf')
        y_max = float('-inf')
        
        for trace in fig.data:
            if hasattr(trace, 'y') and trace.y is not None:
                y_vals = [y for y in trace.y if y is not None and not isinstance(y, str)]
                if y_vals:
                    y_min = min(y_min, min(y_vals))
                    y_max = max(y_max, max(y_vals))
        
        if y_min == float('inf'):
            y_min, y_max = 0, 100
        
        # Добавляем отступ
        padding = (y_max - y_min) * 0.1
        return y_min - padding, y_max + padding
    
    def _add_moon_phase(
        self,
        fig: go.Figure,
        event: AstroEvent,
        x_range: Optional[tuple],
        y_min: float,
        y_max: float
    ) -> go.Figure:
        """Добавляет метку лунной фазы (вертикальный прямоугольник)."""
        color = event.color
        
        # Определяем прозрачность
        opacity = self.moon_phases_opacity
        
        # Конвертируем строку в datetime если нужно
        event_date = event.date
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, '%Y-%m-%d')
        
        # Для vrect нужен x1 отличный от x0, используем add_shape
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        
        # Добавляем вертикальный прямоугольник через shape
        fig.add_shape(
            type="rect",
            x0=event_date,
            x1=event_date,
            y0=0,
            y1=1,
            yref="paper",  # относительно всей высоты
            fillcolor=color,
            opacity=opacity,
            layer="below",
            line=dict(width=2, color=color)
        )
        
        # Добавляем annotation для символа
        fig.add_annotation(
            x=event_date,
            y=1.02,
            yref="paper",
            text=event.symbol,
            showarrow=False,
            font=dict(size=16, color=color),
            textangle=0,
            xanchor="center",
            yanchor="bottom"
        )
        
        return fig
    
    def _add_aspect_line(
        self,
        fig: go.Figure,
        event: AstroEvent,
        y_min: float,
        y_max: float
    ) -> go.Figure:
        """Добавляет линию аспекта."""
        # Конвертируем строку в datetime если нужно
        event_date = event.date
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, '%Y-%m-%d')
        
        # Цвет зависит от типа аспекта
        aspect_colors = {
            'Conjunction': '#FFD700',
            'Sextile': '#00CED1',
            'Square': '#FF4500',
            'Trine': '#32CD32',
            'Opposition': '#FF1493',
        }
        color = aspect_colors.get(event.aspect_type, '#888888')
        
        # Стиль линии
        dash = 'dash' if event.aspect_type in ['Square', 'Opposition'] else 'dot'
        
        # Используем add_shape вместо add_vline для надёжности
        fig.add_shape(
            type="line",
            x0=event_date,
            x1=event_date,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(
                color=color,
                width=1.5,
                dash=dash
            )
        )
        
        # Добавляем annotation
        fig.add_annotation(
            x=event_date,
            y=1.02,
            yref="paper",
            text=event.label,
            showarrow=False,
            font=dict(size=9, color=color),
            textangle=-45,
            xanchor="left",
            bgcolor='rgba(0,0,0,0.7)',
            borderpad=2
        )
        
        return fig
    
    def _add_planet_marker(
        self,
        fig: go.Figure,
        event: AstroEvent,
        y_min: float,
        y_max: float
    ) -> go.Figure:
        """Добавляет маркер планетного события."""
        # Конвертируем строку в datetime если нужно
        event_date = event.date
        if isinstance(event_date, str):
            event_date = datetime.strptime(event_date, '%Y-%m-%d')
        
        color = event.color
        y_pos = y_max - (y_max - y_min) * 0.05  # 5% от верха
        
        # Добавляем annotation
        fig.add_annotation(
            x=event_date,
            y=y_pos,
            text=event.label,
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=1,
            arrowcolor=color,
            ax=0,
            ay=-30,
            font=dict(
                size=10,
                color=color
            ),
            bgcolor='rgba(0,0,0,0.8)',
            bordercolor=color,
            borderwidth=1,
            borderpad=3,
            name=f"Planet: {event.planet}"
        )
        
        return fig
    
    def _update_legend(self, fig: go.Figure) -> go.Figure:
        """Обновляет легенду графика."""
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.15,
                xanchor='right',
                x=1,
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='#444',
                borderwidth=1
            )
        )
        return fig
    
    def create_legend_items(self) -> list:
        """Создаёт элементы легенды для астрологических событий."""
        items = [
            {'name': '🌕 Full Moon', 'color': EVENT_COLORS['Full Moon']},
            {'name': '🌑 New Moon', 'color': EVENT_COLORS['New Moon']},
            {'name': '☌ Conjunction', 'color': '#FFD700'},
            {'name': '□ Square', 'color': '#FF4500'},
            {'name': '△ Trine', 'color': '#32CD32'},
            {'name': '☍ Opposition', 'color': '#FF1493'},
        ]
        return items


def add_astro_to_chart(
    fig: go.Figure,
    events: list,
    x_range: Optional[tuple] = None
) -> go.Figure:
    """
    Удобная функция для добавления астро-оверлея на график.
    
    Example:
        >>> events = [
        ...     {'date': '2026-03-22', 'type': 'New Moon'},
        ...     {'date': '2026-03-25', 'type': 'Square', 'planet1': 'Mars', 'planet2': 'Saturn'},
        ... ]
        >>> fig = add_astro_to_chart(fig, events)
    """
    overlay = AstroOverlay()
    return overlay.add_to_figure(fig, events, x_range)


def create_astro_events_from_ephemeris(
    ephemeris_data: list
) -> list:
    """
    Конвертирует данные эфемерид в формат событий для оверлея.
    
    Args:
        ephemeris_data: Список dict с полями:
            - date: str (ISO format)
            - moon_phase: str (для лунных фаз)
            - retrograde: list of planets in retrograde
            - aspects: list of dicts с planet1, planet2, type, orb
    
    Returns:
        list of AstroEvent
    """
    events = []
    
    for data in ephemeris_data:
        date = data['date']
        
        # Лунные фазы
        if 'moon_phase' in data and data['moon_phase']:
            events.append(AstroEvent(
                date=date,
                event_type='moon_phase',
                description=data['moon_phase']
            ))
        
        # Ретроградные планеты
        for planet in data.get('retrograde', []):
            events.append(AstroEvent(
                date=date,
                event_type='station',
                planet=planet,
                description=f'{planet} Retrograde'
            ))
        
        # Аспекты
        for aspect in data.get('aspects', []):
            events.append(AstroEvent(
                date=date,
                event_type='aspect',
                planet=aspect.get('planet1'),
                planet2=aspect.get('planet2'),
                aspect_type=aspect.get('type'),
                orb=aspect.get('orb', 0)
            ))
    
    return events
