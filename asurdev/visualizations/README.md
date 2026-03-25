# asurdev Sentinel — Visualizations

Модуль визуализации для астрологических и финансовых данных.

## Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements-visualizations.txt

# Запуск демо
python visualizations/demo.py
```

## Структура

| Файл | Описание |
|------|----------|
| `zodiac_wheel.py` | Натальная карта (matplotlib → PNG) |
| `gann_levels.py` | Gann уровни (plotly → HTML/PNG) |
| `astro_overlay.py` | Астро-оверлей на свечные графики |

## Использование

### 1. Зодиакальное колесо

```python
from visualizations import ZodiacWheel

wheel = ZodiacWheel(style='modern')
img_bytes = wheel.draw(
    positions={
        'Sun': {'sign': 0, 'degree': 15},
        'Moon': {'sign': 3, 'degree': 22},
    },
    houses={1: 0, 2: 25},
    aspects=[{'planet1': 'Sun', 'planet2': 'Moon', 'type': 'Trine', 'orb': 7}]
)

# Сохранить
with open('wheel.png', 'wb') as f:
    f.write(img_bytes)
```

### 2. Gann уровни

```python
from visualizations import GannLevels
import pandas as pd

gann = GannLevels()
levels = gann.calculate_levels(high=68000, low=62000, close=64500)

# Нарисовать график
fig = gann.draw_prices(prices_df, levels)
fig.write_html('gann_chart.html')
```

### 3. Астро-оверлей

```python
from visualizations import AstroOverlay

overlay = AstroOverlay()
events = [
    {'date': '2026-03-22', 'type': 'New Moon'},
    {'date': '2026-03-25', 'type': 'Square', 'planet1': 'Mars', 'planet2': 'Saturn'},
]
fig = overlay.add_to_figure(base_figure, events)
```

## React компоненты

См. `ui_react/src/components/ZodiacWheel.tsx` и `GannChart.tsx`.
