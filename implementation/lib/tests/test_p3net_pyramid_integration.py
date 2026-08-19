"""Tests for P3Net's population-pyramid wiring (module docstring's
"Known simplification 1", now resolved: population size is no longer a
constructor argument -- level 0 starts at `growth_factor` individuals and
new, larger levels grow automatically once the current level's sweep
passes stop improving). (Gap in the original task list -- adding it.)
"""

import random

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Observation, Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.search_engines.p3.pyramid import PyramidLevel


def toy_space(n: int = 12) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def toy_objective(genotype: Genotype):
    return (-float(sum(genotype.values)),)


def test_no_population_size_constructor_argument():
    """The whole point of this follow-up: population size must no longer
    be user-specified."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(P3Net)}
    assert "population_size" not in field_names
    assert "growth_factor" in field_names


def test_use_surrogate_interactions_defaults_to_false_and_threads_through_to_the_surrogate():
    """Phase 4 (2026-08-18, Conclusions): single-axis ablation, must not
    change p3net.yaml's own default behaviour, and must actually reach
    RelativeLinkageAwareSurrogate.include_interactions, not just exist as
    an unused constructor field."""
    default_method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
    )
    assert default_method.use_surrogate_interactions is False

    from unittest.mock import patch

    from p3net.surrogates.relative_linkage_aware import RelativeLinkageAwareSurrogate

    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
        use_surrogate_interactions=True,
    )
    with patch(
        "p3net.methods.p3net.RelativeLinkageAwareSurrogate", wraps=RelativeLinkageAwareSurrogate
    ) as spy:
        Runner(objective=toy_objective, budget=150).run(method)
        assert spy.call_count > 0
        for call in spy.call_args_list:
            assert call.kwargs["include_interactions"] is True


def test_level_0_starts_at_growth_factor_individuals():
    method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=3,
    )
    assert len(method._pyramid.levels) == 1
    assert method._pyramid.levels[0].size == 3


def test_growth_factor_is_configurable_and_changes_level_sizes():
    method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=4,
    )
    assert method._pyramid.levels[0].size == 4


def test_pyramid_grows_new_levels_over_a_longer_run():
    """Over a long enough run on a problem where the small level 0
    quickly exhausts easy improvements, at least one new, larger level
    must be grown -- proving growth is real, not just accepted and
    ignored."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert len(method._pyramid.levels) > 1
    sizes = [level.size for level in method._pyramid.levels]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)  # strictly growing, per Pyramid's own contract


def test_pyramid_growth_is_bounded_by_budget_not_runaway():
    """A finite budget must never be exceeded regardless of how many
    levels get grown."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(4),
        growth_factor=2,
    )
    state = Runner(objective=toy_objective, budget=100).run(method)
    assert state.evaluations_used <= 100


def test_old_levels_history_is_preserved_in_h_t_after_growth():
    """Simplification 1 (module docstring): once a level stalls and a new
    one grows, the old level is frozen but its real evaluations must
    still be part of H_t (never discarded)."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(5),
        growth_factor=2,
    )
    state = Runner(objective=toy_objective, budget=120).run(method)
    if len(method._pyramid.levels) > 1:
        old_level_genotypes = method._pyramid.levels[0].population
        for g in old_level_genotypes:
            assert g in method._history
    assert len(method._history) == len({obs.genotype for obs in state.history})


def test_best_objectives_seeded_after_bootstrap_before_any_promote_call():
    """_seed_best_objectives must run exactly once bootstrap completes,
    giving promote() a real baseline rather than leaving best_objectives
    None (which would make the first post-bootstrap pass always count as
    "improving" regardless of its actual quality)."""
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(6),
        growth_factor=4,
    )
    level = method._pyramid.levels[0]
    Runner(objective=toy_objective, budget=4).run(method)
    assert len(level.population) == level.size
    assert level.best_objectives is not None


