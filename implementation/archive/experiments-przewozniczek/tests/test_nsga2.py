"""Tests for search_engines.nsga2 -- fast nondominated sort and crowding
distance. (Gap in the original task list -- adding it, since this is real
algorithmic code, not glue.)"""

import pytest

from search_engines.nsga2.crowding_distance import crowding_distance
from search_engines.nsga2.nondominated_sort import fast_nondominated_sort


def test_nondominated_sort_produces_correct_ranks_on_a_chain():
    # (1,1) dominates (2,2), which dominates (3,3): three strict ranks.
    items = [(1.0, 1.0), (2.0, 2.0), (3.0, 3.0)]
    fronts = fast_nondominated_sort(items, lambda x: x)
    assert fronts == [[(1.0, 1.0)], [(2.0, 2.0)], [(3.0, 3.0)]]


def test_nondominated_sort_groups_mutually_nondominated_points_in_one_front():
    # (1,4),(2,3),(3,2),(4,1) are mutually nondominated -- one front.
    items = [(1.0, 4.0), (2.0, 3.0), (3.0, 2.0), (4.0, 1.0)]
    fronts = fast_nondominated_sort(items, lambda x: x)
    assert len(fronts) == 1
    assert set(fronts[0]) == set(items)


def test_nondominated_sort_mixed_case_two_fronts():
    # (1,1) dominates (2,2) and (3,1); (3,1) and (1,4) are mutually
    # nondominated with each other and are only dominated by (1,1).
    front0_point = (1.0, 1.0)
    dominated_a = (2.0, 2.0)
    dominated_b = (
        3.0,
        1.0,
    )  # dominated only via tie-break: (1,1) dominates it (1<=3, 1<=1, not equal)
    items = [front0_point, dominated_a, dominated_b]
    fronts = fast_nondominated_sort(items, lambda x: x)
    assert fronts[0] == [front0_point]
    assert set(fronts[1]) == {dominated_a, dominated_b}


def test_crowding_distance_boundary_points_are_infinite():
    front = [(1.0, 4.0), (2.0, 3.0), (3.0, 2.0), (4.0, 1.0)]
    distances = crowding_distance(front, lambda x: x)
    assert distances[0] == float("inf")  # (1,4): boundary on objective 0
    assert distances[3] == float("inf")  # (4,1): boundary on objective 0 (and 1)


def test_crowding_distance_matches_hand_computed_value():
    # Classic textbook example: 4 points on an anti-diagonal curve.
    front = [(1.0, 4.0), (2.0, 3.0), (3.0, 2.0), (4.0, 1.0)]
    distances = crowding_distance(front, lambda x: x)
    # Hand-derived: middle two points each accumulate 2/3 + 2/3 = 4/3
    # across the two objectives (span = 3 in both).
    assert distances[1] == pytest.approx(4 / 3)
    assert distances[2] == pytest.approx(4 / 3)


def test_crowding_distance_empty_front_returns_empty():
    assert crowding_distance([], lambda x: x) == {}


def test_crowding_distance_single_point_front_has_no_finite_distance_issue():
    distances = crowding_distance([(1.0, 1.0)], lambda x: x)
    assert distances[0] == float("inf")
