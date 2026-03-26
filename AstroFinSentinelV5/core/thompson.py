"""
AstroFin Sentinel v5 — Thompson Sampling Agent Selector

Replaces static AGENT_WEIGHTS with dynamic selection based on
posterior Beta distribution from belief tracker.

At each orchestration step, for each candidate pool:
    - Filter agents with mean_accuracy < threshold (skip low-utility agents)
    - Sample θ_i ~ Beta(α_i, β_i) for remaining agents (from belief tracker)
    - Select top-K agents by sampled θ_i
    - Only selected agents are called

Unseen agents (no belief record) get uniform prior Beta(1, 1),
making them equally likely to be sampled.
"""

import random
from dataclasses import dataclass
from typing import Optional

import numpy as np

from core.belief import BeliefTracker, get_belief_tracker, BeliefState


# ─── Agent Pools per Flow ──────────────────────────────────────────────────────

@dataclass
class AgentPool:
    """Defines which agents participate in Thompson sampling for one orchestration step."""
    name: str
    agents: list[str]
    min_select: int = 1
    max_select: Optional[int] = None
    min_usefulness: float = 0.30
    k: Optional[int] = None
    description: str = ""


# ── Pool definitions ──────────────────────────────────────────────────────────

TECHNICAL_POOL = AgentPool(
    name="technical",
    agents=["MarketAnalyst", "BullResearcher", "BearResearcher", "TechnicalAgent"],
    min_select=2,
    max_select=4,
    min_usefulness=0.25,
    description="Чистый технический анализ и исследование рыночного направления",
)

MACRO_POOL = AgentPool(
    name="macro",
    agents=["FundamentalAgent", "MacroAgent", "QuantAgent", "OptionsFlowAgent", "SentimentAgent"],
    min_select=2,
    max_select=4,
    min_usefulness=0.30,
    description="Фундаментальный, макроэкономический и сентимент-анализ",
)

ASTRO_POOL = AgentPool(
    name="astro",
    agents=[
        # Классическая астрология
        "GannAgent",
        "BradleyAgent",
        "ElliotAgent",
        "CycleAgent",
        "TimeWindowAgent",
        # Ведическая астрология
        "MuhurtaAgent",
        # Элекционная астрология (root agents/)
        "ElectionAgent",
    ],
    min_select=4,
    max_select=7,
    min_usefulness=0.25,
    description="Астрологический пул: Gann, Bradley, Elliot Wave, Vedic Muhurta, Electoral",
)

ELECTORAL_POOL = AgentPool(
    name="electoral",
    agents=["ElectionAgent", "MuhurtaAgent"],
    min_select=1,
    max_select=2,
    min_usefulness=0.20,
    description="Элективный тайминг: выбор благоприятных моментов (мухурта + элекция)",
)

ALL_POOLS = [TECHNICAL_POOL, MACRO_POOL, ELECTORAL_POOL, ASTRO_POOL]


# ─── Thompson Sampler ─────────────────────────────────────────────────────────

