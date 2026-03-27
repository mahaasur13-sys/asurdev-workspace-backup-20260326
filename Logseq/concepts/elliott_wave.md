---
type:: concept
id:: elliott_wave
tags:: [concept, technical-analysis, wave-theory, fractals, market-cycles, _method]
aliases:: [Elliott Wave, EWP, Ralph Nelson Elliott, Wave Principle, Prechter]
created:: 2026-03-27
updated:: 2026-03-27
related:: [[concepts/bradley_siderograph]], [[concepts/gann_theory]], [[agents/elliot_agent]], [[concepts/muhurta_trading]]
---

# Elliott Wave Theory (Волновой принцип Эллиотта)

## Определение

**Elliott Wave Theory (EWP)** — метод технического анализа, согласно которому движение цен на финансовых рынках follows a recognizable repetitive **wave patterns** driven by collective investor psychology (socionomics). Рыночные движения имеют **фрактальную** природу: одни и те же паттерны повторяются на всех таймфреймах.

> *"The stock market is a creation of man and therefore reflects the peculiar vagrant expression of human beings."* — Ralph Nelson Elliott

---

## Исторический контекст

| Дата | Событие |
|------|---------|
| **1938** | Ральф Нельсон Эллиотт публикует *The Wave Principle* в журнале *Financial World* |
| **1938** | Книга *The Wave Principle* (Financial World) |
| **1946** | Эллиотт публикует *Nature's Law — The Secret of the Universe* — итоговую работу |
| **1948** | Смерть Ральфа Нельсона Эллиотта |
| **1978** | **Robert Prechter и A.J. Frost** публикуют *Elliott Wave Principle: Key to Market Behavior* — библию EWP[^1] |
| **1979** | Prechter основывает **Elliott Wave International (EWI)** — крупнейший сервис волнового анализа |
| **1990s–н.в.** | EWI применяет EWP к криптовалютам, forex, товарам; Prechter опубликовал >20 книг |

**Теория socionomics:** рыночные паттерны отражают социальное настроение, а не внешние события.

---

## Базовая структура: 5-3 волна

### Импульсная фаза (5 волн)

```
         5
        /\      ← Wave 5: финальный толчок
       /  \     ← Wave 3: самый сильный
      /    \   ← Wave 1: начальный толчок
     /      \
    /________\ ← Wave 2: первый откат
             \
              \ ← Wave 4: второй откат
               \
                ← Wave A: начало коррекции
```

| Волна | Тип | Характеристика |
|-------|------|----------------|
| **Wave 1** | Импульс | Начальный толчок (часто слабый, по статистике ~35% от величины Wave 3) |
| **Wave 2** | Коррекция | Откат; **не может** откатиться на 100% Wave 1; типично 50–78.6% |
| **Wave 3** | Импульс | **Самая длинная** волна; **не может** быть самой короткой; обычно 161.8–261.8% от Wave 1 |
| **Wave 4** | Коррекция | Откат; **не может** заходить в ценовую территорию Wave 1; типично 38.2–50% |
| **Wave 5** | Импульс | Финальный толчок; расхождение с RSI (дивергенция) — частый сигнал разворота |

### Коррекционная фаза (3 волны)

```
        A
       /\      ← Wave A: начинается в обратном направлении
      /  \     ← Wave B: откат (частично возвращается)
     /    \   ← Wave C: финальное движение
    /      \
```

| Волна | Тип | Характеристика |
|-------|------|----------------|
| **Wave A** | Коррекция | Первое движение против тренда; часто воспринимается как откат |
| **Wave B** | Импульс | Откат; может достигать 38.2–100% от Wave A |
| **Wave C** | Коррекция | Финальное движение; **обычно** = 100% Wave A или 161.8% от Wave A |

### Полный цикл (8 волн)

```
5 импульсных + 3 коррекционных = 8 волн
Затем начинается новый цикл более высокого порядка
```

---

## Фрактальность

EWP предполагает, что волновые паттерны **самоподобны** на всех масштабах:

```
Суперцикл (Supercycle)  — decades
    └── Цикл (Cycle)     — годы
        └── Первичный (Primary) — месяцы/годы
            └── Промежуточный (Intermediate) — недели/месяцы
                └── Малый (Minor) — дни/недели
                    └── Минутный (Minute) — часы
                        └── Микро (Micro) — минуты
```

Каждый уровень содержит **полный 8-волновой цикл** предыдущего уровня.

---

## Правила (Hard Rules) vs Руководства (Guidelines)

### ⚠️ Правила (нарушение = невалидный подсчёт)

| Правило | Описание |
|---------|---------|
| **Wave 2** | Не откатывается на 100%+ от Wave 1 |
| **Wave 3** | **Никогда** не бывает самой короткой импульсной волной (1, 3, 5) |
| **Wave 4** | **Никогда** не заходит в ценовую территорию Wave 1 |

### ✓ Руководства (типичные, но не обязательные)