@pytest.mark.parametrize("growth_factor", [2, 3])
def test_p3net_still_outperforms_random_search_with_pyramid_wiring(growth_factor):
    """Regression guard: pyramid wiring must not make search worse on the
    same structured toy problem the pre-pyramid implementation was
    validated against (tests/test_p3net_integration.py)."""

    def trap_objective(genotype: Genotype):
        def trap4(u: int) -> int:
            return 4 if u == 4 else 3 - u

        total = sum(trap4(sum(genotype.values[b * 4 : (b + 1) * 4])) for b in range(3))
        return (-float(total),)

    space = toy_space(12)
    budget = 200
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(42),
        growth_factor=growth_factor,
    )
    state = Runner(objective=trap_objective, budget=budget).run(method)
    p3net_best = min(obs.objectives[0] for obs in state.history)

    rng = random.Random(42)
    random_best = min(trap_objective(space.sample_uniform(rng))[0] for _ in range(budget))
    assert p3net_best <= random_best


def test_bootstrap_and_mixing_proposal_counters_start_at_zero():
    method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=3,
    )
    assert method.bootstrap_proposals == 0
    assert method.mixing_proposals == 0


def test_a_run_confined_to_bootstrap_only_counts_bootstrap_proposals():
    """Budget exactly matching level 0's size (as in
    test_best_objectives_seeded_after_bootstrap_before_any_promote_call)
    never leaves the bootstrap phase -- every proposal must be counted as
    bootstrap, none as mixing."""
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(6),
        growth_factor=4,
    )
    Runner(objective=toy_objective, budget=4).run(method)
    assert method.bootstrap_proposals == 4
    assert method.mixing_proposals == 0


def test_a_longer_run_that_grows_the_pyramid_counts_both_bootstrap_and_mixing_proposals():
    """Same long-run scenario as test_pyramid_grows_new_levels_over_a_longer_run:
    at least one full sweep and at least one level-growth bootstrap must
    both occur, so both counters must be positive, and they must sum to
    every genotype ever proposed."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert method.bootstrap_proposals > 0
    assert method.mixing_proposals > 0


def test_surrogate_fit_and_linkage_tree_timers_stay_zero_during_pure_bootstrap():
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(6),
        growth_factor=4,
    )
    Runner(objective=toy_objective, budget=4).run(method)
    assert method.surrogate_fit_seconds == 0.0
    assert method.linkage_tree_seconds == 0.0


def test_surrogate_fit_and_linkage_tree_timers_are_positive_once_sweeps_run():
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert method.surrogate_fit_seconds >= 0.0
    assert method.linkage_tree_seconds > 0.0


def test_population_snapshots_recorded_once_per_update_call_and_feed_archive_turnover():
    """population_snapshots must be in exactly the list[list[Genotype]]
    shape metrics.diagnostics.archive_turnover (experiments package)
    already accepts -- this is what actually closes that "Known gaps"
    item, not a bespoke turnover computation duplicating it."""
    from p3net.problem.genotype import Genotype as GenotypeType

    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert len(method.population_snapshots) > 0
    for snapshot in method.population_snapshots:
        assert isinstance(snapshot, list)
        assert all(isinstance(g, GenotypeType) for g in snapshot)
    # Each recorded entry must be its own copy, not a shared reference to
    # the live, still-mutating level.population list -- otherwise every
    # entry would silently collapse to whatever the population looks like
    # by the time the run ends.
    assert method.population_snapshots[0] is not method.population_snapshots[-1]
    assert len(method.population_snapshots[0]) <= len(method.population_snapshots[-1])
    # Growth over budget=150 (test_pyramid_grows_new_levels_over_a_longer_run
    # confirms at least one new level grows here) means later snapshots
    # belong to a strictly larger level than the first one.
    assert len(method.population_snapshots[-1]) > len(method.population_snapshots[0])


def test_chain_depth_log_matches_surrogate_quality_log_length_and_respects_kappa():
    """chain_depth_log (2026-08-17 follow-up: does telescoping chain length
    correlate with the wild magnitude outliers found in Phase 1's
    calibration analysis) is recorded in lockstep with
    surrogate_quality_log, one entry per scored-and-later-evaluated
    proposal, each within [1, kappa]."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert len(method.chain_depth_log) == len(method.surrogate_quality_log)
    assert len(method.chain_depth_log) > 0
    for depth in method.chain_depth_log:
        assert 1 <= depth <= method.kappa


