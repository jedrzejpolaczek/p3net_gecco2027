"""Level-1 tests for NSGA-Net (card `notes/plans/v005-sources/nsga-net.md`,
W-N1-W-N6).

Source: Lu et al., NSGA-Net, GECCO'19 (arXiv:1810.03522v2); authors' code
github.com/ianwhale/nsga-net (`search/nsganet.py`, pymoo 0.3.0). Card
decisions: N-1 a (authors' code: binary tournament, two-point crossover,
integer polynomial mutation eta = 3, duplicate elimination, no BOA), N-2 a,
O-N1 (population / offspring 20).

Helper signatures (interfaces §7, Q-23):
  binary_tournament(a, b, rng) -> 0 | 1   with a, b = (objectives, crowding)
  two_point_crossover(p1, p2, rng) -> (c1, c2)
  int_polynomial_mutation(g, domains, rng) -> g'
"""

from __future__ import annotations

import random
import statistics

import pytest

from p3net.problem.objectives import fast_nondominated_sort

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    drive,
    drive_batches,
    make,
    random_weights,
    space_of,
    vals,
)


def _m():
    from p3net.v005.baselines import nsga_net

    return nsga_net


def _conflicting(domains, seed=0):
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


def test_WN1_binary_tournament_dominance_then_crowding_then_random():
    """W-N1 (code: binary tournament): a dominating individual wins whatever
    the crowding; without dominance the larger crowding distance wins; a
    full tie is decided at random (both outcomes occur)."""
    bt = _m().binary_tournament
    rng = random.Random(0)
    for _ in range(50):
        assert bt(((1.0, 1.0), 0.1), ((2.0, 2.0), 9.0), rng) == 0
        assert bt(((2.0, 2.0), 9.0), ((1.0, 1.0), 0.1), rng) == 1
        assert bt(((1.0, 3.0), 0.2), ((3.0, 1.0), 0.7), rng) == 1
        assert bt(((1.0, 3.0), float("inf")), ((3.0, 1.0), 0.7), rng) == 0
    outcomes = {bt(((1.0, 3.0), 0.5), ((3.0, 1.0), 0.5), random.Random(s)) for s in range(40)}
    assert outcomes == {0, 1}


def test_WN2_two_point_crossover_structure_and_rate():
    """W-N2 (code: PointCrossover(n_points=2); pymoo 0.3.0 has no crossover
    probability there -> always applied, p = 1.0, interfaces §7 Q-23):
    children take genes position-wise from the parents, complementarily,
    swapping one non-empty contiguous segment, in every trial."""
    cx = _m().two_point_crossover
    p1, p2 = G(*([0] * 10)), G(*([1] * 10))
    rng = random.Random(0)
    crossed = 0
    trials = 3000
    for _ in range(trials):
        c1, c2 = (vals(c) for c in cx(p1, p2, rng))
        assert all(a in (0, 1) for a in c1 + c2)
        assert all(a != b for a, b in zip(c1, c2)), "children are not complementary"
        swapped = [i for i, a in enumerate(c1) if a == 1]
        if swapped:
            crossed += 1
            assert swapped == list(range(swapped[0], swapped[-1] + 1)), (
                "swapped part is not one segment"
            )
            assert len(swapped) < 10
    assert crossed == trials, f"crossover skipped in {trials - crossed} of {trials} trials"


def test_WN3_integer_polynomial_mutation_in_range_local_and_rare():
    """W-N3 (code: PolynomialMutation(eta=3, var_type=int); pymoo 0.3.0
    default per-variable probability 1/n): results are integers in 0..k-1;
    on average about one variable changes; small moves dominate (eta = 3)."""
    mut = _m().int_polynomial_mutation
    domains = [8] * 10
    rng = random.Random(1)
    changed, steps = [], []
    for _ in range(3000):
        g = tuple(rng.randrange(8) for _ in range(10))
        r = vals(mut(G(*g), domains, rng))
        assert all(isinstance(v, int) and 0 <= v < 8 for v in r)
        d = [abs(a - b) for a, b in zip(g, r) if a != b]
        changed.append(len(d))
        steps.extend(d)
    assert 0.3 < statistics.fmean(changed) < 1.2
    assert steps.count(1) > steps.count(7)
    assert steps.count(1) + steps.count(2) > 0.5 * len(steps)


def test_WN4_survival_is_rank_and_crowding_mu_plus_lambda():
    """W-N4 (code: RankAndCrowdingSurvival, mu + lambda): after a generation
    the population is the 20 best of parents + offspring by NDS rank (no
    individual of a worse front kept while one of a better front is
    dropped)."""
    from p3net.harness.runner import Observation, RunState

    space = space_of([4] * 8)
    obj = _conflicting([4] * 8)
    m = make(_m().NSGANet, space, 120, 0)
    state = RunState()
    prev = []
    while state.evaluations_used < 120:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=obj(g)) for g in props]
        state.history.extend(new)
        state.evaluations_used += len(new)
        m.update(state, new)
        pop = [vals(o) for o in m.population]
        assert len(pop) == 20
        union = list(dict.fromkeys(prev + [vals(g) for g in props]))
        if prev:
            fronts = fast_nondominated_sort(union, lambda g: obj.value(g))
            rank = {g: r for r, f in enumerate(fronts) for g in f}
            worst_kept = max(rank[g] for g in pop)
            assert all(rank[g] >= worst_kept for g in union if g not in pop), (
                "survival is not by NDS rank"
            )
        prev = pop


def test_WN5_duplicates_eliminated_before_evaluation():
    """W-N5 (code: eliminate_duplicates=True; #35): a small space (2^6 = 64)
    forces many duplicate offspring; none is evaluated twice, and within one
    offspring batch genotypes are distinct."""
    obj = _conflicting([2] * 6)
    batches = drive_batches(make(_m().NSGANet, space_of([2] * 6), 50, 0), obj, 50)
    for b in batches:
        assert len(set(b)) == len(b)
    assert len(set(obj.calls)) == len(obj.calls) <= 50


@pytest.mark.parametrize("budget", [47, 100])
def test_WN6_population_20_offspring_20_budget_respected(budget):
    """W-N6 (O-N1, O-N2, K-2): first batch = 20 random distinct genotypes,
    every further batch = 20 offspring except a last one cut by the budget;
    exactly b evaluations."""
    obj = _conflicting([4] * 8)
    batches = drive_batches(make(_m().NSGANet, space_of([4] * 8), budget, 3), obj, budget)
    assert len(batches[0]) == 20 and len(set(batches[0])) == 20
    assert all(len(b) == 20 for b in batches[1:-1])
    assert_budget_respected(obj, budget, exact=True)


def test_WN6_start_is_random():
    """W-N6 (start random): different seeds give different initial populations."""
    from p3net.harness.runner import RunState

    a = [vals(g) for g in make(_m().NSGANet, space_of([4] * 8), 100, 0).propose(RunState())]
    b = [vals(g) for g in make(_m().NSGANet, space_of([4] * 8), 100, 1).propose(RunState())]
    assert a != b
    obj = _conflicting([4] * 8)
    drive(make(_m().NSGANet, space_of([4] * 8), 40, 0), obj, 40)
    assert obj.n == 40
