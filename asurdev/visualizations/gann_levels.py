"""
Gann Levels Visualization
=========================
Расчёт и визуализация уровней Ганна (поддержки/сопротивления) 
на финансовых графиках.

Зависимости:
    pip install plotly pandas kaleido

Использование:
    from visualizations import GannLevels

    gann = GannLevels()
    
    # Расчёт уровней
    levels = gann.calculate_levels(
        high=68000, low=62000, 
        action='long',  # или 'short', 'neutral'
        price=64500
    )
    
    # Рисуем график
    fig = gann.draw_prices(
        prices_df,  # DataFrame с колонками: open, high, low, close, volume
        levels=levels,
        title="BTC/USD with Gann Levels"
    )
    
    # Сохраняем
    fig.write_image("gann_chart.png")
"""

from typing import Optional, Literal
from dataclasses import dataclass

import numpy as np

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    raise ImportError("plotly required: pip install plotly")

try:
    import pandas as pd
except ImportError:
    raise ImportError("pandas required: pip install pandas")


@dataclass
class GannLevel:
    """Один уровень Ганна."""
    price: float
    level_type: str  # 'resistance', 'support', 'pivot', 'gann_line'
    label: str
    strength: float  # 0.0 - 1.0
    color: str


class GannLevels:
    """
    Класс для расчёта и визуализации уровней Ганна.
    
    Методы Ганна:
    - Gann Fan (веер Ганна) - линии под углом 1x1, 2x1, 1x2, etc.
    - Gann Square (квадрат Ганна) - уровни из корней квадратных
    - Pivot levels (разворотные уровни)
    - Support/Resistance (уровни по максимумам/минимумам)
    """
    
    def __init__(
        self,
        square_of_nine: bool = True,
        fan: bool = True,
        pivots: bool = True
    ):
        self.square_of_nine = square_of_nine
        self.fan = fan
        self.pivots = pivots
    
    def calculate_levels(
        self,
        high: float,
        low: float,
        close: Optional[float] = None,
        action: Literal['long', 'short', 'neutral'] = 'neutral',
        price: Optional[float] = None,
        volatility_factor: float = 0.02
    ) -> dict:
        """
        Рассчитывает все уровни Ганна.
        
        Args:
            high: Максимум периода
            low: Минимум периода
            close: Цена закрытия (если отличается от high/low)
            action: Тип действия ('long', 'short', 'neutral')
            price: Текущая цена для расчёта относительных уровней
            volatility_factor: Фактор волатильности (0.02 = 2%)
            
        Returns:
            dict с ключами: 'resistance', 'support', 'pivots', 'gann_lines'
        """
        if close is None:
            close = (high + low) / 2
        if price is None:
            price = close
            
        range_price = high - low
        
        levels = {
            'resistance': [],
            'support': [],
            'pivots': [],
            'gann_lines': []
        }
        
        # === Pivot Levels (классические) ===
        pivot_point = (high + low + close) / 3
        r1 = 2 * pivot_point - low
        r2 = pivot_point + (high - low)
        r3 = high + 2 * (pivot_point - low)
        s1 = 2 * pivot_point - high
        s2 = pivot_point - (high - low)
        s3 = low - 2 * (high - pivot_point)
        
        levels['pivots'] = [
            GannLevel(pivot_point, 'pivot', 'PP', 1.0, '#FFD700'),
            GannLevel(r1, 'resistance', 'R1', 0.9, '#FF6B6B'),
            GannLevel(r2, 'resistance', 'R2', 0.7, '#FF6B6B'),
            GannLevel(r3, 'resistance', 'R3', 0.5, '#FF6B6B'),
            GannLevel(s1, 'support', 'S1', 0.9, '#4ECDC4'),
            GannLevel(s2, 'support', 'S2', 0.7, '#4ECDC4'),
            GannLevel(s3, 'support', 'S3', 0.5, '#4ECDC4'),
        ]
        
        # === Gann Square of Nine Levels ===
        if self.square_of_nine:
            sqrt_high = np.sqrt(high)
            sqrt_low = np.sqrt(low)
            sqrt_price = np.sqrt(price)
            
            # Ключевые уровни из квадрата 9
            gann_prices = []
            for n in range(-12, 13):
                # Центральные числа квадрата
                center = sqrt_price + n * 0.125  # Шаг 1/8
                gann_price = center ** 2
                if low * 0.9 < gann_price < high * 1.1:
                    gann_prices.append(gann_price)
            
            # Уникальные уровни
            gann_prices = sorted(set(gann_prices))[:8]
            
            for gp in gann_prices:
                if gp > price:
                    levels['resistance'].append(
                        GannLevel(gp, 'gann_line', f'G{self._round_price(gp)}', 0.6, '#9B59B6')
                    )
                else:
                    levels['support'].append(
                        GannLevel(gp, 'gann_line', f'G{self._round_price(gp)}', 0.6, '#3498DB')
                    )
        
        # === Gann Fan Lines ===
        if self.fan:
            # Линия 1x1 (45 градусов)
            midpoint = (high + low) / 2
            
            # Расстояние от максимума/минимума до текущей цены
            dist_high = high - price
            dist_low = price - low
            
            # Линия 1x1 проекция
            gann_1x1_up = price + dist_high * 1.0
            gann_1x1_down = price - dist_low * 1.0
            
            # Линия 2x1 проекция
            gann_2x1_up = price + dist_high * 0.5
            gann_2x1_down = price - dist_low * 0.5
            
            # Линия 1x2 проекция
            gann_1x2_up = price + dist_high * 2.0
            gann_1x2_down = price - dist_low * 2.0
            
            levels['gann_lines'] = [
                GannLevel(gann_1x1_up, 'resistance', '1x1↑', 0.8, '#E74C3C'),
                GannLevel(gann_1x1_down, 'support', '1x1↓', 0.8, '#27AE60'),
                GannLevel(gann_2x1_up, 'resistance', '2x1↑', 0.6, '#E74C3C'),
                GannLevel(gann_2x1_down, 'support', '2x1↓', 0.6, '#27AE60'),
                GannLevel(gann_1x2_up, 'resistance', '1x2↑', 0.4, '#E74C3C'),
                GannLevel(gann_1x2_down, 'support', '1x2↓', 0.4, '#27AE60'),
            ]
        
        # === Round numbers (психологические уровни) ===
        round_prices = [
            self._round_price(high * 1.05),
            self._round_price(high),
            self._round_price(midpoint),
            self._round_price(low),
            self._round_price(low * 0.95),
        ]
        
        for rp in round_prices:
            if rp > price:
                levels['resistance'].append(
                    GannLevel(rp, 'resistance', f'Round', 0.3, '#95A5A6')
                )
            else:
                levels['support'].append(
                    GannLevel(rp, 'support', f'Round', 0.3, '#95A5A6')
                )
        
        # Сортируем уровни
        levels['resistance'] = sorted(levels['resistance'], key=lambda x: x.price, reverse=True)
        levels['support'] = sorted(levels['support'], key=lambda x: x.price, reverse=True)
        
        return levels
    
    def _round_price(self, price: float) -> float:
        """Округляет цену до психологически значимого уровня."""
        if price > 50000:
            return round(price / 500) * 500
        elif price > 10000:
            return round(price / 100) * 100
        elif price > 1000:
            return round(price / 50) * 50
        else:
            return round(price / 5) * 5
    
    def draw_prices(
        self,
        prices_df,
        levels: Optional[dict] = None,
        title: str = "Gann Levels Chart",
        show_volume: bool = True
    ):
        """
        Рисует свечной график с уровнями Ганна.
        
        Args:
            prices_df: DataFrame с колонками OHLCV (open, high, low, close, volume)
            levels: Результат calculate_levels() или словарь с уровнями
            title: Заголовок графика
            show_volume: Показывать объёмы
            
        Returns:
            plotly Figure object
        """
        # Создаём subplots
        specs = [[{"secondary_y": True}]] if show_volume else [[None]]
        fig = make_subplots(
            rows=1, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(title,),
            specs=specs
        )
        
        # Свечной график
        fig.add_trace(
            go.Candlestick(
                x=prices_df.index,
                open=prices_df['open'],
                high=prices_df['high'],
                low=prices_df['low'],
                close=prices_df['close'],
                name='OHLC',
                increasing_line_color='#26A69A',
                decreasing_line_color='#EF5350',
                increasing_fillcolor='#26A69A',
                decreasing_fillcolor='#EF5350',
            ),
            row=1, col=1
        )
        
        # Объёмы
        if show_volume and 'volume' in prices_df.columns:
            colors = ['#26A69A' if prices_df['close'].iloc[i] >= prices_df['open'].iloc[i] 
                     else '#EF5350' for i in range(len(prices_df))]
            
            fig.add_trace(
                go.Bar(
                    x=prices_df.index,
                    y=prices_df['volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.5,
                    yaxis='y2'
                ),
                row=1, col=1,
                secondary_y=True
            )
        
        # Добавляем уровни
        if levels:
            self._add_levels_to_figure(fig, levels, prices_df.index[0], prices_df.index[-1])
        
        # Настройка layout
        fig.update_layout(
            template='plotly_dark',
            height=600,
            xaxis_rangeslider_visible=False,
            yaxis=dict(
                title='Price',
                showgrid=True,
                gridcolor='#2D2D2D',
            ),
            yaxis2=dict(
                title='Volume',
                showgrid=False,
                overlaying='y',
                side='right',
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            hovermode='x unified',
        )
        
        return fig
    
    def _add_levels_to_figure(self, fig, levels: dict, x_start, x_end):
        """Добавляет горизонтальные линии уровней на график."""
        all_levels = []
        
        # Собираем все уровни
        for level_list in [levels.get('resistance', []), 
                         levels.get('support', []),
                         levels.get('pivots', []),
                         levels.get('gann_lines', [])]:
            if isinstance(level_list, list):
                all_levels.extend(level_list)
            elif isinstance(level_list, dict):
                all_levels.append(level_list)
        
        for level in all_levels:
            if isinstance(level, GannLevel):
                price = level.price
                color = level.color
                width = 2 if level.strength > 0.7 else 1
                dash = 'solid' if level.level_type in ['pivot', 'resistance', 'support'] else 'dash'
            elif isinstance(level, dict):
                price = level.get('price')
                color = level.get('color', '#888888')
                width = level.get('width', 1)
                dash = level.get('dash', 'solid')
            else:
                continue
            
            fig.add_hline(
                y=price,
                line_color=color,
                line_width=width,
                line_dash=dash,
                annotation_text=f"${price:,.0f}",
                annotation_position="right",
                annotation_font_size=10,
                annotation_font_color=color,
            )
    
    def add_astro_markers(
        self,
        fig,
        astro_events: list,
        x_start,
        x_end
    ):
        """
        Добавляет астрологические маркеры на график.
        
        Args:
            fig: Plotly Figure
            astro_events: Список событий [
                {'date': '2026-03-22', 'type': 'New Moon', 'planet': 'Moon'},
                {'date': '2026-03-25', 'type': 'Mars Square Saturn', 'planet': 'Mars'},
                ...
            ]
            x_start: Начальная дата графика
            x_end: Конечная дата графика
        """
        for event in astro_events:
            date = event.get('date')
            event_type = event.get('type', '')
            planet = event.get('planet', '')
            color = event.get('color', '#9B59B6')
            
            # Определяем цвет и символ по типу события
            if 'Moon' in event_type or 'Full Moon' in event_type:
                symbol = '🌕' if 'Full' in event_type else '🌑'
                color = '#F1C40F'
            elif 'Mars' in planet:
                symbol = '♂'
                color = '#E74C3C'
            elif 'Venus' in planet:
                symbol = '♀'
                color = '#E91E63'
            elif 'Jupiter' in planet:
                symbol = '♃'
                color = '#3498DB'
            elif 'Saturn' in planet:
                symbol = '♄'
                color = '#95A5A6'
            else:
                symbol = '✦'
            
            fig.add_vline(
                x=date,
                line_color=color,
                line_width=2,
                line_dash='dot',
                annotation_text=f"{symbol} {event_type}",
                annotation_position='top',
                annotation_font_size=9,
                annotation_font_color=color,
            )
        
        return fig


def calculate_gann_levels(
    high: float,
    low: float,
    close: Optional[float] = None,
    action: Literal['long', 'short', 'neutral'] = 'neutral'
) -> dict:
    """
    Удобная функция для быстрого расчёта уровней Ганна.
    
    Example:
        >>> levels = calculate_gann_levels(high=68000, low=62000, close=64500)
        >>> for level in levels['resistance']:
        ...     print(f"{level.label}: ${level.price:,.0f}")
    """
    gann = GannLevels()
    return gann.calculate_levels(high, low, close, action)


def draw_gann_chart(
    prices_df,
    levels: Optional[dict] = None,
    astro_events: Optional[list] = None,
    title: str = "Chart with Gann Levels"
) -> go.Figure:
    """
    Удобная функция для создания полного графика Ганна.
    
    Example:
        >>> import pandas as pd
        >>> df = pd.read_csv('btc.csv', parse_dates=True, index_col='date')
        >>> levels = calculate_gann_levels(df['high'].max(), df['low'].min())
        >>> astro = [{'date': '2026-03-22', 'type': 'New Moon'}]
        >>> fig = draw_gann_chart(df, levels, astro)
        >>> fig.write_html('gann_chart.html')
    """
    gann = GannLevels()
    fig = gann.draw_prices(prices_df, levels, title)
    
    if astro_events:
        fig = gann.add_astro_markers(
            fig, astro_events, 
            prices_df.index[0], 
            prices_df.index[-1]
        )
    
    return fig
