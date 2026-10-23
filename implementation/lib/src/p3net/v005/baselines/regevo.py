"""Regularized (aging) evolution, multi-objective adaptation (card `regevo.md`).

Real et al., AAAI 2019, Alg. 1 and NAS-Bench-201 `R_EA.py`: a population of P
random architectures; each cycle samples S members with replacement, mutates the
best one in one variable and removes the oldest member (FIFO). Our only
multi-objective adaptation (#24, RE-1 b): the tournament winner is chosen by
NSGA-II's crowded comparison computed on the whole current population.
P = 20 (#37), S = 5 (S/P = 0.25 as in Real et al.), no identity mutation (O-RE3),
a duplicate child costs no budget and still enters the population (O-RE4).
"""

from __future__ import annotations

import random
from collections import deque

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import crowding_distance, fast_nondominated_sort
from p3net.v005.common import CELL_EDGES, EvalCache, _is_cell_space, cardinalities, is_valid, random_genotype, space_size

MAX_DUPLICATE_CHILDREN = 100_000


#: generator for the random tie-break of `crowded_winner`; RegEvo sets it to its own
#: generator before each tournament (the interface keeps the two-argument signature)
_TIE_RNG = random


def crowded_winner(sample: list[Observation], population: list[Observation]) -> Observation:
    """RE-1 b: the sample member with the lowest non-domination rank in the
    population, ties by the larger crowding distance in its population front, then
    at random (with `_TIE_RNG`, so a seeded run is reproducible)."""
    idx = list(range(len(population)))
    obj = lambda i: tuple(population[i].objectives)  # noqa: E731
    rank, crowd = {}, {}
    for r, front in enumerate(fast_nondominated_sort(idx, obj)):
        cd = crowding_distance(front, obj)
        for k, i in enumerate(front):
            rank[i], crowd[i] = r, cd[k]

    def key(o: Observation):
        i = next(j for j, p in enumerate(population) if p is o or p.genotype == o.genotype)
        return rank[i], -crowd[i]

    best = min(key(o) for o in sample)
    return _TIE_RNG.choice([o for o in sample if key(o) == best])


class RegEvo:
    def __init__(self, space, budget, rng, *, population_size: int = 20, sample_size: int = 5):
        self.space, self.rng = space, rng
        self.budget = int(budget)
        self.P = min(int(population_size), self.budget)
        self.S = int(sample_size)
        self.domains = cardinalities(space)
        self.cache = EvalCache()
        self.population: deque[Observation] = deque()
        self.used = 0
        self._pending: list[Genotype] = []
        self._size = space_size(space)
        # O-RE3 (2026-10-20, b): mutation units as in `R_EA.py` -- in a cell space a node,
        # then one of its incoming edges; every non-cell variable is a unit of its own (Z-RE1)
        if _is_cell_space(space):
            nodes = sorted({dst for _, dst in CELL_EDGES})
            self.units = [[i for i, (_, dst) in enumerate(CELL_EDGES) if dst == n] for n in nodes]
            self.units += [[i] for i in range(len(CELL_EDGES), len(self.domains))]
        else:
            self.units = [[i] for i in range(len(self.domains))]

    def config(self) -> dict:
        return {"population_size": self.P, "sample_size": self.S, "seed": None}

    def _mutate(self, g: Genotype) -> Genotype:
        while True:
            unit = self.units[self.rng.randrange(len(self.units))]
            i = unit[self.rng.randrange(len(unit))]
            v = self.rng.choice([x for x in range(self.domains[i]) if x != g.values[i]])
            child = g.with_values(indices=[i], new_values=[v])
            if is_valid(self.space, child):
                return child

    def _cycle_child(self) -> Genotype:
        pop = list(self.population)
        sample = [self.rng.choice(pop) for _ in range(self.S)]  # with replacement
        global _TIE_RNG
        _TIE_RNG = self.rng
        parent = crowded_winner(sample, pop)
        return self._mutate(parent.genotype)

    def _age(self, obs: Observation) -> None:
        self.population.append(obs)
        if len(self.population) > self.P:
            self.population.popleft()

    def propose(self, state: RunState) -> list[Genotype]:
        if self.used >= self.budget or self._pending:
            return []
        if not self.population and len(self.cache) == 0:
            init: list[Genotype] = []
            while len(init) < self.P:
                g = random_genotype(self.space, self.rng)
                if g not in init:
                    init.append(g)
            self._pending = init
            self.used += len(init)
            return list(init)
        for _ in range(MAX_DUPLICATE_CHILDREN):
            child = self._cycle_child()
            known = self.cache.get(child)
            if known is None:
                self._pending = [child]
                self.used += 1
                return [child]
            self._age(Observation(genotype=child, objectives=known))  # O-RE4
            if len(self.cache) >= self._size:
                break
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
            self._age(Observation(genotype=obs.genotype, objectives=tuple(obs.objectives)))
        self._pending = []
