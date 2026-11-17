"""Tests for experiments.reporting -- fixed-budget summary table,
sensitivity/convergence/Pareto-progression/diagnostics figures, and
scripts/generate_report.py's end-to-end wiring. (Gap in the original task
list -- adding it, per the plan's own note that reporting/tables.py and
reporting/plots.py are covered by a smoke check that they run without
error and produce the expected shape given synthetic run data, rather than
the usual "checkable value" unit test.)
"""

from __future__ import annotations

import json
import random

import pytest
from matplotlib.figure import Figure

from reporting import (
    RawRun,
    SensitivityPoint,
    construct_best_known_front,
    convergence_curve_figure,
    duplication_rate_figure,
    fixed_budget_summary_table,
    load_raw_run,
    load_raw_runs,
    nadir_reference_point,
    p3_alone_sweep_completion_table,
    pareto_front_progression_figure,
    render_summary_table_markdown,
    render_sweep_completion_table_markdown,
    sensitivity_figure,
    surrogate_calibration_figure,
    surrogate_quality_figure,
)
from scripts import run_experiment
from scripts.generate_report import generate_report


def _run(method: str, search_space: str, budget: int, seed: int, points, **diagnostics) -> RawRun:
    from p3net.harness.runner import Observation
    from p3net.problem.genotype import Genotype

    history = tuple(
        Observation(genotype=Genotype(values=(f"g{i}",)), objectives=tuple(p))
        for i, p in enumerate(points)
    )
    return RawRun(
        method=method,
        search_space=search_space,
        budget=budget,
        seed=seed,
        evaluations_used=len(points),
        history=history,
        diagnostics=diagnostics,
    )


# -- reporting._common --------------------------------------------------


def test_construct_best_known_front_pools_and_filters_dominated_points():
    runs = [
        _run("a", "space", 10, 1, [(1.0, 5.0), (3.0, 3.0)]),
        # (2.0, 5.0) is dominated by (1.0, 5.0): 1<=2 and 5<=5, strictly
        # better in the first objective -- must be filtered out.
        _run("b", "space", 10, 1, [(2.0, 5.0), (0.5, 6.0)]),
    ]
    front = construct_best_known_front(runs)
    assert (2.0, 5.0) not in front
    assert set(front) == {(1.0, 5.0), (3.0, 3.0), (0.5, 6.0)}


def test_construct_best_known_front_empty_for_no_runs():
    assert construct_best_known_front([]) == []


def test_construct_best_known_front_2d_matches_generic_pareto_front():
    from p3net.problem.objectives import pareto_front

    rng = random.Random(2)
    points = [(rng.uniform(0.0, 10.0), rng.uniform(0.0, 10.0)) for _ in range(200)]
    runs = [_run("a", "space", 10, 1, points)]

    fast = set(construct_best_known_front(runs))
    exact = set(pareto_front(points, lambda p: p))
    assert fast == exact


def test_construct_best_known_front_2d_collapses_exact_duplicates():
    runs = [
        _run("a", "space", 10, 1, [(1.0, 1.0), (1.0, 1.0), (2.0, 2.0)]),
    ]
    front = construct_best_known_front(runs)
    assert front == [(1.0, 1.0)]


def test_construct_best_known_front_completes_on_a_realistic_pooled_scale():
    rng = random.Random(3)
    # This project's real R=30, 4-budget-tier grid pools ~230,000 points
    # per benchmark -- not a timing assertion (flaky by nature), but if
    # this regressed back to the generic O(n^2) pareto_front, the test
    # suite itself would take an impractically long time to finish, which
    # is the real regression signal.
    points = [(rng.uniform(0.0, 100.0), rng.uniform(0.0, 100.0)) for _ in range(50_000)]
    runs = [_run("a", "space", 10, 1, points)]
    front = construct_best_known_front(runs)
    assert len(front) > 0
    assert len(front) < 50_000  # a real front is much smaller than the pool


def test_nadir_reference_point_is_coordinatewise_max_plus_slack():
    ref = nadir_reference_point([(1.0, 5.0), (3.0, 2.0)], slack=0.1)
    assert ref == pytest.approx((3.1, 5.1))


def test_nadir_reference_point_rejects_empty_and_mismatched_dims():
    with pytest.raises(ValueError):
        nadir_reference_point([])
    with pytest.raises(ValueError):
        nadir_reference_point([(1.0,), (1.0, 2.0)])


