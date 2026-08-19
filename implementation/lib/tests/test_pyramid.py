"""Tests for p3net.search_engines.p3.pyramid. (Gap in the original task
list -- adding it since pyramid growth/promotion has real, testable
logic.)"""

from p3net.problem.genotype import Genotype
from p3net.search_engines.p3.pyramid import Pyramid


def test_new_level_added_only_when_all_existing_levels_stalled():
    pyramid = Pyramid()
    level0 = pyramid.maybe_grow()
    assert level0 is not None
    assert len(pyramid.levels) == 1

    # not stalled yet (nothing promoted) -> no growth
    assert pyramid.maybe_grow() is None
    assert len(pyramid.levels) == 1

    # improving promotion (nothing promoted yet -> trivially improves): level 0 is not stalled
    pyramid.promote(0, Genotype(values=(0,)), (1.0,), population_objectives=[])
    assert pyramid.maybe_grow() is None

    # non-improving promotion (dominated by what's already promoted): level 0 becomes stalled
    pyramid.promote(0, Genotype(values=(1,)), (2.0,), population_objectives=[(1.0,)])
    assert pyramid.all_stalled
    level1 = pyramid.maybe_grow()
    assert level1 is not None
    assert len(pyramid.levels) == 2
    assert level1.size > level0.size


def test_promotion_requires_a_real_objective_value_per_accepted_step():
    pyramid = Pyramid()
    pyramid.add_level()
    improved = pyramid.promote(0, Genotype(values=(0,)), (1.0,), population_objectives=[])
    assert improved is True
    assert pyramid.levels[0].best_objectives == (1.0,)
    assert len(pyramid.levels[0].population) == 1


def test_levels_have_strictly_growing_size():
    pyramid = Pyramid(growth_factor=2)
    sizes = [pyramid.add_level().size for _ in range(4)]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)


def test_all_stalled_is_false_with_no_levels():
    pyramid = Pyramid()
    assert pyramid.all_stalled is False


def test_is_stalled_reports_per_level_state():
    pyramid = Pyramid()
    pyramid.add_level()
    assert pyramid.is_stalled(0) is False
    pyramid.promote(0, Genotype(values=(0,)), (1.0,), population_objectives=[])  # improving
    assert pyramid.is_stalled(0) is False
    pyramid.promote(0, Genotype(values=(1,)), (2.0,), population_objectives=[(1.0,)])  # dominated
    assert pyramid.is_stalled(0) is True


# -- hypervolume-contribution stall criterion (2026-08-18) ------------------
#
# Conclusions, "population-pyramid bootstrap share": strict Pareto dominance
# against a single incumbent degenerates, in 2D, to "did this one sweep pass
# fail to beat the incumbent on BOTH objectives simultaneously" -- rare, so
# levels stalled almost immediately, forcing runaway geometric growth. These
# tests establish the replacement criterion's own defining behaviour.


def test_a_nondominated_but_not_strictly_dominating_point_now_counts_as_improving():
    """The whole point of softening from strict dominance to hypervolume
    contribution: a genuinely useful trade-off point that neither
    dominates nor is dominated by the incumbent used to mark the level
    stalled under the old rule. It must not anymore."""
    pyramid = Pyramid()
    pyramid.add_level()
    pyramid.promote(0, Genotype(values=(0,)), (1.0, 5.0), population_objectives=[])
    # (0.5, 6.0): better f1, worse f2 -- neither dominates nor is dominated
    # by (1.0, 5.0) under strict Pareto dominance, but it adds real
    # hypervolume (extends the front rather than being absorbed by it).
    improved = pyramid.promote(
        0, Genotype(values=(1,)), (0.5, 6.0), population_objectives=[(1.0, 5.0)]
    )
    assert improved is True
    assert pyramid.is_stalled(0) is False


def test_a_strictly_dominated_point_still_does_not_improve():
    pyramid = Pyramid()
    pyramid.add_level()
    pyramid.promote(0, Genotype(values=(0,)), (1.0, 5.0), population_objectives=[])
    improved = pyramid.promote(
        0, Genotype(values=(1,)), (2.0, 6.0), population_objectives=[(1.0, 5.0)]
    )
    assert improved is False
    assert pyramid.is_stalled(0) is True


def test_a_duplicate_of_an_existing_point_does_not_improve():
    """Adding a point with the exact same objectives as one already in
    the population contributes zero additional hypervolume."""
    pyramid = Pyramid()
    pyramid.add_level()
    pyramid.promote(0, Genotype(values=(0,)), (1.0, 5.0), population_objectives=[])
    improved = pyramid.promote(
        0, Genotype(values=(1,)), (1.0, 5.0), population_objectives=[(1.0, 5.0)]
    )
    assert improved is False
