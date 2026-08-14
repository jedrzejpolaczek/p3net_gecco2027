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

    # improving promotion: level 0 is not stalled
    pyramid.promote(0, Genotype(values=(0,)), (1.0,))
    assert pyramid.maybe_grow() is None

    # non-improving promotion (dominated): level 0 becomes stalled
    pyramid.promote(0, Genotype(values=(1,)), (2.0,))
    assert pyramid.all_stalled
    level1 = pyramid.maybe_grow()
    assert level1 is not None
    assert len(pyramid.levels) == 2
    assert level1.size > level0.size


def test_promotion_requires_a_real_objective_value_per_accepted_step():
    pyramid = Pyramid()
    pyramid.add_level()
    improved = pyramid.promote(0, Genotype(values=(0,)), (1.0,))
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
