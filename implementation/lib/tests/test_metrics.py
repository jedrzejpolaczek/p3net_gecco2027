"""Tests for p3net.metrics.hypervolume and p3net.metrics.igd_plus."""

import pytest

from p3net.metrics.hypervolume import hypervolume, hypervolume_relative_to_best_known_front
from p3net.metrics.igd_plus import igd_plus


def test_hypervolume_known_small_example():
    assert hypervolume([(1.0, 1.0)], reference=(2.0, 2.0)) == pytest.approx(1.0)


def test_hypervolume_two_nondominated_points_known_value():
    # reference (4,4); points (1,3) and (3,1): union of dominated boxes
    # = 3 + 3 - overlap(1) = 5, worked out by hand via inclusion-exclusion.
    hv = hypervolume([(1.0, 3.0), (3.0, 1.0)], reference=(4.0, 4.0))
    assert hv == pytest.approx(5.0)


def test_hypervolume_dominated_point_does_not_change_the_result():
    # (2,2) is dominated by (1,1) and contributes nothing.
    hv_with = hypervolume([(1.0, 1.0), (2.0, 2.0)], reference=(3.0, 3.0))
    hv_without = hypervolume([(1.0, 1.0)], reference=(3.0, 3.0))
    assert hv_with == pytest.approx(hv_without)


def test_hypervolume_rejects_reference_dominated_by_a_point():
    with pytest.raises(ValueError):
        hypervolume([(5.0, 5.0)], reference=(4.0, 4.0))


def test_hypervolume_empty_points_is_zero():
    assert hypervolume([], reference=(1.0, 1.0)) == 0.0


def test_hypervolume_generalises_to_three_objectives():
    hv = hypervolume([(0.0, 0.0, 0.0)], reference=(2.0, 2.0, 2.0))
    assert hv == pytest.approx(8.0)


def test_hypervolume_relative_to_best_known_front():
    reference = (4.0, 4.0)
    best_known = [(1.0, 3.0), (3.0, 1.0)]
    same_as_best = hypervolume_relative_to_best_known_front(best_known, best_known, reference)
    assert same_as_best == pytest.approx(1.0)

    worse_points = [(2.0, 3.5)]
    relative = hypervolume_relative_to_best_known_front(worse_points, best_known, reference)
    assert 0.0 <= relative < 1.0


def test_igd_plus_zero_when_approximation_equals_oracle_front():
    oracle = [(1.0, 3.0), (3.0, 1.0)]
    assert igd_plus(oracle, oracle) == pytest.approx(0.0)


def test_igd_plus_known_value():
    oracle = [(0.0, 0.0)]
    approximation = [(3.0, 4.0)]
    assert igd_plus(approximation, oracle) == pytest.approx(5.0)


def test_igd_plus_ignores_being_better_than_oracle():
    # IGD+ only counts how much WORSE the approximation is; being better
    # in one objective doesn't add distance.
    oracle = [(2.0, 2.0)]
    approximation = [(1.0, 5.0)]  # better in obj 0, worse in obj 1
    assert igd_plus(approximation, oracle) == pytest.approx(3.0)


def test_igd_plus_generalises_to_three_objectives():
    oracle = [(0.0, 0.0, 0.0)]
    approximation = [(1.0, 2.0, 2.0)]
    assert igd_plus(approximation, oracle) == pytest.approx((1.0**2 + 2.0**2 + 2.0**2) ** 0.5)


def test_igd_plus_rejects_empty_inputs():
    with pytest.raises(ValueError):
        igd_plus([], [(1.0,)])
    with pytest.raises(ValueError):
        igd_plus([(1.0,)], [])