class ThompsonSampler:
    """
    Thompson sampling selector using Beta distribution per agent.

    Each agent i has posterior Beta(α_i, β_i).
    At selection time: sample θ_i ~ Beta(α_i, β_i) for all agents,
    then select top-K agents by sampled θ_i.

    Agents whose mean_accuracy falls below min_usefulness threshold
    are excluded from the sampling pool (low expected utility).

    Unseen agents (no belief record) use Beta(1 + exploration_bonus, 1)
    by default, making them more likely to be sampled while still being
    conservative. Higher exploration_bonus → faster exploration.
    """

    CONFIDENCE_THRESHOLD = 0.30

    DEFAULT_PRIOR_ALPHA = 1.0
    DEFAULT_PRIOR_BETA  = 1.0

    def __init__(
        self,
        belief_tracker: Optional[BeliefTracker] = None,
        default_k: int = 4,
        random_seed: Optional[int] = None,
        min_usefulness: float = 0.30,
        exploration_bonus: float = 0.0,
    ):
        """
        Args:
            belief_tracker:     BeliefTracker instance (default: global singleton)
            default_k:          Default number of agents to select per pool
            random_seed:        Seed for reproducibility (None = random)
            min_usefulness:     Default threshold for mean_accuracy (overridden by pool.min_usefulness)
            exploration_bonus:   Added to alpha for unseen agents → Beta(1+bonus, 1).
                                 0.0 = uniform prior (conservative),
                                 1.0 = Beta(2, 1) slightly optimistic,
                                 2.0 = Beta(3, 1) more exploratory.
                                 Default: 0.0.
        """
        self.belief = belief_tracker or get_belief_tracker()
        self.default_k = default_k
        self.min_usefulness = min_usefulness
        self.exploration_bonus = exploration_bonus
        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)

    # ── Beta sampling ─────────────────────────────────────────────────────────

    def _sample_beta(self, alpha: float, beta: float) -> float:
        """Sample from Beta(alpha, beta) using NumPy."""
        return np.random.beta(alpha, beta)

    # ── Core selection ────────────────────────────────────────────────────────

    def select(
        self,
        pool: AgentPool,
        k: Optional[int] = None,
    ) -> list[tuple[str, float]]:
        """
        Thompson sampling selection for one agent pool.

        Args:
            pool: AgentPool defining candidates and constraints
            k:    Number of agents to select.
                  Resolved in order: k argument > pool.k > self.default_k

        Returns:
            List of (agent_name, sample_value) for selected agents,
            sorted descending by sample value.
        """
        threshold = pool.min_usefulness if pool.min_usefulness else self.min_usefulness

        # Resolve K: explicit arg > pool.k > default_k
        if k is None:
            k = pool.k if pool.k is not None else self.default_k

        k = min(k, len(pool.agents))
        k = max(k, pool.min_select)

        # Step 1: Separate eligible vs. below-threshold agents
        eligible: list[tuple[str, float, Optional[BeliefState]]] = []
        below_threshold: list[str] = []

        for agent_name in pool.agents:
            belief = self.belief.get(agent_name)
            if belief is not None:
                mean_acc = belief.mean
                if mean_acc < threshold:
                    below_threshold.append(agent_name)
                    continue
                alpha, beta = belief.alpha, belief.beta
            else:
                # Unseen agents — apply exploration_bonus to alpha
                # Beta(1 + bonus, 1): bonus=0 → uniform Beta(1,1)
                # bonus=1 → optimistic Beta(2,1); bonus=2 → Beta(3,1)
                alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                beta  = self.DEFAULT_PRIOR_BETA

            sample = self._sample_beta(alpha, beta)
            eligible.append((agent_name, sample, belief))

        # If ALL agents are below threshold, fall back to all (still need agents)
        if not eligible:
            eligible = []
            for agent_name in pool.agents:
                belief = self.belief.get(agent_name)
                if belief is not None:
                    alpha, beta = belief.alpha, belief.beta
                else:
                    alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                    beta  = self.DEFAULT_PRIOR_BETA
                sample = self._sample_beta(alpha, beta)
                eligible.append((agent_name, sample, belief))
            below_threshold = []

        eligible.sort(key=lambda x: x[1], reverse=True)
        selected = eligible[:k]

        if below_threshold:
            names = [a for a, _, _ in eligible[:k]]
            print(f"[Thompson] '{pool.name}' — filtered out (low utility): {below_threshold} | selected: {names}")

        return [(name, score) for name, score, _ in selected]

    def select_with_exclusions(
        self,
        pool: AgentPool,
        excluded: list[str],
        k: Optional[int] = None,
    ) -> list[tuple[str, float]]:
        """Like select() but excludes specified agents (e.g. already selected in another flow)."""
        candidates = [a for a in pool.agents if a not in excluded]
        if not candidates:
            return []

        tmp_pool = AgentPool(
            name=pool.name,
            agents=candidates,
            min_select=pool.min_select,
            max_select=pool.max_select,
            min_usefulness=pool.min_usefulness,
        )
        return self.select(tmp_pool, k=k)

    def scores(
        self,
        pool: AgentPool,
    ) -> list[tuple[str, float, Optional[BeliefState], bool]]:
        """
        Return all agents with their sampled scores and threshold flag (for logging/debugging).

        Returns:
            List of (agent_name, sample, belief, below_threshold)
        """
        threshold = pool.min_usefulness if pool.min_usefulness else self.min_usefulness
        result = []
        for agent_name in pool.agents:
            belief = self.belief.get(agent_name)
            if belief is not None:
                alpha, beta = belief.alpha, belief.beta
                below = belief.mean < threshold
            else:
                alpha = self.DEFAULT_PRIOR_ALPHA + self.exploration_bonus
                beta  = self.DEFAULT_PRIOR_BETA
                below = False

            sample = self._sample_beta(alpha, beta)
            result.append((agent_name, sample, belief, below))
        result.sort(key=lambda x: x[1], reverse=True)
        return result


# ─── Module-level singleton ───────────────────────────────────────────────────

_sampler: Optional[ThompsonSampler] = None


def get_thompson_sampler() -> ThompsonSampler:
    global _sampler
    if _sampler is None:
        _sampler = ThompsonSampler()
    return _sampler


def thompson_select(
    pool: AgentPool,
    k: Optional[int] = None,
) -> list[tuple[str, float]]:
    return get_thompson_sampler().select(pool, k=k)


def thompson_scores(
    pool: AgentPool,
) -> list[tuple[str, float, Optional[BeliefState]]]:
    return [(a, s, b) for a, s, b, _ in get_thompson_sampler().scores(pool)]
