---
type:: concept
id:: ec_01_hubris_cap
tags:: [concept, signal, confidence, _pending]
aliases:: [EC-01, Hubris Cap, Hubris Limit]
created:: 2026-03-27
updated:: 2026-03-27
related:: [[agents/synthesis_agent], [methods/belief_tracker]]
---

# EC-01: Hubris Cap (待澄清 / Pending Clarification)

## ⚠️ Информация не найдена

**Статус:** Требуется уточнение у пользователя.

---

## Что известно

На основе анализа кодовой базы и документации проекта:

- **EC-01** — код правила/сигнала, найден в `synthesis_agent.py` (EC = Error Correction?)
- **Hubris Cap** — "ограничение высокомерия" модели (overconfidence)
- Связан с **confidence score** агентов и ограничением максимальной уверенности

---

## Гипотеза

```
EC-01 (Hubris Cap):
  IF agent_confidence > 90% THEN confidence = 90%
  Reasoning: не бывает 100% уверенности в трейдинге
```

В коде: **EC-01** может быть правилом:
- **EC-01 (Hubris Cap):** максимальная уверенность = 90% (cap)
- **EC-02:** может быть другим корректирующим правилом

---

## Вопросы к пользователю

### 1. Что означает EC-01?

EC = Error Correction? Error Cap? Electional Constraint?

### 2. Как работает Hubris Cap?

Это:
- [ ] Ограничение максимальной уверенности (cap)?
- [ ] Снижение уверенности при противоречивых сигналах?
- [ ] Фильтр при превышении определённого threshold?

### 3. Формула

Есть ли числовая формула? Например:

```
HubrisCap(confidence) = min(confidence, 90)
```

### 4. Где используется?

В каком файле/агенте? Связан ли с `synthesis_agent`?

### 5. Пример

Есть ли пример вход→выход?

---

## Ожидаемый ответ

```
EC-01 = [расшифровка]
Hubris Cap = [формула или описание]
Используется в: [файл/функция]
```

---

## Шаблон после уточнения

```markdown
## Определение
[Что такое EC-01 Hubris Cap]

## Формула
[Математическое определение]

## Применение в AstroFinSentinelV5
[Где используется]

## Код
```python
# [реализация]
```

## Связи
- [[agents/synthesis_agent]]
- [[methods/belief_tracker]]
```

---

## ✅ Ответ пользователя (2026-03-27)

**EC-01 = Error Cap** — динамический ограничитель уверенности агента.

**Механизм:**
- Агент с >20 сессий, но mean_accuracy < 0.55 → система снижает его confidence на 5–15%
- Цель: не дать «переобученным» агентам доминировать
- Файл: `core/belief.py` (planned)

**Статус реализации:** ⚠️ Not implemented — концепт есть, кода нет

**TODO:**
- [ ] Реализовать `BeliefTracker.get_agent_confidence_cap()` в `core/belief.py`
- [ ] Интегрировать в `TradingSignal.from_agents()`
- [ ] Добавить тесты

## Источники
[^1]: Гипотеза автора (2026-03-27)