| Руководство | Описание |
|-------------|---------|
| **Чередование** | Wave 2 и Wave 4 обычно чередуются по форме (sharp vs sideways) |
| **Растяжение** | Одна из волн 1–3–5 обычно растянута (обычно Wave 3) |
| **Откаты** | Wave 2: 50/61.8/78.6%; Wave 4: 38.2/50% |
| **Дивергенция** | Wave 5 часто показывает дивергенцию RSI с Wave 3 |

---

## Виды коррекций

### Zig-Zag (зигзаг)

```
     /\     /\     /\     
   /    \ /    \ /    \
  /      X      X      \
/              A         \
                     /\  B
                   /    \
                            \  C
```

- **3-волновая** структура (A-B-C)
- Wave A и C — импульсы
- Глубина: обычно **> 50%** от предыдущего импульса

### Flat (плоская)

```
        /\      /\      /\
       /  \    /  \    /  \
      /    \  /    \  /
     /      \/      \/
    /       A        \
                       B
                        /\  C
                      /    \
```

- **3-волновая** (A-B-C)
- B возвращается **близко к 100%** A
- C обычно **~ 100%** A

### Triangle (треугольник)

```
      /\      /\
     /  \    /  \
    /    \  /    \
   /      \/      \
  /      /\      /
 /      /  \    /
/      /    \  /
       консолидация
```

- **5-волновая** боковая коррекция
- Обычно предшествует финальной волне (Wave 5 или Wave C)
- Сходящийся (converging) — наиболее частый
- Расходящийся (expanding) — менее частый

---

## Применение в трейдинге

### Fib ratios в EWP

| Соотношение | Применение |
|------------|-----------|
| **61.8%** | Классический откат (Golden Ratio) |
| **78.6%** | Глубокий откат |
| **161.8%** | Растяжение волны 3 |
| **261.8%** | Экстремальное растяжение |
| **100%** | Equality rule (Wave C = Wave A) |

### Определение целей

1. **Fibonacci retracement** от Wave 1 → цели для Wave 2
2. **Fibonacci extension** от Wave 1–2 → цели для Wave 3
3. **Alternation** между Wave 2 и Wave 4 → предсказать глубину Wave 4
4. **Equality** (правило равенства) → Wave C ≈ Wave A

### Stop-loss

```
Stop-loss для LONG:
  • Под основанием Wave 2
  • Под началом Wave 1 ( нарушение = отмена сценария)
  • Под Wave 4 (если уже в Wave 5)
```

---

## В проекте AstroFinSentinelV5

- **Файл:** `agents/_impl/elliot_agent.py` (реализация на Python)
- **Вход:** price history, current wave count hypothesis
- **Выход:** `ElliotSignal {wave_count, pattern, targets, stop_loss, confidence}`
- **Интеграция:** вызывается как технический фильтр в `technical_agent` или standalone

```python
from agents._impl.elliot_agent import run_elliot_agent

result = run_elliot_agent(symbol="BTCUSDT", price_history=closes)
# result.wave_count  = "Wave 3 of (3) of Cycle"
# result.pattern      = "Impulse"
# result.targets      = [98000, 105000, 112000]
# result.stop_loss    = 84000
# result.confidence   = 74
```

---

## Изображения

![elliott-wave-patterns](./concepts/elliott-wave-patterns.png)
*Рис.1 — Elliott Wave паттерны: импульсные и коррективные волны с Fibonacci-соотношениями*

---

## Ключевые источники

### Книги

- **Prechter, Robert & Frost, A.J. *Elliott Wave Principle: Key to Market Behavior.* New Classics Library, 1978.** — **Primary source**[^1]
- Prechter, Robert. *Conquer the Crash: You Can Survive and Prosper in a Bear Market.* 2003.
- Prechter, Robert. *The Socionomic Theory of Finance.* 2007.
- Neelley, Brian. *Advanced Elliott Wave Analysis.* 2012.

### Архивы

- Elliott Wave International (EWI): elliottwave.com — самый большой архив волнового анализа
- arXiv: ElliottAgents paper (2024) — мультиагентная NLP-система на EWP[^2]

### Программное обеспечение

- **AstroFinSentinelV5:** `agents/_impl/elliot_agent.py` (Python implementation)

---

## Known Issues

| Проблема | Описание | Статус |
|----------|---------|--------|
| Субъективность | Два аналитика могут дать разный подсчёт | ⚠️ Принято — требуется опыт |
| Overfitting | EWP "подходит" к любому графику | ⚠️ Документировано как риск |
| Retroactive | Волновой подсчёт меняется при новых данных | ⚠️ Принято как свойство |

---

## TODO

- [ ] Добавить автоматический поиск волн через scipy.signal
- [ ] Интегрировать Fib ratios из технического модуля
- [ ] Сравнить результаты с Prechter's weekly forecasts

---

## Ссылки

- [[concepts/bradley_siderograph]] — альтернативный метод прогнозирования
- [[concepts/gann_theory]] — другой подход к временным циклам
- [[concepts/muhurta_trading]] — индийская астрологическая традиция трейдинга
- [[agents/elliot_agent]] — реализация в AstroFinSentinelV5

[^1]: https://www.elliottwave.com/contentv3/4/download?filename=Elliott-Wave-Principle-Key-to-Market-Behavior
[^2]: https://arxiv.org/html/2507.03435v1
