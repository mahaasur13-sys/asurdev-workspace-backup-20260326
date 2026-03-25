# Western Astrology Knowledge Base — Mankasi System

## Структура

```
knowledge/western/
├── README.md                          # Этот файл
└── mankasi/
    ├── Planetary_Forgers.md          # Планетарные кузнецы
    ├── Intercepted_Signs.md           # Перехваченные знаки
    ├── Essential_Dignities.md         # Essential Dignities
    ├── House_Strength_Algorithm.md   # 6-шаговый алгоритм
    ├── House_Classification.md        # Типы домов
    ├── Accidental_Dignities.md        # Акцидентальные достоинства
    ├── Planet_Strength_Analysis.md    # Полный анализ планеты
    ├── Muhurta_Western_Timing.md     # Западная мухурта
    └── House_System_Comparison.md     # Сравнение домных систем
```

## Использование

### RAG

```python
from rag import ObsidianKnowledgeBase

kb = ObsidianKnowledgeBase(
    vault_path="/home/workspace/asurdev/knowledge/western"
)
context = kb.get_context("planetary forger house analysis", max_length=1500)
```

### WesternHouseAnalyzer

```python
from western_house_analyzer import WesternHouseAnalyzer

analyzer = WesternHouseAnalyzer(is_day_chart=True)
result = analyzer.analyze_house(
    house=10,
    cusp_sign="Sagittarius",
    ruler="Jupiter",
    ruler_position={"sign": "Taurus", "degree": 15.2, "house": 4},
    planets_in_house=["Venus"]
)
```

### WesternAstrologer.interpret_houses()

```python
from western import WesternAstrologer

astrologer = WesternAstrologer()
ephemeris_data = {
    "positions": {"Sun": "Leo", "Moon": "Cancer", ...},
    "houses": {1: {"sign": "Aries"}, ...},
    "planets_in_signs": {"Aries": ["Mars"], ...}
}
result = astrologer.interpret_houses(ephemeris_data)
```

## Теги

| Тег | Описание |
|-----|----------|
| `#манкаси` | Система Майкла Манкаси |
| `#дома` | Дома гороскопа |
| `#диспозитор` | Диспозиторы и кузнецы |
| `#перехват` | Перехваченные знаки |
| `#сила` | Оценка силы |
| `#muhurta` | Выбор времени |
| `#западная` | Западная астрология |
| `#timing` | Timing для действий |

## Интеграция с AstroCouncil

AstroCouncil использует WesternAstrologer с расширенным interpret_houses():

```python
council = AstroCouncilAgent(lat=55.7558, lon=37.6173)
result = await council.analyze({"action": "house_analysis"})
# result.details["western_houses"] содержит анализ по Манкаси
```

## Тестирование

```bash
cd /home/workspace/asurdev
python3 -c "from western_house_analyzer import WesternHouseAnalyzer; ..."
```
