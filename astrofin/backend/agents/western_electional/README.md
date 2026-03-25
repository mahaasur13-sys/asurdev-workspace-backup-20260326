# Western Electional Astrology Agent

## Обзор

WesternElectionalAgent — агент для поиска оптимальных торговых окон на основе Western (Lilly) Electional Astrology.

## Принципы работы

### 1. Essential Dignities (Lilly System)

Показывают силу планеты в знаке:

| Dignity | Сила | Описание |
|---------|------|---------|
| Exaltation | +100 | Максимальная сила |
| Rulership | +80 | Собственный знак |
| Triplicity | +60-20 | Групповая сила |
| Term | +30-10 | Ограниченная сила |
| Decan | +20-5 | Дробная сила |
| Fall | -20 | Максимальная слабость |
| Debilitation | -20 | Потеря силы |
| Peregrine | +10 | Нейтральная |

### 2. Major Aspects

| Aspect | Угол | Качество |
|--------|------|----------|
| Conjunction | 0° | Нейтральное |
| Sextile | 60° | ✅ Благоприятное |
| Square | 90° | ⚠️ Напряжённое |
| Trine | 120° | ✅✅ Очень благоприятное |
| Opposition | 180° | ⚠️ Конфликтное |

### 3. House System

| House | Значение для Trading |
|-------|---------------------|
| 10th | Успех, карьера |
| 2nd | Финансы |
| 11th | Прибыль |
| 5th | Спекуляции |
| 8th | Риск |

## Использование

```python
from backend.agents.western_electional import WesternElectionalAgent

agent = WesternElectionalAgent()

# Найти окна для LONG на 7 дней
result = await agent.run({
    "symbol": "BTC",
    "price": 68000,
    "direction": "LONG",
    "horizon_days": 7,
    "election_type": "trade_entry"
})

print(f"Best window: {result.metadata['best_window']['start']}")
print(f"Score: {result.metadata['best_window']['score']}/100")
```

## Election Types

- `trade_entry` — Вход в сделку
- `trade_exit` — Выход из сделки  
- `position_open` — Открытие позиции
- `position_close` — Закрытие позиции
- `new_moon` — Новолуние
- `full_moon` — Полнолуние

## Критерии оценки

### Для LONG:
✅ Jupiter strong (Exalted/Ruled)
✅ Venus strong (financial)
✅ Moon in Taurus, Cancer, Leo, Virgo, Scorpio, Pisces
✅ Saturn weak (bearish pressure)
✅ Mars weak (less resistance)
✅ NOT void-of-course Moon

### Для SHORT:
✅ Saturn strong (bearish)
✅ Mars strong (aggression)
✅ Moon in Aries, Gemini, Libra, Capricorn, Aquarius
✅ Jupiter weak
✅ Venus weak