def test_load_raw_run_round_trips_through_persist_run(tmp_path, monkeypatch):
    class FakeMethod:
        sweeps_completed = 3

    class FakeCache:
        duplication_rate = 0.25

    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import Genotype

    state = RunState(
        evaluations_used=2,
        history=[
            Observation(genotype=Genotype(values=("x",)), objectives=(1.0, 2.0)),
            Observation(genotype=Genotype(values=("y",)), objectives=(0.5, 3.0)),
        ],
    )
    monkeypatch.setattr(run_experiment, "RESULTS_DIR", tmp_path)
    result = run_experiment.RunResult(state=state, cache=FakeCache(), method=FakeMethod())
    out_path = run_experiment.persist_run(
        result, method_name="p3net", search_space_name="space", budget=10, seed=1
    )

    raw = load_raw_run(out_path)
    assert raw.method == "p3net"
    assert raw.budget == 10
    assert raw.seed == 1
    assert raw.objectives == ((1.0, 2.0), (0.5, 3.0))
    assert raw.diagnostics == {"duplication_rate": 0.25, "sweeps_completed": 3}


def test_load_raw_run_defaults_diagnostics_for_old_files_without_the_key(tmp_path):
    path = tmp_path / "old.json"
    path.write_text(
        json.dumps(
            {
                "method": "random_search",
                "search_space": "space",
                "budget": 5,
                "seed": 1,
                "evaluations_used": 1,
                "history": [{"genotype": ["a"], "objectives": [1.0, 2.0]}],
            }
        ),
        encoding="utf-8",
    )
    raw = load_raw_run(path)
    assert raw.diagnostics == {}


def test_load_raw_runs_reads_every_json_file(tmp_path):
    for i in range(3):
        (tmp_path / f"run{i}.json").write_text(
            json.dumps(
                {
                    "method": "random_search",
                    "search_space": "space",
                    "budget": 5,
                    "seed": i,
                    "evaluations_used": 1,
                    "history": [{"genotype": ["a"], "objectives": [1.0, 2.0]}],
                }
            ),
            encoding="utf-8",
        )
    runs = load_raw_runs(tmp_path)
    assert len(runs) == 3


# -- reporting.tables -----------------------------------------------------


def _paired_runs():
    """p3net clearly better than "baseline" (smaller objectives, closer to
    the origin) across 3 matched seeds, same search_space/budget."""
    runs = []
    for seed in (1, 2, 3):
        runs.append(_run("p3net", "space", 100, seed, [(1.0, 1.0), (0.9, 1.2)]))
        runs.append(_run("baseline", "space", 100, seed, [(5.0, 5.0), (4.8, 5.5)]))
    return runs


def test_fixed_budget_summary_table_reports_median_iqr_and_significance():
    rows = fixed_budget_summary_table(_paired_runs())
    by_method = {r.method: r for r in rows}
    assert by_method["p3net"].n_runs == 3
    assert by_method["baseline"].n_runs == 3
    # p3net's front is much closer to the pooled best-known front than
    # baseline's -- its relative-hypervolume score should be higher.
    assert by_method["p3net"].median > by_method["baseline"].median
    assert by_method["baseline"].adjusted_p_value is not None
    assert by_method["baseline"].effect_size is not None
    # P3Net is the reference for every comparison, never compared to itself.
    assert by_method["p3net"].adjusted_p_value is None


def test_fixed_budget_summary_table_skips_significance_without_enough_paired_seeds():
    runs = [
        _run("p3net", "space", 100, 1, [(1.0, 1.0)]),
        _run("baseline", "space", 100, 1, [(5.0, 5.0)]),
    ]
    rows = fixed_budget_summary_table(runs)
    baseline_row = next(r for r in rows if r.method == "baseline")
    assert baseline_row.adjusted_p_value is None


def test_fixed_budget_summary_table_uses_igd_plus_when_oracle_front_supplied():
    runs = [
        _run("p3net", "space", 100, 1, [(1.0, 1.0)]),
        _run("p3net", "space", 100, 2, [(1.1, 1.1)]),
    ]
    oracle_front = [(0.0, 0.0), (2.0, 2.0)]
    rows = fixed_budget_summary_table(runs, oracle_fronts={"space": oracle_front})
    assert all(r.metric == "igd_plus" for r in rows)


