---
type:: concept
id:: muhurta_trading
tags:: [concept, astrology, timing, vedic, electional]
weight:: 3
created:: 2026-03-27
updated:: 2026-03-27
sources:: [Muhurta Chintamani (Mantreshvara, XIV век), B.V. Raman «Muhurta», V.K. Shridhar «Electional Astrology»]
---

# Muhurta Trading — Ведический Астрологический Тайминг

## Определение

**Muhurta** (санскр. मुहूर्त, muhūrta) — «момент», «единица времени» (48 минут) в ведической астрологии. **Muhurta Shastra** — наука выбора благоприятного момента для любого начинания.

> «Как корабль без руля, так и дело без Muhurta — на произвол волн кармы.»

---

## Ключевые понятия

### 1. Panchanga (Панчанга) — 5 столпов

| Элемент | Значение | Благоприятный для Muhurta |
|---------|---------|--------------------------|
| **Tithi** (титхи) | Лунный день (1–15, Shukla/Brihat) | 2,3,5,7,10,11,13 |
| **Vaar** (вар) | День недели | Среда (Budh), Четверг (Brihaspati), Пятница (Shukra) |
| **Nakshatra** (накшатра) | Лунная стоянка (27 звезд) | Rohini, Mrigashira, Uttara Phalguni, Swati, Hasta, Pushya, Shravana, Dhanistha, Uttara Bhadrapada |
| **Yoga** (йога) | Лунно-солнечное сочетание | Amrita, Siddha, Shubha, Mitra |
| **Karana** (карана) | Половина титхи (11固定) | Bava, Kaulava, Taitila, Garaja, Vanija |

### 2. Накшатры — ключ к трейдингу

| Категория | Накшатры | Применение |
|---------|---------|-----------|
| **Dhan** (богатство) | Rohini, Swati, Dhanistha | Входы в позицию |
| **Shubha** (благо) | Pushya, Hasta, Uttara Phalguni | Долгосрочные сделки |
| **Kshaya** (упадок) | Ashlesha, Magha, Mula | Избегать входов |
| **Trayodasha** (разрушение) | Bharani, Krittika (частично) | Катастрофические дни |

### 3. Choghadiya — 8 мухурт в сутках

| Тип | Время | Сигнал |
|-----|-------|--------|
| **Amrut** (A) | 1, 4 | ✅ Лучшее время для входа |
| **Shubha** (S) | 2, 5 | ✅ Хорошее |
| **Mira** (M) | 3, 7 | ⚠️ Нейтральное |
| **Chara** (C) | 6, 8 | ❌ Избегать |

### 4. Vedic Yoga — 27 типов

Три ключевых для трейдинга:
- **Amrita Yoga** — «бессмертие», лучшее время для BUY
- **Siddha Yoga** — исполнение целей, для закрытия сделок
- **Pati Yoga** — конфликт, избегать открытия

---

## Muhurta Chintamani — первоисточник

### О тексте

| | |
|---|---|
| **Автор** | Мантрешвара (Mantreshvara) |
| **Эпоха** | XIV век н.э. |
| **Язык** | Санскрит |
| **Перевод** | B.V. Raman, «Muhurta Chintamani» (1946) |
| **Статус** | Называется «Библией Muhurta» — главный авторитетный источник |

### Структура (кратко)

1. **Adhyaya 1–5**: Общие принципы Muhurta, Panchanga Shuddhi
2. **Adhyaya 6–10**: Специфические начинания (путешествия, торговля, брак)
3. **Adhyaya 11–15**: Muhurta для духовных практик и медитации
4. **Adhyaya 16–20**: Война, политика, государственные дела
5. **Adhyaya 21–30**: Исправление ошибок, гриф «Шанигарахрита»

### Ключевые правила для финансовой Muhurta

> Из Muhurta Chintamani:

1. **Tithi Rule**: Тихи 2, 3, 5, 7, 10, 11, 13 (Shukla Paksha) — лучшие для финансовых операций
2. **Nakshatra Rule**: Rohini, Swati, Dhanistha, Pushya, Shravana — благоприятны для накопления капитала
3. **Yoga Rule**: Amrita Yoga и Siddha Yoga — усиливают результат
4. **Karana Rule**: Bava, Kaulava — нейтральные; Garaja — осторожно

---

## Как применяется в AstroFin Sentinel

### ElectoralAgent (agents/electoral_agent.py)

```python
async def run_electoral_agent(
    symbol: str,
    side: str = "LONG",
    nakshatra_filter: str = "Dhan",
    include_choghadiya: bool = True,
) -> dict:
    """
    Muhurta timing —сканирование окон входа по Choghadiya/Nakshatra.
    Вес в системе: 3%
    """
```

**Логика:**
1. Текущее время → Panchanga (Tithi, Vaar, Nakshatra, Yoga, Karana)
2. Поиск следующего благоприятного окна (Nakshatra Dhan или Shubha)
3. Choghadiya Amrut/Shubha → подтверждение входа
4. Возвращает `window_start`, `window_end`, `strength_score` (0–100)

### Choghadiya Lookup (встроенная таблица)

| Время IST | 06:00–07:48 | 07:48–09:36 | 09:36–11:24 | 11:24–13:12 | 13:12–15:00 | 15:00–16:48 | 16:48–18:36 | 18:36–20:24 |
|-----------|------------|------------|-------------|--------------|--------------|--------------|--------------|--------------|
| **День 1** | Amrut | Shubha | Chara | Mira | Chara | Shubha | Amrut | Kaulava |
| **День 2** | Shubha | Amrut | Kaulava | Chara | Mira | Kaulava | Shubha | Mira |
| **День 3** | Mira | Chara | Shubha | Amrut | Kaulava | Amrut | Mira | Chara |

### Практическое применение

```
Текущая накшатра = Rohini (Dhan, богатство) ✅
Текущая йога = Amrita Yoga ✅
Choghadiya = Amrut (06:00-07:48 IST) ✅
Tithi = Trayodashi (13) ⚠️

→ Вход ОЧЕНЬ благоприятен (3/4 индикатора зелёные)
→ Но Trayodashi = разрушение → подождать закрытия свечи
→ Окно: Rohini + Amrita + Amrut = ПОКУПАТЬ через 2 часа
```

---

## Дополнительные источники

| Книга | Автор | Год | Примечание |
|-------|-------|-----|-----------|
| **Muhurta Chintamani** | Mantreshvara | XIV в. | Первоисточник |
| **Muhurta** | B.V. Raman | 1946 | Перевод + комментарий |
| **Electional Astrology** | V.K. Shridhar | 2019 | Современный практический труд |
| **Phaladeepika** | Mantreshvara | XIV в. | Дополнительный источник по Muhurta |

---

## Другие концепции

- [[bradley_siderograph]] — сезонность S&P 500
- [[gann_theory]] — углы Ганна
- [[market_cycles]] — рыночные циклы

---

## Теги

#concept #astrology #muhurta #vedic #timing #trading #electoral #nakshatra #choghadiya #panchanga # MuhurtaChintamani
