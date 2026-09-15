"""
End-to-end correctness check: does this project's P3 actually behave like
P3 on a problem where the answer is known?

Problem: m concatenated, deceptive, k-ary trap blocks on a categorical
genotype (alphabet {0,1,2}), block variables interleaved through a fixed
random permutation. Per block, with u zeros and v ones among its k
variables:

    score = k                         if u == k   (global optimum: block all 0)
    score = (k - 1 - u) + 0.25 * v/k  otherwise    (deceptive: pulls toward all 1)

Single-variable moves always lead away from the optimum, so a structure-blind
hill climber converges to all-1 blocks (score k - 0.75), and only a method
that changes a whole block at once reaches the optimum. The global optimum
is the all-zero genotype, known in advance.

PRE-REGISTERED CRITERIA (fixed before the first run, 2026-09-14):
  P3 canonical (canonical_pyramid.climb: FIHC + GOM up the pyramid, real
  evaluations)            -> optimum within budget in >= 8/10 seeds
  uniform random search   -> optimum in <= 1/10 seeds
  FIHC with random restarts -> optimum in <= 1/10 seeds
  P3Net default and P3Net cascade=True -> DIAGNOSTIC ONLY, no threshold:
  their surrogate is additive and a deceptive trap is non-additive by
  construction, and their budget is necessarily far smaller (surrogate refit
  cost). Reported as measured.
Only the evaluation budget may be adjusted, and only for runtime reasons,
never after looking at success counts.

Writes results/checks/p3_trap_correctness.md.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from p3net.harness.runner import Runner  # noqa: E402
from p3net.methods.p3net import P3Net  # noqa: E402
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace  # noqa: E402
from p3net.search_engines.p3.canonical_pyramid import (  # noqa: E402
    CanonicalPyramid,
    _first_improvement_hill_climb,
    climb,
)
from sklearn.linear_model import RidgeCV  # noqa: E402

OUT = EXPERIMENTS_ROOT / "results" / "checks" / "p3_trap_correctness.md"


class BudgetReached(Exception):
    pass


@dataclass
class TrapProblem:
    blocks: int
    block_len: int
    permutation_seed: int = 12345

    def __post_init__(self) -> None:
        n = self.blocks * self.block_len
        positions = list(range(n))
        random.Random(self.permutation_seed).shuffle(positions)
        self.true_blocks = [
            positions[b * self.block_len : (b + 1) * self.block_len] for b in range(self.blocks)
        ]
        self.space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * n)
        self.optimum_score = float(self.blocks * self.block_len)

    def score(self, genotype: Genotype) -> float:
        total = 0.0
        k = self.block_len
        for block in self.true_blocks:
            values = [genotype.values[i] for i in block]
            u = values.count(0)
            v = values.count(1)
            total += k if u == k else (k - 1 - u) + 0.25 * v / k
        return total


class Counter:
    """Counts every objective call; stops the search at the budget or as soon
    as the optimum has been evaluated."""

    def __init__(self, problem: TrapProblem, budget: int) -> None:
        self.problem = problem
        self.budget = budget
        self.calls = 0
        self.best = float("-inf")
        self.hit_at: int | None = None

    def __call__(self, genotype: Genotype):
        if self.calls >= self.budget:
            raise BudgetReached
        self.calls += 1
        s = self.problem.score(genotype)
        self.best = max(self.best, s)
        if s >= self.problem.optimum_score and self.hit_at is None:
            self.hit_at = self.calls
            raise BudgetReached
        return (-s,)


def run_canonical_p3(problem: TrapProblem, budget: int, seed: int) -> Counter:
    rng = random.Random(seed)
    counter = Counter(problem, budget)
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    try:
        while True:
            climb(
                problem.space.sample_uniform(rng),
                pyramid,
                search_space=problem.space,
                fitness_fn=counter,
                rng=rng,
            )
    except BudgetReached:
        pass
    return counter


def run_random(problem: TrapProblem, budget: int, seed: int) -> Counter:
    rng = random.Random(seed)
    counter = Counter(problem, budget)
    try:
        while True:
            counter(problem.space.sample_uniform(rng))
    except BudgetReached:
        pass
    return counter


def run_fihc_restarts(problem: TrapProblem, budget: int, seed: int) -> Counter:
    rng = random.Random(seed)
    counter = Counter(problem, budget)
    try:
        while True:
            _first_improvement_hill_climb(
                problem.space.sample_uniform(rng), problem.space, counter, rng
            )
    except BudgetReached:
        pass
    return counter


def run_p3net(problem: TrapProblem, budget: int, seed: int, *, cascade: bool) -> Counter:
    counter = Counter(problem, budget)
    method = P3Net(
        search_space=problem.space,
        validity=lambda g: -1.0,
        model_factory=RidgeCV,
        rng=random.Random(seed),
        cascade=cascade,
    )

    def objective(genotype: Genotype):
        return (counter(genotype)[0], 0.0)

    try:
        Runner(objective=objective, budget=budget + 1).run(method)
    except BudgetReached:
        pass
    return counter


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument(
        "--first-seed", type=int, default=1, help="runtime calibration uses seeds outside 1..10"
    )
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--budget", type=int, default=50_000)
    parser.add_argument("--p3net-budget", type=int, default=2_000)
    parser.add_argument("--blocks", type=int, default=5)
    parser.add_argument("--block-len", type=int, default=4)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args(argv)

    problem = TrapProblem(blocks=args.blocks, block_len=args.block_len)
    arms = {
        "p3_canonical": (
            lambda s: run_canonical_p3(problem, args.budget, s),
            args.budget,
            ">= 8/10",
        ),
        "random_search": (lambda s: run_random(problem, args.budget, s), args.budget, "<= 1/10"),
        "fihc_restarts": (
            lambda s: run_fihc_restarts(problem, args.budget, s),
            args.budget,
            "<= 1/10",
        ),
        "p3net_default": (
            lambda s: run_p3net(problem, args.p3net_budget, s, cascade=False),
            args.p3net_budget,
            "diagnostic",
        ),
        "p3net_cascade": (
            lambda s: run_p3net(problem, args.p3net_budget, s, cascade=True),
            args.p3net_budget,
            "diagnostic",
        ),
    }
    if args.only:
        arms = {k: v for k, v in arms.items() if k in args.only}

    rows = []
    for name, (runner, budget, criterion) in arms.items():
        hits, evals_to_hit, bests = 0, [], []
        started = time.monotonic()
        for seed in range(args.first_seed, args.first_seed + args.seeds):
            c = runner(seed)
            bests.append(c.best)
            if c.hit_at is not None:
                hits += 1
                evals_to_hit.append(c.hit_at)
            print(
                f"{name} seed {seed}: best {c.best:.2f}/{problem.optimum_score:.0f} "
                f"{'HIT at ' + str(c.hit_at) if c.hit_at else 'miss'} ({c.calls} evals)",
                flush=True,
            )
        seconds = time.monotonic() - started
        median_hit = statistics.median(evals_to_hit) if evals_to_hit else None
        rows.append(
            (
                name,
                budget,
                criterion,
                hits,
                args.seeds,
                median_hit,
                statistics.median(bests),
                seconds,
            )
        )

    lines = [
        "# P3 correctness on concatenated deceptive k-ary traps",
        "",
        f"m={args.blocks} blocks, k={args.block_len}, alphabet {{0,1,2}}, n={args.blocks * args.block_len}, "  # noqa: E501
        f"variables interleaved (permutation seed {problem.permutation_seed}); optimum score {problem.optimum_score:.0f}, "  # noqa: E501
        f"score of the all-deceptive local optimum {args.blocks * (args.block_len - 0.75):.2f}.",
        "Criteria were fixed before the first run (see scripts/p3_trap_correctness.py).",
        "",
        "| Arm | Budget | Pre-registered criterion | Optimum found | Median evals to optimum | Median best score | Wall-clock s |",  # noqa: E501
        "|---|---|---|---|---|---|---|",
    ]
    for name, budget, criterion, hits, n, median_hit, median_best, seconds in rows:
        lines.append(
            f"| {name} | {budget} | {criterion} | {hits}/{n} | "
            f"{'--' if median_hit is None else f'{median_hit:.0f}'} | {median_best:.2f} | {seconds:.0f} |"  # noqa: E501
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
