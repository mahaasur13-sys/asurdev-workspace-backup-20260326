#!/usr/bin/env python3
"""
Thompson Sampling CLI — test and inspect agent selection.

Usage:
    python tools/thompson_cli.py scores --pool astro        # show all agents + sampled scores
    python tools/thompson_cli.py select --pool astro --k 4  # select top-K
    python tools/thompson_cli.py leaderboard                # belief leaderboard
    python tools/thompson_cli.py simulate --pool astro --k 4 --n 100  # simulate N runs
    python tools/thompson_cli.py reset                      # reset all beliefs
"""

import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.thompson import (
    ThompsonSampler,
    AgentPool,
    TECHNICAL_POOL,
    ELECTORAL_POOL,
    ASTRO_POOL,
    get_thompson_sampler,
)
from core.belief import get_belief_tracker


POOL_MAP = {
    "technical": TECHNICAL_POOL,
    "astro": ASTRO_POOL,
    "electoral": ELECTORAL_POOL,
    "all": None,
}


def cmd_scores(args):
    sampler = ThompsonSampler(
        random_seed=args.seed,
        exploration_bonus=args.exploration_bonus,
    )
    pool = POOL_MAP[args.pool]
    results = sampler.scores(pool)

    print(f"\n=== Thompson Scores: {pool.name.upper()} ===")
    print(f"exploration_bonus={args.exploration_bonus}  k={pool.k or sampler.default_k}")
    print(f"{'Agent':<22} {'Sample':>8}  {'Alpha':>6}  {'Beta':>6}  {'Mean':>7}  Sessions")
    print("-" * 65)

    for name, score, belief in results:
        if belief:
            print(
                f"  {name:<20} {score:>8.4f}  "
                f"{belief.alpha:>6.2f}  {belief.beta:>6.2f}  "
                f"{belief.mean:>7.4f}  {belief.total_sessions}"
            )
        else:
            bonus_note = f"+{args.exploration_bonus:.1f}" if args.exploration_bonus else ""
            print(f"  {name:<20} {score:>8.4f}  (unseen, Beta(1{bonus_note},1))")


def cmd_select(args):
    sampler = ThompsonSampler(exploration_bonus=args.exploration_bonus)
    pool = POOL_MAP[args.pool]
    # k resolved: explicit --k > pool.k > default_k(=4)
    k = args.k if args.k is not None else (pool.k if pool.k is not None else sampler.default_k)
    selected = sampler.select(pool, k=k)

    print(f"\n=== Thompson Selected ({pool.name.upper()}, k={k}) ===")
    for rank, (name, score) in enumerate(selected, 1):
        print(f"  {rank}. {name:<22} score={score:.4f}")


def cmd_leaderboard(args):
    tracker = get_belief_tracker()
    rows = tracker.leaderboard()

    if not rows:
        print("\nNo belief data yet. Run some sessions first.\n")
        return

    print(f"\n{'=== Belief Leaderboard (Beta Posterior) ===':^60}")
    print(f"{'Rank':<5} {'Agent':<22} {'Mean':>7}  {'CI 95%':>14}  {'Sessions':>9}  {'α':>5}  {'β':>5}")
    print("-" * 72)

    for rank, row in enumerate(rows, 1):
        ci = row["ci_95"]
        print(
            f"  {rank:<3} {row['agent_name']:<22} {row['mean_accuracy']:>7.4f}  "
            f"[{ci[0]:.3f}, {ci[1]:.3f}]  {row['total_sessions']:>9}  "
            f"{row['alpha']:>5.1f}  {row['beta']:>5.1f}"
        )


def cmd_simulate(args):
    """Simulate N Thompson sampling runs and show selection frequency."""
    pool = POOL_MAP[args.pool]
    counts = {name: 0 for name in pool.agents}
    k = args.k if args.k is not None else (pool.k if pool.k is not None else 4)

    sampler = ThompsonSampler(
        random_seed=args.seed,
        exploration_bonus=args.exploration_bonus,
    )

    for i in range(args.n):
        selected = sampler.select(pool, k=k)
        for name, _ in selected:
            counts[name] += 1

    print(f"\n=== Simulation: {args.n} runs, k={k}, pool={pool.name}, exploration_bonus={args.exploration_bonus} ===")
    print(f"Random seed: {args.seed or 'random'}")
    print(f"\n{'Agent':<22} {'Selected':>10}  {'Frequency':>10}")
    print("-" * 45)
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    for name, count in sorted_counts:
        pct = count / args.n * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {name:<20} {count:>10}  [{bar}] {pct:>5.1f}%")


def cmd_reset(args):
    tracker = get_belief_tracker()
    if args.agent:
        deleted = tracker.reset(args.agent)
        print(f"Reset {deleted} record(s) for '{args.agent}'")
    else:
        deleted = tracker.reset()
        print(f"Reset all {deleted} belief record(s)")


def main():
    parser = argparse.ArgumentParser(description="Thompson Sampling CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_scores = sub.add_parser("scores", help="Show sampled scores for all agents in pool")
    p_scores.add_argument("--pool", choices=["technical", "astro", "electoral"], default="astro")
    p_scores.add_argument("--seed", type=int, default=None)
    p_scores.add_argument("--exploration-bonus", type=float, default=0.0,
                          help="Bonus added to alpha for unseen agents: Beta(1+bonus, 1). Default: 0.0")

    p_select = sub.add_parser("select", help="Run Thompson selection")
    p_select.add_argument("--pool", choices=["technical", "astro", "electoral"], default="astro")
    p_select.add_argument("--k", type=int, default=None, help="Agents to select (default: pool.k or 4)")
    p_select.add_argument("--seed", type=int, default=None)
    p_select.add_argument("--exploration-bonus", type=float, default=0.0,
                          help="Bonus added to alpha for unseen agents: Beta(1+bonus, 1). Default: 0.0")

    sub.add_parser("leaderboard", help="Show belief leaderboard")

    p_sim = sub.add_parser("simulate", help="Simulate N runs")
    p_sim.add_argument("--pool", choices=["technical", "astro", "electoral"], default="astro")
    p_sim.add_argument("--k", type=int, default=None, help="Agents to select per run (default: pool.k or 4)")
    p_sim.add_argument("--n", type=int, default=100)
    p_sim.add_argument("--seed", type=int, default=42)
    p_sim.add_argument("--exploration-bonus", type=float, default=0.0,
                          help="Bonus added to alpha for unseen agents: Beta(1+bonus, 1). Default: 0.0")

    p_reset = sub.add_parser("reset", help="Reset belief tracker")
    p_reset.add_argument("--agent", type=str, default=None, help="Reset one agent (default: all)")

    args = parser.parse_args()

    if args.cmd == "scores":
        cmd_scores(args)
    elif args.cmd == "select":
        cmd_select(args)
    elif args.cmd == "leaderboard":
        cmd_leaderboard(args)
    elif args.cmd == "simulate":
        cmd_simulate(args)
    elif args.cmd == "reset":
        cmd_reset(args)


if __name__ == "__main__":
    main()
