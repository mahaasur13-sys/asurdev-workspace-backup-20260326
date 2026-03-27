---
type:: method
id:: thompson_sampling
tags:: [method, agent-selection, bayesian, reinforcement-learning, _impl]
aliases:: [Thompson Sampling, Bayesian Agent Selection, Multi-Armed Bandit]
related:: [belief_tracker, volatility_engine, synthesis_agent]
created:: 2026-03-27
updated:: 2026-03-27
---

# Thompson Sampling

> Динамический отбор агентов на основе Bayesian Beta-распределения.
> Файл: `core/thompson.py`

## Концепция

Вместо статических весов (все агенты вызываются всегда) — **Thompson Sampling** выбирает лучших K агентов из каждого пула на каждом запуске, используя posterior Beta-распределение из belief tracker.

```
Агент i → Beta(α_i, β_i) → sample θ_i → выбираем top-K
```

**Почему:** exploration vs exploitation. Агент, который был слабым 10 сессий назад, мог "научиться" — нужно дать ему шанс.

---

## Пул агентов

### TECHNICAL_POOL

```
agents = ["MarketAnalyst", "BullResearcher", "BearResearcher", "TechnicalAgent"]
min_select = 2
max_select = 4
min_usefulness = 0.25
```

### MACRO_POOL

```
agents = ["FundamentalAgent", "MacroAgent", "QuantAgent", "OptionsFlowAgent", "SentimentAgent"]
min_select = 2
max_select = 4
min_usefulness = 0.30
```

### ASTRO_POOL

```
agents = ["GannAgent", "BradleyAgent", "ElliotAgent", "CycleAgent",
          "TimeWindowAgent", "MuhurtaAgent", "ElectionAgent"]
min_select = 4
max_select = 7
min_usefulness = 0.25
```

### ELECTORAL_POOL

```
agents = ["ElectionAgent", "MuhurtaAgent"]
min_select = 1
max_select = 2
min_usefulness = 0.20
```

---

## Алгоритм отбора

```
1. Для каждого агента i в пуле:
     belief = belief_tracker.get(agent_name)
     если belief.mean < min_usefulness:
         → исключить (низкая ожидаемая точность)
     иначе:
         α, β = belief.alpha, belief.beta
         θ_i = sample Beta(α, β)

2. Если ВСЕ исключены → fallback: Beta(1, 1) для всех

3. Сортируем по θ_i descending

4. Берём top-K (k = min(k, len(pool)))
   K = explicit_arg > pool.k > default_k(=4)

5. Return: [(agent_name, θ_i), ...] для выбранных
```

---

## Prior для Beta

| Состояние | Prior | Комментарий |
|-----------|-------|------------|
| **Seen agent** | Beta(α, β) из belief.db | Данные накоплены |
| **Unseen agent** | Beta(1 + bonus, 1) | bonus=0 → uniform, bonus=1 → оптимистичный |

**`exploration_bonus`** — гиперпараметр:

| bonus | Prior unseen | Эффект |
|-------|-------------|---------|
| 0.0 | Beta(1, 1) | Консервативный — невидимые редко выбираются |
| 1.0 | Beta(2, 1) | ~66% mean — умеренно exploratory |
| 2.0 | Beta(3, 1) | ~75% mean — агрессивно exploratory |

---

## Hyperparameters

### K — число агентов на пул

```
pool.k = None → sampler.default_k = 4
pool.k = 3    → всегда 3
select(pool, k=5) → явный override
```

### min_usefulness — порог отсечения

Агенты с `mean_accuracy < min_usefulness` **не участвуют** в сэмплировании (отфильтровываются).

### CONFIDENCE_THRESHOLD = 0.30

Глобальный fallback, если `pool.min_usefulness` не задан.

---

## Usage

```python
from core.thompson import (
    ThompsonSampler,
    AgentPool,
    TECHNICAL_POOL,
    ASTRO_POOL,
    thompson_select,
    get_thompson_sampler,
)

# Быстрый отбор
sampler = ThompsonSampler(exploration_bonus=0.0)
selected = sampler.select(TECHNICAL_POOL, k=3)
# [("QuantAgent", 0.72), ("MacroAgent", 0.65), ("SentimentAgent", 0.58)]

# Scores — для отладки
scores = sampler.scores(TECHNICAL_POOL)
# [(name, sample, belief_or_None, below_threshold), ...]

# С исключениями (не выбирать то, что уже в другом пуле)
selected = sampler.select_with_exclusions(
    ASTRO_POOL,
    excluded=["QuantAgent", "MacroAgent"],
    k=5,
)

# Module-level singleton
from core.thompson import thompson_select
selected = thompson_select(TECHNICAL_POOL)
```

---

## CLI Tool

```bash
python tools/thompson_cli.py scores --pool astro
python tools/thompson_cli.py select --pool astro --k 4
python tools/thompson_cli.py leaderboard
python tools/thompson_cli.py simulate --pool astro --k 4 --n 100 --seed 42
python tools/thompson_cli.py reset --agent QuantAgent
```

---

## Интеграция с оркестратором

```
sentinel_v5.py → ThompsonSampler.select(pool)
                           │
            ┌──────────────┼──────────────┐
            │ TECHNICAL_POOL│ MACRO_POOL   │
            │ ASTRO_POOL    │ELECTORAL_POOL│
            └──────────────┴──────────────┘
                           │
              Выбранные агенты → run_*_agent()
                           │
                           ▼
                    Synthesis Agent
```

---

## Интеграция с LangGraph

```python
from langgraph_schema import AgentState

# BeliefGuard вызывается внутри каждого node:
def _pool_decide(pool, k_override=None):
    for agent in pool.agents:
        belief = belief_tracker.get(agent_name)
        if belief and belief.mean < pool.min_usefulness:
            skip  # отфильтрован
        else:
            θ = sample Beta(α, β)
            eligible.append((name, θ))
    
    selected = sorted(eligible, key=lambda x: x[1], reverse=True)[:k]
    return (should_run, selected)
```

---

## Thompson vs Static Weights

| Аспект | Static AGENT_WEIGHTS | Thompson Sampling |
|--------|---------------------|------------------|
| **Selection** | Всегда все | Только top-K |
| **Exploration** | Нет | Невидимые агенты имеют шанс |
| **Exploitation** | 100% static | Bayesian posterior |
| **Determinism** | Полностью детерминирован | Стохастический (seedable) |

---

## Сравнение: bonus=1.0 vs bonus=0.0 (k=3, 50 runs)

| Agent | bonus=1.0 | bonus=0.0 |
|-------|-----------|-----------|
| FundamentalAgent | 60% | 44% |
| BullResearcher | 54% | 38% |
| OptionsFlowAgent | 46% | 26% |
| QuantAgent | 42% | 50% |
| SentimentAgent | 12% | 28% |

---

## Known Issues

| # | Описание | Статус |
|---|---------|--------|
| 1 | Agent pool names не синхронизированы с BeliefTracker._POOL_MAP | ⚠️ TODO: DRY |
| 2 | Нет cold-start стратегии — все unseen начинают с Beta(1,1) | 📋 Future |
| 3 | exploration_bonus не конфигурируется извне | 📋 Future |

---

## TODO

- [ ] Синхронизировать pool definitions с BeliefTracker._POOL_MAP
- [ ] Добавить cold-start стратегию (fab4-like epsilon-greedy)
- [ ] Конфиг для exploration_bonus и default_k

---

## См. также

- [[belief_tracker]] — Bayesian belief tracking
- [[volatility_engine]] — управление рисками
- [[synthesis_agent]] — финальный синтез
- [[agents_index]] — все агенты
