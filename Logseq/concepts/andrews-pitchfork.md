---
type:: concept
id:: andrews-pitchfork
tags:: [concept, technical-analysis, trend-lines, andrews-pitchfork, patrick-mikula]
aliases:: [вилы Эндрюса, Andrews Pitchfork, медианные линии, pitchfork analysis]
created:: 2026-03-27
updated:: 2026-03-27
related:: [[concepts/gann-theory]], [[concepts/elliott-wave]], [[methods/thompson_sampling]], [[agents/technical_agent]]
---

# Andrews Pitchfork & Patrick Mikula Methods

## Определение

**Andrews Pitchfork (вилы Эндрюса)** — инструмент технического анализа, разработанный доктором Аланом Эндрюсом (Alan Andrews) в 1960-х годах. Представляет собой три параллельные линии: центральная медианная линия (handle) и две внешние линии (tines), образующие канал.

Основной принцип: **цена стремится вернуться к медианной линии примерно в 80% случаев**.

## Исторический контекст

- **1960-е** — Алан Эндрюс разрабатывает метод медианных линий
- **1980-е–1990-е** — Патрик Микула (Patrick Mikula), CTA, систематизирует методы в Austin Financial Group
- **2005** — публикация книги «Лучшие методы линий тренда Алана Эндрюса плюс пять новых техник»
- **Современность** — индикатор доступен на TradingView, MultiCharts

## Часть 1. Оригинальные методы Алана Эндрюса

### 1.1 Построение вил (Pitchfork Construction)

Для построения классических вил Эндрюса требуется **три последовательных pivot-точки**:

| Точка | Обозначение | Описание |
|-------|-------------|---------|
| **A** | Anchor (якорь) | Начальный pivot — точка разворота тренда |
| **B** | First tine | Первый свинг в противоположном направлении |
| **C** | Second tine | Второй свинг, совпадающий по направлению с точкой A |

**Паттерны:**
- **Low-High-Low (LHL)** — точка A — минимум, B — максимум, C — минимум (восходящий тренд)
- **High-Low-High (HLH)** — точка A — максимум, B — минимум, C — максимум (нисходящий тренд)

### 1.2 Медианная линия (Median Line)

Центральная линия вил — ключевой элемент метода:
- Цена возвращается к медианной линии примерно в **80% случаев**
- Если цена **не достигает медианы** — сигнал возможного разворота
- Если цена **пробивает медиану** — движение, вероятно, продолжится к противоположному зубу

### 1.3 Фильтрация точки C

Эндрюс использовал осциллятор **Stochastic** для повышения точности идентификации точки C.

### 1.4 Модификации вил

| Вариант | Построение | Применение |
|---------|------------|------------|
| **Original (Andrews)** | Якорь остаётся в точке A | Сильные трендовые рынки |
| **Schiff** | Якорь смещается на 50% к точке B **только по цене** | Мелкие тренды, коррекционные фазы |
| **Modified Schiff** | Якорь смещается на 50% **и по цене, и по времени** | Слабые или боковые тренды |

## Часть 2. Пять новых техник Патрика Микулы

> **Источник:** Patrick Mikula, *«Лучшие методы линий тренда Алана Эндрюса плюс пять новых техник»* (Austin Financial Group, 2005)

### Техника 1: Action & Reaction Lines

Основана на **третьем законе Ньютона**: «действие равно противодействию».

- **Action Lines** — параллельны A-B, проецируют исходный импульс в будущее
- **Reaction Lines** — параллельны B-C, отражают ритм реакции рынка
- Шаг распространения = длина «ручки» (handle)

### Техника 2: Lattice Matrix

Создаёт сетку (grid) внутри структуры вил:
- Горизонтальная линия на ценовом уровне пивота
- Вертикальные линии в каждой точке пересечения с медианой и параллелями
- Отмечают **временные точки**, где геометрия цена-время сходится

### Техника 3: Sliding Parallel Lines

Параллельные линии сдвигаются при появлении новых экстремумов — адаптивное отслеживание рыночной структуры.

### Техника 4: Unorthodox Trend Lines

