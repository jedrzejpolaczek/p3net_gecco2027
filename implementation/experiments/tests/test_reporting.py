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
