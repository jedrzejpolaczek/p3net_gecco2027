"""NSGA-Net as in the authors' code (card `nsga-net.md`, N-1 a; github.com/ianwhale/
nsga-net `search/nsganet.py`, pymoo 0.3.0).

NSGA-II mu + lambda: binary tournament by dominance, then crowding, then at random
(`binary_tournament`, 'comp_by_dom_and_crowding'); two-point crossover, always
applied (pymoo 0.3.0 `PointCrossover` has no probability); integer polynomial
mutation, eta = 3, per-variable probability 1/n, rounded and kept in range; duplicate
elimination before evaluation; survival by rank and crowding. No BOA exploitation
stage (absent from the authors' code). Population and offspring 20 (#37).
"""

from __future__ import annotations

import math

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import crowding_distance, dominates, fast_nondominated_sort
from p3net.v005.common import EvalCache, cardinalities, is_valid, random_genotype, space_size

ETA = 3.0
MAX_MATING_ROUNDS = 100  # pymoo: n_max_iterations when filling the offspring with unique ones


def binary_tournament(a, b, rng) -> int:
    """a, b = (objectives, crowding); returns 0 if a wins, 1 if b wins."""
    (fa, ca), (fb, cb) = a, b
    if dominates(tuple(fa), tuple(fb)):
        return 0
    if dominates(tuple(fb), tuple(fa)):
        return 1
    if ca > cb:
        return 0
    if cb > ca:
        return 1
    return rng.randrange(2)


def two_point_crossover(p1: Genotype, p2: Genotype, rng) -> tuple[Genotype, Genotype]:
    """pymoo 0.3.0 PointCrossover(n_points=2): two distinct cut points in 1..n-1;
    the segment between them is exchanged."""
    n = len(p1.values)
    a, b = sorted(rng.sample(range(1, n), 2)) if n > 2 else (1, n)
    c1 = list(p1.values)
    c2 = list(p2.values)
    c1[a:b], c2[a:b] = list(p2.values[a:b]), list(p1.values[a:b])
    return Genotype(values=tuple(c1)), Genotype(values=tuple(c2))


def int_polynomial_mutation(g: Genotype, domains, rng, eta: float = ETA) -> Genotype:
    """pymoo 0.3.0 PolynomialMutation(eta, prob=1/n, var_type=int) on [0, k-1]."""
    n = len(domains)
    out = list(g.values)
    for i, k in enumerate(domains):
        if k < 2 or rng.random() >= 1.0 / n:
            continue
        x, xl, xu = float(out[i]), 0.0, float(k - 1)
        d1, d2 = (x - xl) / (xu - xl), (xu - x) / (xu - xl)
        u, mp = rng.random(), 1.0 / (eta + 1.0)
        if u <= 0.5:
            val = 2.0 * u + (1.0 - 2.0 * u) * (1.0 - d1) ** (eta + 1.0)
            dq = val**mp - 1.0
        else:
            val = 2.0 * (1.0 - u) + 2.0 * (u - 0.5) * (1.0 - d2) ** (eta + 1.0)
            dq = 1.0 - val**mp
        y = min(max(x + dq * (xu - xl), xl), xu)
        out[i] = int(min(max(round(y), 0), k - 1))
    return Genotype(values=tuple(out))


def rank_and_crowding(pop: list[Observation], size: int, rng) -> tuple[list[Observation], dict[int, tuple[int, float]]]:
    """RankAndCrowdingSurvival: fill by fronts, cut the last front by crowding
    (descending, random among ties). Returns survivors and (rank, crowding) per survivor."""
    idx = list(range(len(pop)))
    obj = lambda i: tuple(pop[i].objectives)  # noqa: E731
    survivors, info = [], {}
    for r, front in enumerate(fast_nondominated_sort(idx, obj)):
        cd = crowding_distance(front, obj)
        members = list(range(len(front)))
        rng.shuffle(members)
        members.sort(key=lambda k: -cd[k])
        for k in members:
            if len(survivors) >= size:
                break
            info[len(survivors)] = (r, cd[k])
            survivors.append(pop[front[k]])
        if len(survivors) >= size:
            break
    return survivors, info


class NSGANet:
    def __init__(self, space, budget, rng, *, pop_size: int = 20, n_offspring: int = 20):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.pop_size, self.n_offspring = int(pop_size), int(n_offspring)
        self.domains = cardinalities(space)
        self.cache = EvalCache()
        self.population: list[Observation] = []
        self._info: dict[int, tuple[int, float]] = {}
        self.used = 0
        self._pending: list[Genotype] = []
        self._size = space_size(space)

    def config(self) -> dict:
        return {"pop_size": self.pop_size, "n_offspring": self.n_offspring, "eta": ETA,
                "crossover": "two_point (p = 1.0)", "mutation_prob": "1/n", "eliminate_duplicates": True}

    def _select(self) -> Observation:
        i, j = self.rng.randrange(len(self.population)), self.rng.randrange(len(self.population))
        a = (self.population[i].objectives, self._info[i][1])
        b = (self.population[j].objectives, self._info[j][1])
        return self.population[i] if binary_tournament(a, b, self.rng) == 0 else self.population[j]

    def _offspring(self, n: int) -> list[Genotype]:
        out: list[Genotype] = []
        for _ in range(MAX_MATING_ROUNDS):
            while len(out) < n:
                before = len(out)
                for _ in range(math.ceil((n - len(out)) / 2)):
                    c1, c2 = two_point_crossover(self._select().genotype, self._select().genotype, self.rng)
                    for c in (c1, c2):
                        c = int_polynomial_mutation(c, self.domains, self.rng)
                        if len(out) < n and c not in out and c not in self.cache and is_valid(self.space, c):
                            out.append(c)
                if len(out) == before:
                    break
            if len(out) >= n or len(self.cache) + len(out) >= self._size:
                break
        return out

    def propose(self, state: RunState) -> list[Genotype]:
        remaining = self.budget - self.used
        if remaining <= 0 or self._pending:
            return []
        if not self.population:
            n = min(self.pop_size, remaining)
            init: list[Genotype] = []
            while len(init) < n:
                g = random_genotype(self.space, self.rng)
                if g not in init:
                    init.append(g)
            batch = init
        else:
            batch = self._offspring(min(self.n_offspring, remaining))
        self._pending = batch
        self.used += len(batch)
        return list(batch)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        new = []
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
            new.append(Observation(genotype=obs.genotype, objectives=tuple(obs.objectives)))
        self.population, self._info = rank_and_crowding(self.population + new, self.pop_size, self.rng)
        self._pending = []
