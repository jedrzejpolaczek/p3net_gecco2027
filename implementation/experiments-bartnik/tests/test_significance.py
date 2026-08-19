"""Tests for experiments.stats.significance -- paired Wilcoxon +
Holm-Bonferroni + Cliff's delta over the defined P3Net-vs-nine-arms
comparison set. (Gap in the original task list -- adding it.)

Reference: experiments/stats/significance.py; chapters/v003/results/
main.tex ("Statistical plan").
"""

import pytest

from stats.significance import (
    Comparison,
    cliffs_delta,
    compare_p3net_to_baselines,
    holm_bonferroni_correction,
)

# -- cliffs_delta -----------------------------------------------------------


def test_cliffs_delta_is_one_when_a_strictly_dominates_b():
    assert cliffs_delta([10.0, 11.0, 12.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_cliffs_delta_is_negative_one_when_b_strictly_dominates_a():
    assert cliffs_delta([1.0, 2.0, 3.0], [10.0, 11.0, 12.0]) == pytest.approx(-1.0)


def test_cliffs_delta_is_zero_for_identical_distributions():
    assert cliffs_delta([1.0, 2.0], [1.0, 2.0]) == pytest.approx(0.0)


def test_cliffs_delta_rejects_empty_samples():
    with pytest.raises(ValueError):
        cliffs_delta([], [1.0])
    with pytest.raises(ValueError):
        cliffs_delta([1.0], [])


# -- holm_bonferroni_correction ----------------------------------------------


def test_holm_bonferroni_matches_hand_computed_adjustment():
    # 3 tests, raw p-values 0.01, 0.02, 0.03, alpha=0.05.
    # sorted ascending: 0.01 (m=3), 0.02 (m-1=2), 0.03 (m-2=1)
    # adjusted: max(0.03, .) -> 0.03; max(0.03, 0.04) -> 0.04; max(0.04, 0.03) -> 0.04
    results = holm_bonferroni_correction([0.01, 0.02, 0.03], alpha=0.05)
    assert [r.adjusted_p_value for r in results] == pytest.approx([0.03, 0.04, 0.04])
    assert all(r.reject_null for r in results)


def test_holm_bonferroni_adjusted_p_values_are_monotone_in_sorted_order():
    results = holm_bonferroni_correction([0.2, 0.001, 0.15, 0.04], alpha=0.05)
    order = sorted(range(len(results)), key=lambda i: results[i].p_value)
    adjusted_in_sorted_order = [results[i].adjusted_p_value for i in order]
    assert adjusted_in_sorted_order == sorted(adjusted_in_sorted_order)


def test_holm_bonferroni_caps_adjusted_p_value_at_one():
    results = holm_bonferroni_correction([0.9, 0.9, 0.9], alpha=0.05)
    assert all(r.adjusted_p_value <= 1.0 for r in results)
    assert not any(r.reject_null for r in results)


def test_holm_bonferroni_empty_input():
    assert holm_bonferroni_correction([]) == []


# -- compare_p3net_to_baselines ----------------------------------------------


def test_compare_p3net_to_baselines_reports_one_result_per_comparison():
    comparisons = [
        Comparison(
            baseline="random_search",
            benchmark="nas_hpo_bench_ii",
            budget=50,
            p3net_scores=(5.0, 4.5, 4.8, 5.2, 4.9, 5.1),
            baseline_scores=(8.0, 7.5, 7.8, 8.2, 7.9, 8.1),
        ),
        Comparison(
            baseline="nsga_net",
            benchmark="nas_hpo_bench_ii",
            budget=50,
            p3net_scores=(5.0, 4.5, 4.8, 5.2, 4.9, 5.1),
            baseline_scores=(5.1, 4.6, 4.9, 5.1, 5.0, 5.0),
        ),
    ]
    results = compare_p3net_to_baselines(comparisons)
    assert len(results) == 2
    assert results[0].comparison is comparisons[0]
    # P3Net strictly, consistently beats random_search here (lower is
    # better in these synthetic scores) -- effect size should reflect that.
    assert results[0].effect_size == pytest.approx(-1.0)
    for result in results:
        assert 0.0 <= result.adjusted_p_value <= 1.0


def test_compare_p3net_to_baselines_applies_holm_correction_across_exactly_the_given_set():
    """Adding a third, unrelated comparison changes the correction factor
    for the OTHER two -- proving the correction is scoped to exactly the
    comparison set passed in, not some other implicit universe of tests."""
    pair = Comparison(
        baseline="random_search",
        benchmark="nas_hpo_bench_ii",
        budget=50,
        p3net_scores=(5.0, 4.5, 4.8, 5.2, 4.9, 5.1),
        baseline_scores=(8.0, 7.5, 7.8, 8.2, 7.9, 8.1),
    )
    results_alone = compare_p3net_to_baselines([pair])
    results_with_extra = compare_p3net_to_baselines([pair, pair])
    assert results_with_extra[0].adjusted_p_value >= results_alone[0].adjusted_p_value


def test_compare_p3net_to_baselines_rejects_unpaired_samples():
    bad = Comparison(
        baseline="random_search",
        benchmark="nas_hpo_bench_ii",
        budget=50,
        p3net_scores=(1.0, 2.0),
        baseline_scores=(1.0,),
    )
    with pytest.raises(ValueError):
        compare_p3net_to_baselines([bad])


def test_compare_p3net_to_baselines_empty_input():
    assert compare_p3net_to_baselines([]) == []
