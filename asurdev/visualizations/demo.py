#!/usr/bin/env python3
"""
Demo script для visualizations модуля asurdev Sentinel.
Запускать: python visualizations/demo.py
"""

import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualizations import ZodiacWheel, GannLevels, AstroOverlay
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def demo_zodiac_wheel():
    """Демо зодиакального колеса."""
    print("\n" + "=" * 60)
    print("🛡️  DEMO: Zodiac Wheel (Натальная карта)")
    print("=" * 60)
    
    # Пример позиций планет
    positions = {
        'Sun': {'sign': 0, 'degree': 15},      # Овен 15°
        'Moon': {'sign': 3, 'degree': 22},      # Рак 22°
        'Mercury': {'sign': 0, 'degree': 8},    # Овен 8°
        'Venus': {'sign': 1, 'degree': 25},     # Телец 25°
        'Mars': {'sign': 5, 'degree': 10},     # Дева 10°
        'Jupiter': {'sign': 9, 'degree': 5},   # Козерог 5°
        'Saturn': {'sign': 8, 'degree': 18},   # Стрелец 18°
    }
    
    # Пример домов
    houses = {
        1: 0,    # AC в Овене
        2: 25,   # 2 дом в Тельце
        3: 15,   # 3 дом в Близнецах
        4: 0,    # IC в Раке
        5: 25,   # 5 дом во Льве
        6: 18,   # 6 дом в Деве
        7: 0,    # DC в Весах
        8: 25,   # 8 дом в Скорпионе
        9: 15,   # 9 дом в Стрельце
        10: 0,   # MC в Козероге
        11: 25,  # 11 дом в Водолее
        12: 18,  # 12 дом в Рыбах
    }
    
    # Пример аспектов
    aspects = [
        {'planet1': 'Sun', 'planet2': 'Moon', 'type': 'Trine', 'orb': 7},
        {'planet1': 'Sun', 'planet2': 'Mars', 'type': 'Square', 'orb': 5},
        {'planet1': 'Venus', 'planet2': 'Jupiter', 'type': 'Conjunction', 'orb': 3},
        {'planet1': 'Mars', 'planet2': 'Saturn', 'type': 'Opposition', 'orb': 2},
    ]
    
    # Рисуем в разных стилях
    for style in ['modern', 'classic', 'astroprint']:
        wheel = ZodiacWheel(style=style)
        img_bytes = wheel.draw(positions, houses, aspects, title=f'asurdev - {style}')
        
        filename = f'zodiac_wheel_{style}.png'
        with open(filename, 'wb') as f:
            f.write(img_bytes)
        print(f"✅ Saved: {filename} ({len(img_bytes)} bytes)")
    
    print("\n📊 Позиции планет:")
    for planet, data in positions.items():
        sign_names = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 
                     'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
        print(f"   {planet:10} → {sign_names[data['sign']]} {data['degree']}°")
    
    print("\n🏠 Дома:")
    sign_names = ['Овен', 'Телец', 'Близнецы', 'Рак', 'Лев', 'Дева', 
                 'Весы', 'Скорпион', 'Стрелец', 'Козерог', 'Водолей', 'Рыбы']
    for h, deg in houses.items():
        house_sign = sign_names[int(deg / 30) % 12]
        print(f"   House {h:2} → {house_sign} {deg}°")