def test_fixed_budget_summary_table_empty_input():
    assert fixed_budget_summary_table([]) == []


def test_fixed_budget_summary_table_scopes_holm_correction_per_cell():
    """Regression test: the comparison set for Holm-Bonferroni correction is
    "P3Net vs. each other arm, per benchmark and per budget tier" (Statistical
    plan) -- i.e. one correction family PER (search_space, budget) cell, not
    one family across every cell passed to this function. A cell's own
    significance must not depend on what other, unrelated cells happen to be
    included in the same call.

    Cell "A"/budget 10 has one baseline, completely separated from p3net
    across 6 paired seeds (exact two-sided Wilcoxon raw p = 2*(1/2)**6 =
    0.03125): with the correct m=1 family for that cell, this is significant
    at alpha=0.05 on its own. Cell "B"/budget 10 has three unrelated,
    perfectly-null baselines (raw p=1.0 each, by construction: exactly half
    the paired seeds favour each side). Pooling every cell's comparisons into
    one m=4 family before correcting -- the bug this test guards against --
    inflates cell A's adjusted p to 0.125, wrongly erasing its significance;
    scoping the correction to cell A alone must not.
    """
    runs = []
    # Cell A: p3net vs. "separated" -- p3net strictly ahead in every one of
    # 6 paired seeds.
    for seed in range(6):
        runs.append(_run("p3net", "A", 10, seed, [(1.0, 1.0)]))
        runs.append(_run("separated", "A", 10, seed, [(5.0, 5.0)]))
    # Cell B: p3net vs. three null baselines -- 6 paired seeds each, split
    # 3-3 so the paired Wilcoxon statistic is exactly at its median (raw
    # p=1.0), and a p3net row so the cell is picked up at all.
    for seed in range(6):
        p3net_point = (1.0, 1.0) if seed < 3 else (5.0, 5.0)
        runs.append(_run("p3net", "B", 10, seed, [p3net_point]))
        for baseline in ("null1", "null2", "null3"):
            baseline_point = (5.0, 5.0) if seed < 3 else (1.0, 1.0)
            runs.append(_run(baseline, "B", 10, seed, [baseline_point]))

    rows = fixed_budget_summary_table(runs)
    separated_row = next(r for r in rows if r.search_space == "A" and r.method == "separated")
    assert separated_row.adjusted_p_value == pytest.approx(0.03125)
    assert separated_row.reject_null is True


def test_render_summary_table_markdown_produces_a_pipe_table():
    rows = fixed_budget_summary_table(_paired_runs())
    text = render_summary_table_markdown(rows)
    assert text.startswith("| Method")
    assert "p3net" in text
    assert "baseline" in text


def test_p3_alone_sweep_completion_table_reads_persisted_diagnostic():
    runs = [
        _run("p3_alone", "space", 50, 1, [(1.0, 1.0)], sweeps_completed=2),
        _run("p3_alone", "space", 50, 2, [(1.0, 1.0)], sweeps_completed=4),
        _run("p3net", "space", 50, 1, [(1.0, 1.0)]),  # no sweeps_completed -- ignored
    ]
    rows = p3_alone_sweep_completion_table(runs)
    assert len(rows) == 1
    assert rows[0].median_sweeps_completed == 3
    assert rows[0].n_runs == 2


def test_render_sweep_completion_table_markdown_produces_a_pipe_table():
    rows = p3_alone_sweep_completion_table(
        [_run("p3_alone", "space", 50, 1, [(1.0, 1.0)], sweeps_completed=2)]
    )
    text = render_sweep_completion_table_markdown(rows)
    assert text.startswith("| Search space")


# -- reporting.plots -------------------------------------------------------


def _hypervolume_trace_by_full_recompute(objectives, reference):
    """Reference implementation matching _hypervolume_trace's old
    behaviour exactly (recompute the front from scratch every step) --
    used only to prove the incremental version returns identical values,
    not because this is the version worth keeping (O(k^3) vs O(k^2))."""
    from p3net.metrics import hypervolume as hv
    from p3net.problem.objectives import pareto_front as pf

    trace = []
    seen = []
    for point in objectives:
        seen.append(point)
        trace.append(hv(pf(seen, lambda p: p), reference))
    return trace


