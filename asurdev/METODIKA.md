# asurdev Sentinel — Методика Анализа

## Концепция

**asurdev Sentinel** — гибридная система принятия решений, объединяющая:
- Классическую технический анализ (Gann, Andrews, Dow Theory)
- Цикловой анализ (Timing Solution)
- Финансовую астрологию (Wester + Vedic)
- Консенсус-синтез C.L.E.A.R.

---

## Структура анализа (C.L.E.A.R.)

```
┌─────────────────────────────────────────────────────────────┐
│                    C.L.E.A.R. FRAMEWORK                      │
├─────────────────────────────────────────────────────────────┤
│  C — Cycle Analysis        │  Циклы (astro + timing)        │
│  L — Lunar State           │  Фаза Луны (бычий/медвежий)    │
│  E — Essential Dignities   │  Dignities планет (5→-5)       │
│  A — Aspects & Receiptions │  Аспекты, рецепции            │
│  R — Rule of 7             │  Ключевые ценовые уровни       │
└─────────────────────────────────────────────────────────────┘
```

### Веса агентов

| Агент | Вес | Тип |
|-------|-----|-----|
| MarketAnalyst | 25% | Technical |
| BullResearcher | 15% | Fundamental |
| BearResearcher | 15% | Fundamental |
| Astrologer | 20% | Astrology |
| CycleAgent | 10% | Cycles |
| Merriman | 10% | Elliott Wave |
| Gann | 5% | Gann |

---

## I. Астрологический анализ

### A. Лунные фазы (Vedic)

| Фаза | Сигнал | Сила |
|------|--------|------|
| New Moon → First Quarter | 🟢 BULLISH | 55% |
| Full Moon → Last Quarter | 🔴 BEARISH | 55% |

### B. Essential Dignities (Lilly)

```
Formula: Score = Exalt(+5) + Triplicity(±3) + Term(±2) + Face(±1)
```

**Сигнал:**
- Score > 5 → STRONG_BULLISH
- Score 3-5 → BULLISH  
- Score 0-2 → NEUTRAL
- Score -2-(-1) → BEARISH
- Score < -2 → STRONG_BEARISH

### C. Аспекты (Orbs)

| Аспект | Орб | Природа |
|--------|-----|---------|
| Conjunction | 8° | Смешанная |
| Sextile | 6° | Good |
| Square | 8° | Bad |
| Trine | 8° | Good |
| Opposition | 10° | Bad |

**Бычьи аспекты:** Trine + Sextile = +2
**Медвежьи аспекты:** Square + Opposition = -2

### D. Nakshatras (Лунные стоянки)

| Тип | Сигнал |
|-----|--------|
| Mesh (Aries), Simha (Leo), Dhanush (Sagittarius) | 🔴 Fire — агрессия |
| Vrushab (Taurus), Makar (Capricorn), Kumbha (Aquarius) | 🟢 Earth — стабильность |
| Mithun (Gemini), Kanya (Virgo), Tula (Libra) | 🔵 Air — интеллект |
| Vrushchik (Scorpio), Meen (Pisces), Kark (Cancer) | 🟣 Water — эмоции |

---

## II. Технический анализ

### A. Gann Square of 9

```
Levels = √(Price × Price) → cardinls + ordinals
Cardinals: 0°, 90°, 180°, 270°
Ordinals: 45°, 135°, 225°, 315°
```

**Signal:** цена у поддержки/сопротивления Gann = +10%

### B. Andrews Pitchfork

```
Median Line = 3 points (Pivots A, B, C)
SHL = Median - 2×(B - Median)
SSL = Median + 2×(B - Median)
```

**Signal:** цена у Median/SSL/SHL

### C. Dow Theory

```
BULL: HH > HH && HL > HL
BEAR: LH < LH && LL < LL
```

---

## III. Цикловой анализ

### Timing Solution Integration

- 4-year cycle (Kondratieff)
- 52-week cycle (Jagerson)
- 28-day lunar cycle
- 7-day minor cycle

---

## IV. Формула синтеза

```python
def synthesize(responses) -> dict:
    # 1.加权平均
    bull_weight = sum(r.confidence for r in bull_agents)
    bear_weight = sum(r.confidence for r in bear_agents)
    
    # 2. Astro modifier
    astro_modifier = get_astro_modifier(date)
    
    # 3. Final score
    score = (bull_weight - bear_weight) × astro_modifier
    
    # 4. Verdict
    if score > 60: return STRONG_BUY
    elif score > 30: return BUY
    elif score > -30: return NEUTRAL
    elif score > -60: return SELL
    else: return STRONG_SELL
```

---

## V. Риск-менеджмент

| Вердикт | Max Risk | Position |
|---------|----------|----------|
| STRONG_BUY | 2% | 20% |
| BUY | 3% | 15% |
| NEUTRAL | 5% | 10% |
| SELL | 3% | 10% |
| STRONG_SELL | 2% | 5% |

---

## VI. Ограничения

⚠️ **Дисклеймер:**
1. Система — **интеллектуальный помощник**, не финансовый совет
2. Астрология — **дополнительный фильтр**, не замена техническому анализу
3. Результаты прошлого тестирования не гарантируют будущих результатов
4. Всегда используйте собственный риск-менеджмент
