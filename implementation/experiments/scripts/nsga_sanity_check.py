"""
Sanity check of this project's NSGA-Net baseline against an independent
NSGA-II implementation (optuna.samplers.NSGAIISampler).

NSGA-Net is the engine-only NSGA-II arm every P3 result is compared with, and
it is implemented in-house (methods/nsga_net.py). If it were materially weaker
than a standard NSGA-II, every "P3 vs NSGA-II" statement in the paper would be
against a straw man. Known deviation going in: methods/nsga_net.py draws
parents uniformly at random (rng.sample), not by crowded binary tournament as
canonical NSGA-II does; survivor selection is standard NSGA-II.

Both arms: population 20, uniform crossover always applied (swap prob 0.5),
per-variable mutation probability 0.1, same budget of UNIQUE evaluations
(duplicates are answered from a cache and not charged, matching the project
harness).

Problems (categorical, alphabet {0,1,2}, n = 20, both minimised, exact front known):
  linear : f1 = n - #zeros,          f2 = n - #twos
  lotz   : f1 = n - leading zeros,   f2 = n - trailing twos

PRE-REGISTERED CRITERION (fixed before the first run, 2026-09-14):
  On both problems, the median final hypervolume (normalised by the exact
  front's) of NSGA-Net is within 5% relative of optuna NSGA-II's, and both
  medians exceed uniform random search's. Mann-Whitney U p-values are
  reported for information only.

Writes results/checks/nsga_sanity_check.md.
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

import optuna  # noqa: E402
from p3net.harness.runner import Runner  # noqa: E402
from p3net.metrics.hypervolume import hypervolume  # noqa: E402
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace  # noqa: E402
from p3net.problem.objectives import pareto_front  # noqa: E402
from scipy.stats import mannwhitneyu  # noqa: E402

from methods.nsga_net import NSGANet  # noqa: E402
from methods.random_search import RandomSearch  # noqa: E402

OUT = EXPERIMENTS_ROOT / "results" / "checks" / "nsga_sanity_check.md"
N = 20
ALPHABET = (0, 1, 2)
SPACE = SearchSpace(domains=(CategoricalDomain(values=ALPHABET),) * N)
REFERENCE = (N + 1.0, N + 1.0)


def linear(g: Genotype):
    return (float(N - g.values.count(0)), float(N - g.values.count(2)))


def lotz(g: Genotype):
    lead = 0
    for v in g.values:
        if v != 0:
            break
        lead += 1
    trail = 0
    for v in reversed(g.values):
        if v != 2:
            break
        trail += 1
    return (float(N - lead), float(N - trail))


def exact_front(problem):
    if problem is linear:
        return [(float(N - a), float(a)) for a in range(N + 1)]
    return [(float(N - i), float(i)) for i in range(N + 1)]


def normalised_hv(points, problem) -> float:
    front = pareto_front(list(points), lambda p: p)
    return hypervolume(front, REFERENCE) / hypervolume(exact_front(problem), REFERENCE)


def run_project_method(method_cls, problem, budget, seed, **params) -> float:
    method = method_cls(
        search_space=SPACE, validity=lambda g: -1.0, rng=random.Random(seed), **params
    )
    state = Runner(objective=problem, budget=budget).run(method)
    return normalised_hv([o.objectives for o in state.history], problem)


def run_optuna_nsga2(problem, budget, seed) -> float:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.NSGAIISampler(
        population_size=20, mutation_prob=0.1, crossover_prob=1.0, swapping_prob=0.5, seed=seed
    )
    study = optuna.create_study(directions=["minimize", "minimize"], sampler=sampler)
    seen: dict[tuple, tuple[float, float]] = {}
    max_trials = budget * 50
    trials = 0
    while len(seen) < budget and trials < max_trials:
        trials += 1
        trial = study.ask()
        values = tuple(trial.suggest_categorical(f"x{i}", list(ALPHABET)) for i in range(N))
        if values not in seen:
            seen[values] = problem(Genotype(values=values))
        study.tell(trial, list(seen[values]))
    return normalised_hv(seen.values(), problem)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--seeds", type=int, default=10)
    parser.add_argument("--budget", type=int, default=1000)
    args = parser.parse_args(argv)

    lines = [
        "# NSGA-Net vs. optuna NSGA-II sanity check",
        "",
        f"n={N}, alphabet {{0,1,2}}, budget {args.budget} unique evaluations, {args.seeds} seeds. "
        "Hypervolume normalised by the exact front's. Criterion fixed before the first run: "
        "NSGA-Net median within 5% of optuna NSGA-II, both above random search.",
        "",
        "| Problem | NSGA-Net median | optuna NSGA-II median | Relative gap | MWU p | Random search median | Criterion met |",  # noqa: E501
        "|---|---|---|---|---|---|---|",
    ]
    all_met = True
    for problem in (linear, lotz):
        ours, ref, rnd = [], [], []
        for seed in range(1, args.seeds + 1):
            ours.append(
                run_project_method(
                    NSGANet, problem, args.budget, seed, population_size=20, mutation_rate=0.1
                )
            )
            ref.append(run_optuna_nsga2(problem, args.budget, seed))
            rnd.append(run_project_method(RandomSearch, problem, args.budget, seed))
            print(
                f"{problem.__name__} seed {seed}: nsga_net {ours[-1]:.4f} optuna {ref[-1]:.4f} random {rnd[-1]:.4f}",  # noqa: E501
                flush=True,
            )
        m_ours, m_ref, m_rnd = (
            statistics.median(ours),
            statistics.median(ref),
            statistics.median(rnd),
        )
        gap = (m_ours - m_ref) / m_ref
        p = mannwhitneyu(ours, ref).pvalue
        met = abs(gap) <= 0.05 and m_ours > m_rnd and m_ref > m_rnd
        all_met &= met
        lines.append(
            f"| {problem.__name__} | {m_ours:.4f} | {m_ref:.4f} | {gap:+.2%} | {p:.3f} | {m_rnd:.4f} | {'yes' if met else 'NO'} |"  # noqa: E501
        )
    lines += ["", f"Overall: {'criterion met' if all_met else 'CRITERION NOT MET'}"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