def test_hypervolume_trace_incremental_matches_full_recompute():
    from reporting.plots import _hypervolume_trace

    rng_points = [
        (5.0, 5.0),
        (3.0, 4.0),
        (6.0, 1.0),
        (4.0, 4.5),  # dominated by (3.0, 4.0) -- must not enter the front
        (1.0, 6.0),
        (2.0, 2.0),
    ]
    reference = (7.0, 7.0)
    incremental = _hypervolume_trace(rng_points, reference)
    full_recompute = _hypervolume_trace_by_full_recompute(rng_points, reference)
    assert incremental == pytest.approx(full_recompute)


def test_hypervolume_trace_completes_on_a_realistic_budget_size():
    from reporting.plots import _hypervolume_trace

    # A strictly nondominated 200-point sequence (this project's largest
    # budget tier) -- must return promptly, not hang.
    points = [(float(i), 200.0 - float(i)) for i in range(200)]
    trace = _hypervolume_trace(points, reference=(201.0, 201.0))
    assert len(trace) == 200
    assert trace == sorted(trace)  # best-so-far hypervolume never decreases


def test_convergence_curve_figure_returns_a_figure_with_one_line_per_method():
    fig = convergence_curve_figure(_paired_runs(), search_space="space", budget=100)
    assert isinstance(fig, Figure)
    ax = fig.axes[0]
    assert len(ax.lines) == 2  # p3net + baseline


def test_convergence_curve_figure_handles_no_matching_runs():
    fig = convergence_curve_figure(_paired_runs(), search_space="nope", budget=999)
    assert isinstance(fig, Figure)
    assert len(fig.axes[0].lines) == 0


def test_pareto_front_progression_figure_returns_a_figure():
    fig = pareto_front_progression_figure(
        _paired_runs(), search_space="space", budget=100, method="p3net"
    )
    assert isinstance(fig, Figure)


def test_pareto_front_progression_figure_rejects_non_2d_objectives():
    runs = [_run("p3net", "space", 10, 1, [(1.0, 1.0, 1.0)])]
    with pytest.raises(ValueError):
        pareto_front_progression_figure(runs, search_space="space", budget=10, method="p3net")


def test_sensitivity_figure_returns_a_figure_for_a_small_grid():
    points = [
        SensitivityPoint(kappa=1, acceptance_threshold=0.0, hypervolume=1.0, rank_correlation=0.5),
        SensitivityPoint(
            kappa=None, acceptance_threshold=0.01, hypervolume=1.5, rank_correlation=0.7
        ),
    ]
    fig = sensitivity_figure(points, metric="hypervolume")
    assert isinstance(fig, Figure)


def test_sensitivity_figure_rejects_unknown_metric():
    with pytest.raises(ValueError):
        sensitivity_figure([], metric="not_a_metric")


def test_duplication_rate_figure_returns_a_figure_with_one_bar_per_method():
    runs = [
        _run("a", "space", 10, 1, [(1.0, 1.0)], duplication_rate=0.1),
        _run("b", "space", 10, 1, [(1.0, 1.0)], duplication_rate=0.4),
    ]
    fig = duplication_rate_figure(runs)
    assert isinstance(fig, Figure)
    assert len(fig.axes[0].patches) == 2


def test_surrogate_quality_figure_no_data():
    fig = surrogate_quality_figure([], method="p3net")
    assert isinstance(fig, Figure)
    assert len(fig.axes[0].lines) == 0


def test_surrogate_quality_figure_bins_by_history_size_and_scores_sign_agreement():
    # Two bins worth of |H_t|: a low-history bin where the surrogate always
    # gets the sign wrong (accuracy 0.0) and a high-history bin where it
    # always gets it right (accuracy 1.0) -- checks both the binning and
    # that pairwise_comparison_accuracy (not rank_correlation) drives the
    # plotted value, matching the relative-surrogate quality metric
    # metrics/surrogate_quality.py documents for delta_hat_F.
    log = [
        {"history_size": 5, "predicted_delta": 1.0, "true_delta": -1.0},
        {"history_size": 6, "predicted_delta": -1.0, "true_delta": 1.0},
        {"history_size": 50, "predicted_delta": 1.0, "true_delta": 1.0},
        {"history_size": 51, "predicted_delta": -1.0, "true_delta": -1.0},
    ]
    runs = [
        RawRun(
            method="p3net",
            search_space="space",
            budget=10,
            seed=1,
            evaluations_used=4,
            history=(),
            diagnostics={"surrogate_quality_log": log},
        )
    ]
    fig = surrogate_quality_figure(runs, method="p3net", n_bins=2)
    ax = fig.axes[0]
    ys = list(ax.lines[0].get_ydata())
    assert ys == pytest.approx([0.0, 1.0])


