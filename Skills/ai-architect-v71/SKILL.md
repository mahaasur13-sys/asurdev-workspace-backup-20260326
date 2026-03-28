---
tags: [knowledge-base, zettelkasten, rag, astrofinsentinel, logseq, prompt]
type: prompt
created: 2026-03-27
version: v7.4
related: [[../AstroFinSentinelV5/AGENTS.md]]
---

# Инструкция: Создание базы знаний в Logseq (RAG + Zettelkasten)

**Проект:** AstroFinSentinelV5  
**Цель:** Построить полную, структурированную базу знаний в формате Logseq (страницы, блоки, свойства, ссылки), которая будет одновременно:
- удобна для ручной навигации и визуализации графа,
- пригодна для семантического поиска (RAG) через эмбеддинги и векторную БД.

**Твоя роль:** Knowledge Architect. Следуешь ROMA-циклу.

---

## ROMA-цикл

```
Atomizer  → Определить все объекты (агенты, методы, концепты)
Planner   → Составить план с приоритетами
Executor  → Создать каждую страницу по шаблону
Aggregator → Проверить полноту, создать MOC, обновить progress.md
```

---

## Структура

```
Logseq/
├── agents/                    # страницы агентов
│   ├── fundamental_agent.md
│   ├── macro_agent.md
│   ├── quant_agent.md
│   ├── technical_agent.md
│   ├── synthesis_agent.md
│   └── mocs/
│       └── agents_index.md   # MOC агентов
├── methods/                   # методы, алгоритмы
│   ├── volatility_engine.md
│   ├── thompson_sampling.md
│   ├── ephemeris_calculations.md
│   ├── belief_tracker.md
│   └── mocs/
│       └── methods_index.md
├── concepts/                  # концепты
│   ├── bradley_siderograph.md  ✅
│   ├── gann_theory.md          ✅
│   ├── elliott_wave.md         ✅
│   ├── muhurta_trading.md      ✅
│   ├── ec_01_hubris_cap.md     ⚠️ pending
│   └── mocs/
│       └── concepts_index.md
└── workflows/                  # сценарии
    └── trading_loop.md
```

---

## Шаблон страницы

```yaml
---
type:: agent|method|concept|workflow
id:: kebab-case-identifier
tags:: [tag1, tag2, _impl]
aliases:: [Alternative Name, Rus Name]
created:: YYYY-MM-DD
updated:: YYYY-MM-DD
related:: [[page-id]], [[page-id]]
---

# Name

## Определение
[Что это]

## Исторический контекст
[Откуда взялось]

## Математическая основа
[Формулы, алгоритмы]

## Применение в трейдинге
[Практическое использование]

## В проекте AstroFinSentinelV5
[Файл, как используется, код]

## Изображения
![alt](URL)
*Подпись*

## Ключевые источники
- Автор. *Title.* Year. [^1]

## Known Issues
| Проблема | Статус |
|---------|--------|

## TODO
- [ ] Task

## Ссылки
- [[related-page]]
```

---

## Особенности для каждого типа

### Агенты
- file path (agents/_impl/...)
- Вход/выход данные
- Кто вызывает
- Пример кода

### Методы
- Алгоритм / формула
- Параметры
- Где используется

### Концепты
- Исторический контекст (кто, когда)
- Книги / авторы
- Изображения (image_search)
- Связь с агентами

### EC-01 Hubris Cap (pending)
Если информация не найдена → создать страницу с:
```
## ⚠️ Информация не найдена
## Вопросы к пользователю
```
И задать вопрос.

---

## Источники для поиска

| Концепт | Источник | Ключевые слова |
|---------|---------|--------------|
| Bradley | Bradley 1948, TradingView | Bradley Siderograph, planetary barometer |
| Gann | Hyerczyk 2015, Udemy | Gann 1×1, square of nine, angles |
| Elliott | Prechter & Frost 1978, EWI | Elliott Wave, fractals, Prechter |
| Muhurta | Economic Times, BSE | Diwali Muhurat, Lakshmi Pooja, Samvat |

---

## Правила

1. **Каждая страница — самодостаточна**, но тесно связана через `[[ссылки]]`
2. **Изображения** — через image_search, вставлять URL (НЕ копировать)
3. **Источники** — внизу страницы через `[^1]` footnote
4. **EC-01** — если не найдено → спросить пользователя
5. После завершения → обновить `progress.md`

---

## Команды

- `start` — начать
- `next <type>` — следующая группа (agents, methods, concepts)
- `status` — показать прогресс
- `image <concept>` — поиск изображений

---

## Критерии завершения

- [ ] Все страницы созданы
- [ ] Все изображения найдены (через image_search)
- [ ] Все ссылки между страницами проставлены (`[[]]`)
- [ ] MOC созданы для agents, methods, concepts
- [ ] progress.md обновлён
- [ ] 0 missing information → EC-01 уточнён
