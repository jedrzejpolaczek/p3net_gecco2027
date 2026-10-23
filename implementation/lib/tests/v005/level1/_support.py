"""Shared helpers for level-1 tests: small problems with known answers,
counting objectives and an independent ask-tell driver.

Only the public interface from `notes/plans/v005-interfaces.md` §0 is used
here (`Genotype`, `SearchSpace`, `Observation`, `RunState`, `dominates`,
the k-ary trap). The driver is written from the protocol (ask-tell, #34) and
deliberately does NOT use `p3net.v005.testing.step_through`, so a bug shared
by a method and that helper cannot hide itself.
"""

from __future__ import annotations

import inspect
import itertools
import math
import random
from collections.abc import Callable, Iterable, Sequence
from typing import Any

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.problem.objectives import dominates
from p3net.problem.synthetic_kary import build_k_ary_trap_space, k_ary_trap_fitness

# ---------------------------------------------------------------------------
# Genotypes
# ---------------------------------------------------------------------------


def G(*idx: int) -> Genotype:
    """Genotype from value indices (interfaces §0: a genotype is a tuple of
    indices 0..k_i-1)."""
    return Genotype(values=tuple(int(i) for i in idx))


def vals(g: Any) -> tuple:
    """Index tuple of a genotype, whether a method returns `Genotype` or a
    plain tuple (interfaces §7, Q-01: v005 uses `Genotype`)."""
    if hasattr(g, "values") and not isinstance(g, dict):
        v = g.values
        return tuple(v() if callable(v) else v)
    if hasattr(g, "genotype"):  # an Observation
        return vals(g.genotype)
    return tuple(g)


def hamming(a: Any, b: Any) -> int:
    return sum(x != y for x, y in zip(vals(a), vals(b), strict=True))


def diff_positions(a: Any, b: Any) -> list[int]:
    return [i for i, (x, y) in enumerate(zip(vals(a), vals(b), strict=True)) if x != y]


def space_of(domains: Sequence[int]) -> SearchSpace:
    """SearchSpace with the given cardinalities, values 0..k-1."""
    return SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(k))) for k in domains))


def cards(space: SearchSpace) -> list[int]:
    """Cardinalities k_i of a space (the `domains: list[int]` of interfaces §1)."""
    return [len(d.values) for d in space.domains]


def trap_space(n_blocks: int = 3, block_size: int = 3, alphabet: int = 3) -> SearchSpace:
    return build_k_ary_trap_space(n_blocks=n_blocks, block_size=block_size, alphabet_size=alphabet)


def all_genotypes(domains: Sequence[int]) -> list[tuple[int, ...]]:
    return list(itertools.product(*[range(k) for k in domains]))


# ---------------------------------------------------------------------------
# Objectives with known answers
# ---------------------------------------------------------------------------


def trap_f1(block_size: int, n: int) -> Callable[[Any], float]:
    """Positive (log-safe) k-ary trap, minimised; the unique optimum (all
    zeros) has f1 == 1.0."""
    opt = k_ary_trap_fitness(Genotype(values=(0,) * n), block_size=block_size)

    def f(g: Any) -> float:
        return 1.0 + (k_ary_trap_fitness(Genotype(values=vals(g)), block_size=block_size) - opt)

    return f


def additive_cost(weights: Sequence[Sequence[float]]) -> Callable[[Any], float]:
    """f2 = 1 + sum_i w_i[x_i] (positive, additive: an empty true VIG)."""

    def f(g: Any) -> float:
        return 1.0 + sum(weights[i][v] for i, v in enumerate(vals(g)))

    return f


def random_weights(domains: Sequence[int], seed: int = 0) -> list[list[float]]:
    r = random.Random(seed)
    return [[r.random() for _ in range(k)] for k in domains]


class CountingObjective:
    """Two-objective full evaluation that records every call. Optionally
    appends ("eval", genotype) to a shared event log so method events and
    evaluations can be interleaved in one timeline."""

    def __init__(
        self,
        f1: Callable[[Any], float],
        f2: Callable[[Any], float] | None = None,
        log: list | None = None,
    ):
        self.f1 = f1
        self.f2 = f2 if f2 is not None else (lambda g: 0.0)
        self.calls: list[tuple] = []
        self.log = log

    def __call__(self, g: Any) -> tuple[float, float]:
        self.calls.append(vals(g))
        if self.log is not None:
            self.log.append(("eval", {"genotype": vals(g)}))
        return (float(self.f1(g)), float(self.f2(g)))

    def value(self, g: Any) -> tuple[float, float]:
        """Same values, without counting (for assertions)."""
        return (float(self.f1(g)), float(self.f2(g)))

    @property
    def n(self) -> int:
        return len(self.calls)