def test_surrogate_quality_figure_ignores_other_methods():
    runs = [
        _run(
            "baseline",
            "space",
            10,
            1,
            [(1.0, 1.0)],
            surrogate_quality_log=[{"history_size": 5, "predicted_delta": 1.0, "true_delta": 1.0}],
        )
    ]
    fig = surrogate_quality_figure(runs, method="p3net")
    assert len(fig.axes[0].lines) == 0


def test_surrogate_calibration_figure_no_data():
    fig = surrogate_calibration_figure([], method="p3net")
    assert isinstance(fig, Figure)
    assert len(fig.axes[0].patches) == 0


def test_surrogate_calibration_figure_one_bar_per_search_space():
    # "good" search space: perfect predictions, R^2 = 1.0. "bad": always
    # predicts the opposite sign and a larger magnitude than the truth,
    # so R^2 must be negative -- checks the per-dataset split, not just
    # that a number gets plotted.
    good_log = [
        {"history_size": 5, "predicted_delta": 1.0, "true_delta": 1.0},
        {"history_size": 6, "predicted_delta": -2.0, "true_delta": -2.0},
    ]
    bad_log = [
        {"history_size": 5, "predicted_delta": 3.0, "true_delta": 1.0},
        {"history_size": 6, "predicted_delta": -3.0, "true_delta": -1.0},
    ]
    runs = [
        RawRun(
            method="p3net",
            search_space="good_space",
            budget=10,
            seed=1,
            evaluations_used=2,
            history=(),
            diagnostics={"surrogate_quality_log": good_log},
        ),
        RawRun(
            method="p3net",
            search_space="bad_space",
            budget=10,
            seed=1,
            evaluations_used=2,
            history=(),
            diagnostics={"surrogate_quality_log": bad_log},
        ),
    ]
    fig = surrogate_calibration_figure(runs, method="p3net")
    ax = fig.axes[0]
    heights = {label.get_text(): bar.get_height() for label, bar in zip(ax.get_xticklabels(), ax.patches)}
    assert heights["good_space"] == pytest.approx(1.0)
    assert heights["bad_space"] < 0.0


def test_surrogate_calibration_figure_ignores_other_methods():
    runs = [
        _run(
            "baseline",
            "space",
            10,
            1,
            [(1.0, 1.0)],
            surrogate_quality_log=[{"history_size": 5, "predicted_delta": 1.0, "true_delta": 1.0}],
        )
    ]
    fig = surrogate_calibration_figure(runs, method="p3net")
    assert len(fig.axes[0].patches) == 0


# -- scripts.generate_report -----------------------------------------------


def test_generate_report_writes_tables_and_figures_from_raw_json(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for method, seed in (("p3net", 1), ("baseline", 1)):
        payload = {
            "method": method,
            "search_space": "space",
            "budget": 10,
            "seed": seed,
            "evaluations_used": 2,
            "history": [
                {"genotype": ["a"], "objectives": [1.0, 1.0]},
                {"genotype": ["b"], "objectives": [0.9, 1.1]},
            ],
            "diagnostics": {"duplication_rate": 0.2},
        }
        (raw_dir / f"{method}__space__budget10__seed{seed}.json").write_text(
            json.dumps(payload), encoding="utf-8"
        )

    tables_dir = tmp_path / "tables"
    figures_dir = tmp_path / "figures"
    tables, figures = generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=figures_dir
    )
    assert tables
    assert figures
    assert all(p.exists() for p in tables)
    assert all(p.exists() for p in figures)


def test_generate_report_handles_no_raw_runs(tmp_path):
    tables, figures = generate_report(
        raw_results_dir=tmp_path, tables_dir=tmp_path / "t", figures_dir=tmp_path / "f"
    )
    assert tables == []
    assert figures == []