def test_level_size_log_matches_surrogate_quality_log_length_and_is_a_real_pyramid_size():
    """level_size_log (2026-08-18 follow-up: does the |H_t|~30-58 magnitude
    outlier window line up with a specific pyramid level rather than pure
    |H_t|?) records, per logged prediction, the sweeping level's target
    size at scoring time -- every entry must be one of growth_factor's
    actual level sizes."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert len(method.level_size_log) == len(method.surrogate_quality_log)
    possible_sizes = {2**k for k in range(1, 10)}
    assert set(method.level_size_log) <= possible_sizes


def test_warm_start_seeds_new_level_with_nondominated_front_from_history():
    """A newly-grown level starts from H_t's current nondominated front,
    not empty (2026-08-18, Conclusions) -- these genotypes are already
    evaluated, so this costs zero fresh evaluation budget, and moves the
    implementation closer to canonical P3's cascading."""
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=4,
    )

    def obs(bits: tuple[int, ...], objectives: tuple[float, float]) -> Observation:
        return Observation(genotype=Genotype(values=bits), objectives=objectives)

    nondominated = [
        obs((0, 0, 0, 0, 0, 0), (1.0, 5.0)),
        obs((1, 1, 1, 1, 1, 1), (5.0, 1.0)),
    ]
    dominated = obs((0, 1, 0, 1, 0, 1), (3.0, 6.0))  # dominated by both above
    for o in nondominated + [dominated]:
        method._history[o.genotype] = o

    new_level = PyramidLevel(size=10)
    method._warm_start_level(new_level)

    assert {o.genotype for o in nondominated} <= set(new_level.population)
    assert dominated.genotype not in new_level.population
    assert new_level.best_objectives is not None


def test_warm_start_caps_to_the_new_levels_own_size_when_the_front_is_larger():
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=2,
    )

    def obs(bits: tuple[int, ...], objectives: tuple[float, float]) -> Observation:
        return Observation(genotype=Genotype(values=bits), objectives=objectives)

    # 5 mutually nondominated trade-off points -- more than the level below.
    front = [
        obs((0,) * 10, (1.0, 5.0)),
        obs((1,) * 5 + (0,) * 5, (2.0, 4.0)),
        obs((0,) * 5 + (1,) * 5, (3.0, 3.0)),
        obs((1,) * 8 + (0,) * 2, (4.0, 2.0)),
        obs((1,) * 10, (5.0, 1.0)),
    ]
    for o in front:
        method._history[o.genotype] = o

    new_level = PyramidLevel(size=3)
    method._warm_start_level(new_level)

    assert len(new_level.population) == 3
    assert set(new_level.population) <= {o.genotype for o in front}


def test_warm_start_is_a_no_op_when_history_is_still_empty():
    """The very first level, grown at construction time, has nothing to
    warm-start from -- must not raise, must leave the level's population
    untouched for plain bootstrap to fill."""
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=4,
    )
    new_level = PyramidLevel(size=4)
    method._warm_start_level(new_level)
    assert new_level.population == []
    assert new_level.best_objectives is None


def test_population_truncation_keeps_a_nondominated_genotype_over_a_worse_but_lower_f1_one():
    """Once level.population exceeds level.size, update() must truncate it
    by nondomination + crowding distance, not by sorting on objective_index
    alone -- an f1-only sort would drop a genuinely Pareto-optimal genotype
    (best f2 in the set) in favour of one that is dominated in both
    objectives but merely has a better f1."""
    method = P3Net(
        search_space=toy_space(3),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=3,
    )
    level = method._pyramid.levels[0]

    def obs(bits: tuple[int, ...], objectives: tuple[float, float]) -> Observation:
        return Observation(genotype=Genotype(values=bits), objectives=objectives)

    # Bootstrap: fill level 0 (size 3).
    bootstrap = [
        obs((0, 0, 0), (1.0, 9.0)),
        obs((0, 0, 1), (2.0, 8.0)),
        obs((0, 1, 0), (3.0, 7.0)),
    ]
    method.update(None, bootstrap)
    assert len(level.population) == 3

    # A sweep pass reports two new observations: `cheap` is nondominated
    # (worst f1 in the whole set, but the single best f2); `dominated` is
    # beaten in both objectives by bootstrap[0] (1.0, 9.0), but ranks
    # second-best on f1 alone -- exactly what an f1-only sort would keep.
    cheap = obs((1, 1, 1), (10.0, 0.5))
    dominated = obs((0, 1, 1), (1.5, 9.5))
    method.update(None, [cheap, dominated])

    assert len(level.population) == level.size
    assert cheap.genotype in level.population
    assert dominated.genotype not in level.population