class EventLog(list):
    """Observer for the `observer=` hook (interfaces §7, Q-02):
    called as observer(kind, payload)."""

    def __call__(self, kind: str, payload: dict | None = None) -> None:
        self.append((kind, dict(payload or {})))

    def of(self, kind: str) -> list[dict]:
        return [p for k, p in self if k == kind]


# ---------------------------------------------------------------------------
# Independent ask-tell driver (protocol #34, K-2)
# ---------------------------------------------------------------------------


def drive(
    method: Any,
    objective: Callable[[Any], tuple],
    budget: int,
    *,
    max_rounds: int = 200_000,
    until: Callable[[RunState], bool] | None = None,
) -> RunState:
    """Ask-tell loop. Every proposed genotype is evaluated -- the driver does
    NOT truncate a batch -- so a method that overshoots its budget is visible
    as state.evaluations_used > budget (K-2: the method itself must never
    exceed the budget). Stops when the budget is spent, when the method
    proposes nothing, after max_rounds, or when `until(state)` holds."""
    state = RunState()
    rounds = 0
    while state.evaluations_used < budget and rounds < max_rounds:
        if until is not None and until(state):
            break
        rounds += 1
        proposals = list(method.propose(state))
        if not proposals:
            break
        new = [Observation(genotype=g, objectives=objective(g)) for g in proposals]
        state.history.extend(new)
        state.evaluations_used += len(new)
        method.update(state, new)
    return state


def drive_batches(
    method: Any, objective: Callable[[Any], tuple], budget: int, *, max_rounds: int = 100_000
) -> list[list[tuple]]:
    """Like `drive`, but returns the proposal batches (as index tuples)."""
    state = RunState()
    batches: list[list[tuple]] = []
    rounds = 0
    while state.evaluations_used < budget and rounds < max_rounds:
        rounds += 1
        proposals = list(method.propose(state))
        if not proposals:
            break
        batches.append([vals(g) for g in proposals])
        new = [Observation(genotype=g, objectives=objective(g)) for g in proposals]
        state.history.extend(new)
        state.evaluations_used += len(new)
        method.update(state, new)
    return batches


def make(cls: type, space: SearchSpace, budget: int, seed: int, **params: Any) -> Any:
    """Construct a v005 method with the convention of interfaces §4:
    __init__(space, budget, rng, **params) (interfaces §7, Q-03)."""
    return cls(space, budget, random.Random(seed), **params)


# ---------------------------------------------------------------------------
# Assertions shared by many cards
# ---------------------------------------------------------------------------

#: Constructor parameters through which a method could read f2 (or anything
#: else) from the benchmark without a full evaluation (#6, #34).
FORBIDDEN_INIT_PARAMS = {
    "objective",
    "objectives",
    "benchmark",
    "substrate",
    "analytic_cost",
    "analytic_f2",
    "f2",
    "f2_fn",
    "cost",
    "cost_fn",
    "true_f2",
    "evaluate",
    "evaluator",
    "oracle_fn",
}


def assert_no_benchmark_access(cls: type) -> None:
    params = set(inspect.signature(cls.__init__).parameters)
    leaked = params & FORBIDDEN_INIT_PARAMS
    assert not leaked, (
        f"{cls.__name__}.__init__ takes {leaked}: f2 or the benchmark leak into the method"
    )


def assert_budget_respected(
    objective: CountingObjective, budget: int, *, exact: bool = True
) -> None:
    """K-2 and #35: never more than `budget` real evaluations, never the same
    genotype twice, and (exact=True) exactly `budget` when the space is not
    exhausted."""
    assert objective.n <= budget, f"{objective.n} evaluations > budget {budget}"
    assert len(set(objective.calls)) == objective.n, "a duplicate genotype consumed budget (#35)"
    if exact:
        assert objective.n == budget, f"run stopped at {objective.n} < budget {budget}"


def pareto_ok(new: Sequence[float], old: Sequence[float]) -> bool:
    return dominates(tuple(new), tuple(old))


def entropy_ratio_close(a: float, b: float, ratio: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, ratio * b, rel_tol=tol, abs_tol=tol)


def iter_segments(
    log: Iterable[tuple[str, dict]], marker: str = "iteration"
) -> list[list[tuple[str, dict]]]:
    """Split an event log into segments, each starting at `marker`. The last
    segment may be truncated by the budget (K-2); callers that need complete
    iterations should drop it."""
    segs: list[list[tuple[str, dict]]] = []
    for ev in log:
        if ev[0] == marker:
            segs.append([ev])
        elif segs:
            segs[-1].append(ev)
    return segs