Расширение классических линий тренда:
- **Fan Lines** — веерные линии разной степени крутизны
- **Specific Trend Lines** — с учётом внутренней структуры рынка

### Техника 5: Multiple Pitchfork Trading

Интеграция нескольких вил на разных таймфреймах:
- Старшие вилы → основной тренд
- Младшие вилы → точки входа

## Часть 3. Современные расширения (Hyperfork Matrix)

**Hyperfork Matrix** — современная реализация на TradingView:

| Компонент | Описание |
|-----------|---------|
| **Propagation Lines** | Action и Reaction, проецируемые в будущее и прошлое |
| **Lattice Matrix** | Автоматическое построение сетки с вертикалями |
| **Extra Parallels** | Дополнительные параллели за пределами B и C |
| **Backward Lines** | Проецируемые в прошлое для выявления исторических конвергенций |

## Часть 4. Применение в AstroFinSentinelV5

| Агент | Использование |
|-------|---------------|
| `technical_agent.py` | Расчёт уровней поддержки/сопротивления на основе вил |
| `astro_council_agent.py` | Комбинирование с астрологическими циклами (Gann, Bradley) |
| `synthesis_agent.py` | Агрегация сигналов от вил с другими индикаторами |

### Алгоритмическая реализация

```python
# Расчёт медианной линии
def calculate_median_line(pivot_a, pivot_b, pivot_c):
    midpoint = (pivot_b + pivot_c) / 2
    slope = (midpoint.price - pivot_a.price) / (midpoint.time - pivot_a.time)
    return Line(start=pivot_a, slope=slope)

# Расчёт Action/Reaction линий
def calculate_action_lines(median_line, ab_segment, handle_length):
    points = median_line.get_points_at_intervals(handle_length)
    return [Line(point, slope=ab_segment.slope) for point in points]
```

## Источники

**Основные:**
- Mikula, Patrick. *«Лучшие методы линий тренда Алана Эндрюса плюс пять новых техник»*. Austin Financial Group, 2005.
- Dologa, Mircea. *«Integrated Pitchfork Analysis: Basic to Intermediate Level»*. Wiley Trading.

**Дополнительные:**
- Hyperfork Matrix — TradingView Indicator (BlueprintResearch)
- MultiCharts — Andrews' Pitchfork Documentation

---

## EC-01 Hubris Cap — Ответ

**EC-01 (Error Cap / Hubris Cap)** — это поведенческий фильтр для агентов:

1. **Что это:** Ограничение на максимальную уверенность (confidence) агента, когда его историческая точность (win_rate) слишком высокая — это может указывать на переобучение (overfitting).

2. **Зачем:** Агенты с 90%+ accuracy в бэктесте часто «завышают уверенность» в реальной торговле. Hubris Cap ограничивает `confidence ≤ 85%` пока агент не наберёт ≥50 реальных сделок.

3. **Где реализован:** `core/belief.py` — в методе `get_adjusted_confidence()`:
   ```python
   def get_adjusted_confidence(self, agent_name: str, raw_confidence: int) -> int:
       belief = self.get(agent_name)
       if belief and belief.n_sessions < 50 and belief.mean_accuracy > 0.85:
           # Hubris Cap: снижаем уверенность переобученных агентов
           return min(raw_confidence, 85)
       return raw_confidence
   ```

4. **Формула:**
   - Если `n_sessions < 50` И `mean_accuracy > 0.85` → `confidence = min(confidence, 85)`
   - Иначе → `confidence = raw_confidence`

Это защищает от «хабрис-эффекта» — когда агент с красивым бэктестом начинает давать сверхуверенные сигналы на реальном рынке.

---

## Изображения

![andrews-pitchfork-construction](./concepts/andrews-pitchfork-construction.png)
*Рис.1 — Построение вил Эндрюса: выбор точек A, B, C и проведение медианной линии*

![andrews-pitchfork-diagram](./concepts/andrews-pitchfork-diagram.png)
*Рис.2 — Вилы Эндрюса на реальном графике: медианная линия и параллельные каналы*

![action-reaction-lines](./concepts/action-reaction-lines.png)
*Рис.3 — Action & Reaction Lines: проецирование импульса в будущее*
