# Библиотека знаний ведической астрологии

## Обзор

Эта библиотека содержит структурированные знания ведической астрологии (Джйотиш) для использования в мультиагентной системе **AstroFin Sentinel**.

## Структура

```
knowledge/vedic/
├── muhurta_travel_rules.md     # Мухурта для путешествий
├── muhurta_marriage_rules.md   # Мухурта для брака (Виваха)
├── muhurta_business_rules.md   # Мухурта для бизнеса
├── muhurta_general_rules.md    # Общие правила и запреты
└── muhurta_rituals_sacred.md   # Ритуалы и санскары
```

## Использование

### 1. RAG (Retrieval-Augmented Generation)

Знания загружаются в RAG-базу для использования LLM агентами:

```python
from muhurta_search import MuhurtaSearcher

searcher = MuhurtaSearcher()
rules = searcher._get_rules_for_action("брак")
```

### 2. MuhurtaSpecialist Agent

Агент для поиска благоприятного времени:

```python
from agents._impl.muhurta import MuhurtaSpecialist

agent = MuhurtaSpecialist(lat=55.7558, lon=37.6173)
result = await agent.analyze({
    "action": "брак",
    "datetime": "2026-03-22T10:00:00",
    "days_ahead": 7
})
```

### 3. Интеграция с AstroCouncil

AstroCouncil автоматически определяет запросы на мухурту:

```python
from agents._impl.astro_council import AstroCouncilAgent

council = AstroCouncilAgent(lat=55.7558, lon=37.6173)

# Muhurta request - автоматически перенаправляется
result = await council.analyze({
    "action": "брак",
    "datetime": "2026-03-22T10:00:00"
})
```

## Теги

| Тег | Описание |
|-----|----------|
| `#мухурта` | Правила выбора времени |
| `#накшатра` | Информация о лунных созвездиях |
| `#йога` | Астрологические йоги |
| `#доша` | Неблагоприятные влияния |
| `#брак` | Правила для брака |
| `#путешествие` | Мухурта для путешествий |
| `#ритуал` | Ритуальные практики |
| `#расчёт` | Методы расчёта |
| `#планета` | Влияния планет |
| `#запрет` | Запрещённые периоды |

## Формат заметок (Zettelkasten)

Каждая заметка содержит:

- **Атомарное правило** — одно правило на заметку
- **Теги** — для категоризации
- **Внутренние ссылки** — `[[Связанная заметка]]`
- **Примеры** — практические применения

## Расширение библиотеки

1. Создайте новый файл в `knowledge/vedic/`
2. Добавьте frontmatter с тегами
3. Структурируйте по принципу: условие → результат
4. Добавьте внутренние ссылки на связанные темы

## Модули

### `muhurta_search.py`

```python
from muhurta_search import find_muhurta

windows = find_muhurta(
    date=datetime(2026, 3, 22),
    action="путешествие",
    lat=55.7558,
    lon=37.6173,
    days_ahead=7
)
```

### `panchanga_calculator.py`

Расширен с `suitable_activities`:

```python
from panchanga_calculator import get_nakshatra_suitable_activities

activities = get_nakshatra_suitable_activities("Rohini")
# {'recommended': ['брак', 'путешествие', ...], 'avoid': [...], 'description': '...'}
```

### `ashtakavarga_calculator.py`

Расширен с `interpretation` для каждого дома:

```python
from ashtakavarga_calculator import interpret_ashtakavarga_for_trading

result = interpret_ashtakavarga_for_trading(ashtakavarga)
# result['house_analysis']['House_1']['interpretation'] = "Strong personality..."
```

## AstroCouncil Agents

### MuhurtaSpecialist

**Назначение**: Поиск благоприятного времени для действий

**Инструменты**:
- `swiss_ephemeris` — точные астрологические расчёты
- `retrieve_knowledge` — RAG для правил из базы знаний

**Поддерживаемые действия**:
- `брак` / `свадьба` — поиск лучшего времени для бракосочетания
- `путешествие` — благоприятное время для поездок
- `бизнес` — начало деловых начинаний
- `ритуал` — проведение церемоний

### AstroCouncil

Автоматически определяет muhurta-запросы по ключевым словам:
- "благоприятное время"
- "когда лучше"
- "мухурта"
- "планирование"

## Запуск

```bash
# Тест MuhurtaSpecialist
cd /home/workspace/asurdev
python -m agents._impl.muhurta

# Тест AstroCouncil
python -m agents._impl.astro_council.agent

# CLI muhurta_search
python muhurta_search.py 2026-03-22 брак 55.7558 37.6173
```