def demo_gann_levels():
    """Демо Gann уровней."""
    print("\n" + "=" * 60)
    print("📈 DEMO: Gann Levels")
    print("=" * 60)
    
    # Генерируем тестовые данные
    dates = [datetime(2026, 3, 1) + timedelta(days=i) for i in range(30)]
    
    # Цена с трендом
    base_price = 64000
    np.random.seed(42)
    prices_data = []
    
    for i, date in enumerate(dates):
        noise = np.random.randn() * 500
        trend = i * 100
        close = base_price + trend + noise
        high = close + abs(np.random.randn()) * 300
        low = close - abs(np.random.randn()) * 300
        open_price = close + np.random.randn() * 200
        
        prices_data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': int(np.random.uniform(1000, 5000)),
        })
    
    df = pd.DataFrame(prices_data)
    df.set_index('date', inplace=True)
    
    # Расчёт уровней
    gann = GannLevels()
    high = df['high'].max()
    low = df['low'].min()
    close = df['close'].iloc[-1]
    
    levels = gann.calculate_levels(high=high, low=low, close=close)
    
    print(f"\n📊 Price Range: ${low:,.0f} - ${high:,.0f}")
    print(f"   Current Close: ${close:,.0f}")
    
    print("\n🔴 Resistance Levels:")
    for level in levels['resistance'][:4]:
        print(f"   {level.label}: ${level.price:,.0f} (strength: {level.strength})")
    
    print("\n🟢 Support Levels:")
    for level in levels['support'][:4]:
        print(f"   {level.label}: ${level.price:,.0f} (strength: {level.strength})")
    
    print("\n🟡 Pivot Points:")
    for level in levels['pivots']:
        print(f"   {level.label}: ${level.price:,.0f}")
    
    # Рисуем график
    fig = gann.draw_prices(df, levels, title="BTC/USD with Gann Levels", show_volume=True)
    fig.write_html('gann_chart.html')
    print("\n✅ Saved: gann_chart.html")
    
    return df, levels


def demo_astro_overlay():
    """Демо астро-оверлея."""
    print("\n" + "=" * 60)
    print("☽ DEMO: Astro Overlay")
    print("=" * 60)
    
    # Астрологические события
    events = [
        {'date': '2026-03-22', 'type': 'New Moon', 'planet': 'Moon'},
        {'date': '2026-03-25', 'type': 'Square', 'planet1': 'Mars', 'planet2': 'Saturn', 'orb': 1},
        {'date': '2026-03-28', 'type': 'Full Moon', 'planet': 'Libra'},
        {'date': '2026-04-01', 'type': 'Trine', 'planet1': 'Venus', 'planet2': 'Jupiter', 'orb': 2},
        {'date': '2026-04-05', 'type': 'Mercury Retrograde', 'planet': 'Mercury'},
    ]
    
    overlay = AstroOverlay()
    
    print("\n📅 Astro Events:")
    for event in events:
        if 'planet1' in event:
            print(f"   {event['date']}: {event['planet1']} {event['type']} {event['planet2']}")
        else:
            print(f"   {event['date']}: {event['type']} ({event.get('planet', 'Moon')})")
    
    # Создаём базовый график
    from visualizations.gann_levels import GannLevels
    import plotly.graph_objects as go
    
    dates = [datetime(2026, 3, 20) + timedelta(days=i) for i in range(20)]
    prices = [64000 + i * 200 + np.random.randn() * 100 for i in range(20)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name='BTC/USD',
        line=dict(color='#26A69A', width=2)
    ))
    
    # Добавляем астро оверлей
    fig = overlay.add_to_figure(fig, events)
    
    fig.update_layout(
        title='BTC/USD with Astro Events',
        template='plotly_dark',
        height=400,
    )
    
    fig.write_html('astro_overlay_chart.html')
    print("\n✅ Saved: astro_overlay_chart.html")


def main():
    print("\n" + "=" * 60)
    print("🛡️  asurdev Sentinel - Visualizations Demo")
    print("=" * 60)
    
    try:
        demo_zodiac_wheel()
        df, levels = demo_gann_levels()
        demo_astro_overlay()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        print("\nGenerated files:")
        print("  - zodiac_wheel_modern.png")
        print("  - zodiac_wheel_classic.png")
        print("  - zodiac_wheel_astroprint.png")
        print("  - gann_chart.html")
        print("  - astro_overlay_chart.html")
        
    except ImportError as e:
        print(f"\n❌ Missing dependency: {e}")
        print("\nInstall with:")
        print("  pip install -r requirements-visualizations.txt")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
