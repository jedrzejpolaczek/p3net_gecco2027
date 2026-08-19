"""Tests for p3net.problem.objectives -- Pareto dominance/front, fidelity
ladder, evaluation-noise handling. (Gap in the original task list -- adding
it since this module has real, testable logic.)"""

import pytest

from p3net.problem.objectives import (
    FidelityLadder,
    FidelityLevel,
    crowding_distance,
    dominates,
    evaluate_with_noise,
    fast_nondominated_sort,
    pareto_front,
    select_survivors,
)


def test_dominates_basic_two_objective_case():
    assert dominates((1.0, 1.0), (2.0, 2.0))
    assert not dominates((2.0, 2.0), (1.0, 1.0))
    assert not dominates((1.0, 2.0), (2.0, 1.0))  # neither dominates the other
    assert not dominates((1.0, 1.0), (1.0, 1.0))  # equal is not dominance


def test_dominates_rejects_mismatched_length():
    with pytest.raises(ValueError):
        dominates((1.0,), (1.0, 2.0))


def test_dominates_generalises_to_three_objectives():
    assert dominates((1.0, 1.0, 1.0), (2.0, 2.0, 2.0))
    assert not dominates((1.0, 2.0, 1.0), (2.0, 1.0, 1.0))


def test_pareto_front_two_objectives():
    items = [(1.0, 5.0), (5.0, 1.0), (3.0, 3.0), (4.0, 4.0)]  # (4,4) dominated by (3,3)
    front = pareto_front(items, lambda x: x)
    assert set(front) == {(1.0, 5.0), (5.0, 1.0), (3.0, 3.0)}


def test_pareto_front_three_objectives():
    items = [(1.0, 1.0, 1.0), (2.0, 2.0, 2.0), (1.0, 2.0, 3.0)]
    front = pareto_front(items, lambda x: x)
    assert (2.0, 2.0, 2.0) not in front
    assert (1.0, 1.0, 1.0) in front


def test_fidelity_ladder_requires_increasing_rank():
    FidelityLadder(levels=(FidelityLevel(rank=0, config={}), FidelityLevel(rank=1, config={})))
    with pytest.raises(ValueError):
        FidelityLadder(levels=(FidelityLevel(rank=1, config={}), FidelityLevel(rank=0, config={})))


def test_fidelity_ladder_highest_is_last_level():
    ladder = FidelityLadder(
        levels=(
            FidelityLevel(rank=0, config={"epochs": 1}),
            FidelityLevel(rank=1, config={"epochs": 10}),
        )
    )
    assert ladder.highest.config == {"epochs": 10}


def test_evaluate_with_noise_is_noop_for_s_equals_one():
    calls = {"n": 0}

    def query():
        calls["n"] += 1
        return 42.0

    result = evaluate_with_noise(query, s=1)
    assert result == 42.0
    assert calls["n"] == 1


def test_evaluate_with_noise_reduces_stochastic_repeats_via_median():
    values = iter([10.0, 20.0, 30.0])
    result = evaluate_with_noise(lambda: next(values), s=3)
    assert result == 20.0


def test_evaluate_with_noise_rejects_s_below_one():
    with pytest.raises(ValueError):
        evaluate_with_noise(lambda: 1.0, s=0)


def test_fast_nondominated_sort_ranks_items_into_fronts():
    # (4,4) is dominated by (3,3); everything else is mutually nondominated.
    items = [(1.0, 5.0), (5.0, 1.0), (3.0, 3.0), (4.0, 4.0)]
    fronts = fast_nondominated_sort(items, lambda x: x)
    assert set(fronts[0]) == {(1.0, 5.0), (5.0, 1.0), (3.0, 3.0)}
    assert fronts[1] == [(4.0, 4.0)]


def test_crowding_distance_boundary_points_are_infinite():
    front = [(1.0, 5.0), (3.0, 3.0), (5.0, 1.0)]
    distances = crowding_distance(front, lambda x: x)
    assert distances[0] == float("inf")  # extreme on objective 0 (and 1)
    assert distances[2] == float("inf")  # extreme on objective 0 (and 1)
    assert distances[1] < float("inf")  # interior point


def test_select_survivors_keeps_a_nondominated_point_over_a_dominated_one_with_better_single_objective():
    # `cheap` has the worst objective-0 value in the set but is Pareto-optimal
    # (best objective-1 value); `dominated` is beaten in both objectives by
    # `best`, but ranks second-best on objective 0 alone. A survivor selection
    # that sorted by objective 0 alone would keep `dominated` over `cheap`;
    # nondominated-sort + crowding distance must not.
    best = (1.0, 9.0)
    dominated = (1.5, 9.5)  # dominated by `best`
    filler = (3.0, 7.0)
    cheap = (10.0, 0.5)  # worst objective 0, best objective 1 -- nondominated

    survivors = select_survivors([best, dominated, filler, cheap], lambda x: x, target_size=3)

    assert len(survivors) == 3
    assert cheap in survivors
    assert dominated not in survivors
