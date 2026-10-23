"""Elements shared by every v005 method (interfaces §0, §7).

- Validity of cell genotypes (#33): one rule for every cell space.
- Budget (K-2): never more than b real evaluations; cached genotypes are free (#35).
- EvalCache: H_t, the set of really evaluated genotypes.
- initial_design_size (BB-4): min(source value, floor(0.25 b)).
- online_minmax (R-3 a, L-1 b): normalisation by the objectives seen so far.
- ElitistArchive: non-dominated real evaluations (MO-GOMEA acceptance, D-1 b).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Sequence

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, dominates

#: The NAS-Bench-201 cell shared by JAHS-Bench-201, NAS-HPO-Bench-II and NB201
#: (experiments/search_spaces/_cell_graph.py): 4 nodes, edge i joins CELL_EDGES[i].
CELL_EDGES: tuple[tuple[int, int], ...] = ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))
_NONE = "none"


def _is_cell_space(space: SearchSpace) -> bool:
    return space.n >= len(CELL_EDGES) and all(
        _NONE in space.domains[i].values for i in range(len(CELL_EDGES))
    )


def is_valid(space: SearchSpace, g: Genotype) -> bool:
    """#33: a cell genotype is valid iff an input-output path exists through
    edges whose operation is not 'none'. Spaces without a cell (no 'none' in the
    first six coordinates) have no constraint."""
    if not _is_cell_space(space):
        return True
    adjacency: dict[int, list[int]] = {n: [] for n in range(4)}
    for i, (src, dst) in enumerate(CELL_EDGES):
        if space.domains[i].values[g.values[i]] != _NONE:
            adjacency[src].append(dst)
    seen, frontier = {0}, [0]
    while frontier:
        for nxt in adjacency[frontier.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return 3 in seen


def cardinalities(space: SearchSpace) -> list[int]:
    return [len(d.values) for d in space.domains]


def space_size(space: SearchSpace) -> int:
    return math.prod(cardinalities(space))


def random_genotype(space: SearchSpace, rng, *, valid_only: bool = True) -> Genotype:
    """Uniform over value indices; with valid_only, rejection sampling over valid
    genotypes (O-4)."""
    ks = cardinalities(space)
    while True:
        g = Genotype(values=tuple(rng.randrange(k) for k in ks))
        if not valid_only or is_valid(space, g):
            return g


class EvalCache:
    """H_t: every really evaluated genotype with its objectives (O-5, #35)."""

    def __init__(self) -> None:
        self._d: dict[Genotype, Objectives] = {}

    def get(self, g: Genotype) -> Objectives | None:
        return self._d.get(g)

    def put(self, g: Genotype, objs: Sequence[float]) -> None:
        self._d[g] = tuple(float(x) for x in objs)

    def __contains__(self, g: Genotype) -> bool:
        return g in self._d

    def __len__(self) -> int:
        return len(self._d)

    def history(self) -> list[Observation]:
        return [Observation(genotype=g, objectives=o) for g, o in self._d.items()]


class Budget:
    """K-2: at most `total` real evaluations; a genotype already in the cache costs
    nothing (#35). `charge` is called before an evaluation is proposed."""

    def __init__(self, total: int):
        self.total = int(total)
        self.used = 0

    @property
    def remaining(self) -> int:
        return self.total - self.used

    def charge(self, g: Genotype, cache: EvalCache) -> bool:
        if g in cache:
            return True
        if self.used >= self.total:
            return False
        self.used += 1
        return True


def initial_design_size(source_value: int, budget: int) -> int:
    """BB-4: min(source value, floor(0.25 b))."""
    return min(int(source_value), int(budget) // 4)


def online_minmax(history: Iterable[Sequence[float]]) -> Callable[[Sequence[float]], tuple[float, float]]:
    """R-3 a / L-1 b: map objectives to [0, 1] with the min and max of the values
    seen so far; an objective with min == max maps to 0.0 (Q-33)."""
    rows = [tuple(float(x) for x in h) for h in history]
    if not rows:
        return lambda o: tuple(0.0 for _ in o)  # type: ignore[return-value]
    lo = [min(r[i] for r in rows) for i in range(len(rows[0]))]
    hi = [max(r[i] for r in rows) for i in range(len(rows[0]))]

    def f(o: Sequence[float]) -> tuple[float, float]:
        return tuple(  # type: ignore[return-value]
            0.0 if hi[i] == lo[i] else (float(o[i]) - lo[i]) / (hi[i] - lo[i]) for i in range(len(o))
        )

    return f


class ElitistArchive:
    """Non-dominated set of objective vectors (strict dominance; equal vectors kept
    once)."""

    def __init__(self) -> None:
        self.points: list[Objectives] = []

    def add(self, o: Sequence[float]) -> bool:
        o = tuple(float(x) for x in o)
        if any(dominates(p, o) or p == o for p in self.points):
            return False
        self.points = [p for p in self.points if not dominates(o, p)] + [o]
        return True

    def dominated(self, o: Sequence[float]) -> bool:
        o = tuple(o)
        return any(dominates(p, o) for p in self.points)
