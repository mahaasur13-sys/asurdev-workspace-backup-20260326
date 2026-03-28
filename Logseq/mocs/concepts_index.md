---
type:: moc
id:: concepts_index
tags:: [moc, concepts, architecture, financial-astrology, knowledge-base]
created:: 2026-03-27
updated:: 2026-03-27
---

# Concepts Index

> Сводная карта всех концепций AstroFinSentinelV5. Каждая концепция — узел в графе знаний.

---

## Астрологические концепции (Core)

| Концепция | Файл | Описание |
|---------|------|---------|
| [[bradley_siderograph]] | `agents/_impl/bradley_agent.py` | Планетарный барометр — числовая модель астрологического влияния на рынки |
| [[gann_theory]] | `agents/_impl/gann_agent.py` | Геометрия цены-времени — углы, Квадрат Девяти, золотое сечение |
| [[muhurta_trading]] | `agents/_impl/electoral_agent.py` | Индийская традиция — Дивали, Samvat, благоприятные астрологические окна |
| [[ec_01_hubris_cap]] | ??? | ⚠️ **Pending clarification** — требуется уточнение |

---

## Волновые/Циклические теории

| Концепция | Файл | Описание |
|---------|------|---------|
| [[elliott_wave]] | `agents/_impl/elliot_agent.py` | Фрактальные 5-3 волновые паттерны; Prechter & Frost |
| [[gann_theory]] | `agents/_impl/gann_agent.py` | Временные циклы через углы и Квадрат Девяти |
| [[bradley_siderograph]] | `agents/_impl/bradley_agent.py` | Планетарные циклы (Юпитер=12 лет, Сатурн=29 лет) |

---

## Архитектурные концепции

| Концепция | Описание |
|---------|---------|
| [[concepts/roma_cycle]] | Meta-Orchestrator — итеративный цикл развития проекта |
| [[concepts/marti_mars2]] | Агент выбора инструментов |
| [[concepts/tool_use]] | Использование внешних инструментов агентами |
| [[concepts/zettelkasten]] | Zettelkasten-нотификация — база знаний в .md |

> Примечание: концепции ROMA, MARTI-MARS², Tool Use, Zettelkasten — из framework AI-Archi tect v7.x. Документация в `Skills/ai-architect-v71/`.

---

## Конфликтология (между концепциями)

| Конфликт | Правило | Файл |
|---------|--------|------|
| Astro vs Fundamental+Quant | Astro weight −30% | `synthesis_agent.py` |
| Bradley vs Gann | Нет приоритета — оба 3% | `AGENTS.md` |
| Elliott vs Bradley | Нет конфликта — разные входы | — |
| Muhurta vs VIX | Muhurta-фильтр применяется после Volatility | `electoral_agent.py` |

---

## Архитектурная карта концепций

```
┌─────────────────────────────────────────────────────────────┐
│              FINANCIAL ASTROLOGY CONCEPTS                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │ bradley_siderogr │────▶│   gann_theory    │              │
│  │  (planetary)     │     │ (price×time)     │              │
│  └────────┬─────────┘     └────────┬─────────┘              │
│           │                        │                        │
│           ▼                        ▼                        │
│  ┌──────────────────┐     ┌──────────────────┐              │
│  │ muhurta_trading  │     │  elliott_wave    │              │
│  │  (Vedic timing)  │     │  (fractals)      │              │
│  └──────────────────┘     └──────────────────┘              │
│                                                             │
│  ┌──────────────────┐                                       │
│  │  ec_01_hubris_   │   ⚠️ PENDING CLARIFICATION           │
│  │  cap              │                                       │
│  └──────────────────┘                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Граф связей

```
bradley_siderograph
    ├── calls: ephemeris_calculations
    ├── used_by: bradley_agent
    ├── related: elliott_wave (оба — циклические)
    └── related: gann_theory (оба — астрологические)

gann_theory
    ├── calls: ephemeris_calculations (для дат)
    ├── used_by: gann_agent
    ├── related: bradley_siderograph
    └── related: elliott_wave (оба — паттерны)

elliott_wave
    ├── used_by: elliot_agent
    ├── related: bradley_siderograph (оба — рыночные циклы)
    └── related: gann_theory (оба — прогноз разворотов)

muhurta_trading
    ├── used_by: electoral_agent
    ├── related: bradley_siderograph (оба — астрономия)
    └── related: time_window_agent (оба — временные окна)

ec_01_hubris_cap
    ├── used_by: synthesis_agent
    └── related: belief_tracker (оба — доверие/уверенность)
```

---

## Агенты и концепции

| Агент | Концепция | Вес |
|-------|---------|-----|
| [[agents/bradley_agent]] | [[bradley_siderograph]] | 3% |
| [[agents/gann_agent]] | [[gann_theory]] | 3% |
| [[agents/elliot_agent]] | [[elliott_wave]] | — |
| [[agents/electoral_agent]] | [[muhurta_trading]] | 3% |
| [[agents/time_window_agent]] | [[gann_theory]] + [[muhurta_trading]] | 2% |
| [[agents/synthesis_agent]] | [[ec_01_hubris_cap]] | 100% |

---

## Known Issues

| Концепция | Проблема | Приоритет |
|---------|---------|----------|
| ec_01_hubris_cap | Не найдена информация | 🔴 Высокий |
| elliott_wave | Нет полной реализации в агенте | 🟡 Средний |
| muhurta_trading | Время 2025+ (день) не адаптировано | 🟡 Средний |

---

## TODO

- [ ] ⚠️ Уточнить EC-01 Hubris Cap у пользователя
- [ ] Завершить `elliot_agent.py` (волновой подсчёт)
- [ ] Адаптировать `electoral_agent.py` для дневной Muhurta 2025+
- [ ] Добавить диаграмму связей между концепциями в виде Mermaid

---

## See Also

- [[mocs/agents_index]] — карта агентов
- [[mocs/methods_index]] — карта методов
- [[agents/astro_council_agent]] — координатор астро-агентов
- [[agents/synthesis_agent]] — финальный синтез сигналов

### Technical Analysis

| Концепция | Описание | Файлы |
|-----------|---------|--------|
| [[andrews-pitchfork]] | Вилы Эндрюса + 5 техник Микулы | `agents/technical_agent.py` |
| [[elliott-wave]] | Волновой принцип Эллиотта | `agents/_impl/elliot_agent.py` |
| [[market-cycles]] | Доминантные рыночные циклы | `agents/_impl/cycle_agent.py` |
| [[andrews-pitchfork]] | Медианная линия | `Logseq/concepts/andrews_pitchfork.md` |
| [[market_cycles]] | Рыночные циклы | `Logseq/concepts/market_cycles.md` |
| [[ec_01_hubris_cap]] | Hubris Cap | `Logseq/concepts/ec_01_hubris_cap.md` |

---

## 🏠 Astrology Systems

---

### Vedic Astrology (Muhurta/Panchanga)
| ID | Концепция | Файл |
|----|---------|------|
| [[concepts/muhurta]] | Muhurta — выбор момента | `Logseq/concepts/muhurta.md` |
| [[concepts/panchanga]] | Panchanga — 5 элементов | `Logseq/concepts/panchanga.md` |
| [[concepts/choghadiya]] | Choghadiya — периоды дня | `Logseq/concepts/choghadiya.md` |

## 🗄️ Databases
