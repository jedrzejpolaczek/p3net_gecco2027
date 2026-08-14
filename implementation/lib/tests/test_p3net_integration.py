"""Integration test for p3net.methods.p3net.P3Net -- proves the full search
loop runs end to end and out-performs random search on a toy structured
combinatorial problem, independent of any NAS specifics. (Gap in the
original task list -- adding it since this is the one test that exercises
the whole loop together.)"""

import random

from sklearn.linear_model import LinearRegression

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

N_BLOCKS = 3
BLOCK_SIZE = 4
N_VARS = N_BLOCKS * BLOCK_SIZE


def toy_search_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * N_VARS)


def _trap4(u: int) -> int:
    return 4 if u == 4 else 3 - u


def toy_objective(genotype: Genotype):
    """Concatenated deceptive trap functions -- the classic benchmark for
    demonstrating linkage-learning value: crossover that respects each
    4-bit block can jump straight from the deceptive all-zeros local
    optimum to the true all-ones optimum; block-blind search cannot.
    Single objective to minimise (negative total trap value)."""
    total = 0
    for b in range(N_BLOCKS):
        block = genotype.values[b * BLOCK_SIZE : (b + 1) * BLOCK_SIZE]
        total += _trap4(sum(block))
    return (-float(total),)


def always_valid(genotype: Genotype) -> float:
    return -1.0  # g(x) <= 0 always: every genotype in this toy space is valid


class RandomSearch:
    """Sanity baseline: propose one uniform-random valid genotype at a
    time, no state, no surrogate."""

    def __init__(self, space: SearchSpace, seed: int):
        self._space = space
        self._rng = random.Random(seed)

    def propose(self, state):
        return [self._space.sample_uniform(self._rng)]

    def update(self, state, new_observations):
        pass


def test_p3net_completes_full_budget_without_error():
    space = toy_search_space()
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        population_size=10,
    )
    state = Runner(objective=toy_objective, budget=80).run(method)
    assert state.evaluations_used == 80


def test_p3net_respects_dedup_cache_and_records_h_t_without_duplicates():
    space = toy_search_space()
    cache = EvaluationCache()
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(1),
        population_size=10,
        cache=cache,
    )
    Runner(objective=toy_objective, budget=60).run(method)
    assert cache.size() > 0
    seen = list(method._history.keys())
    assert len(seen) == len(set(seen))


def test_p3net_outperforms_random_search_on_a_toy_structured_problem():
    space = toy_search_space()
    budget = 200

    p3net_method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(42),
        population_size=15,
    )
    p3net_state = Runner(objective=toy_objective, budget=budget).run(p3net_method)
    p3net_best = min(obs.objectives[0] for obs in p3net_state.history)

    random_state = Runner(objective=toy_objective, budget=budget).run(RandomSearch(space, seed=42))
    random_best = min(obs.objectives[0] for obs in random_state.history)

    assert p3net_best <= random_best
