"""Tests for scripts.generate_report -- specifically that its report
stays scoped to reporting.MAIN_COMPARISON_METHODS even when
results/raw/ also holds data for methods outside the paper's eleven
documented arms (configs/methods/p3net_*.yaml's `default_grid: false`
sensitivity/design-choice ablations, in particular)."""

import json
from pathlib import Path

from scripts import generate_report


def _write_raw_run(
    raw_dir: Path,
    *,
    method: str,
    search_space: str = "jahs_bench_201",
    budget: int = 10,
    seed: int,
    points: list[tuple[float, float]],
) -> None:
    payload = {
        "method": method,
        "search_space": search_space,
        "budget": budget,
        "seed": seed,
        "evaluations_used": len(points),
        "history": [{"genotype": [seed, i], "objectives": list(p)} for i, p in enumerate(points)],
        "diagnostics": {"duplication_rate": 0.0},
    }
    path = raw_dir / f"{method}__{search_space}__budget{budget}__seed{seed}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_report_excludes_methods_outside_main_comparison_set(tmp_path):
    raw_dir = tmp_path / "raw"
    tables_dir = tmp_path / "tables"
    figures_dir = tmp_path / "figures"
    raw_dir.mkdir()

    for seed in (1, 2):
        _write_raw_run(
            raw_dir, method="p3net", seed=seed, points=[(5.0, 5.0), (4.0, 4.5)]
        )
        _write_raw_run(
            raw_dir, method="random_search", seed=seed, points=[(6.0, 6.0), (5.5, 5.8)]
        )
        # Not one of the paper's eleven documented arms -- e.g. a
        # scripts/run_kappa_sensitivity.py joint-sweep cell
        # (p3net_kappa_sensitivity__kappa4__threshold0p0), which can
        # legitimately land in the same results/raw/ folder as the main
        # grid without being part of its comparison.
        _write_raw_run(
            raw_dir, method="p3net_kappa_half", seed=seed, points=[(3.0, 3.0)]
        )

    tables, figures = generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=figures_dir
    )

    assert tables
    summary_text = (tables_dir / "fixed_budget_summary.md").read_text(encoding="utf-8")
    assert "p3net_kappa_half" not in summary_text
    assert "p3net" in summary_text
    assert "random_search" in summary_text

    for figure_path in figures:
        assert "p3net_kappa_half" not in figure_path.name


def test_generate_report_returns_nothing_when_only_non_main_methods_present(tmp_path):
    raw_dir = tmp_path / "raw"
    tables_dir = tmp_path / "tables"
    figures_dir = tmp_path / "figures"
    raw_dir.mkdir()

    _write_raw_run(raw_dir, method="p3net_cascade", seed=1, points=[(3.0, 3.0)])

    tables, figures = generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=figures_dir
    )

    assert tables == []
    assert figures == []


def test_generate_report_excludes_search_spaces_outside_the_primary_grid(tmp_path):
    """The architecture-only NAS-Bench-201 isolation grid shares
    results/raw/ with the headline grid but is a separate analysis axis.
    Letting it into the headline report adds cells to every arm (18
    instead of 16) and shifts every "of 160" count the paper quotes."""
    raw_dir = tmp_path / "raw"
    tables_dir = tmp_path / "tables"
    figures_dir = tmp_path / "figures"
    raw_dir.mkdir()

    for seed in (1, 2):
        for space in ("jahs_bench_201", "nas_bench_201"):
            _write_raw_run(
                raw_dir, method="p3net", search_space=space, seed=seed,
                points=[(5.0, 5.0), (4.0, 4.5)],
            )
            _write_raw_run(
                raw_dir, method="random_search", search_space=space, seed=seed,
                points=[(6.0, 6.0), (5.5, 5.8)],
            )

    generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=figures_dir
    )
    summary_text = (tables_dir / "fixed_budget_summary.md").read_text(encoding="utf-8")
    assert "jahs_bench_201" in summary_text
    assert "nas_bench_201 " not in summary_text and "| nas_bench_201 |" not in summary_text


def test_generate_report_keeps_frozen_fronts_next_to_the_raw_runs_it_was_given(tmp_path):
    """A caller pointing raw_results_dir at its own directory must never
    read or write the real project's persisted fronts."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    for seed in (1, 2):
        _write_raw_run(raw_dir, method="p3net", seed=seed, points=[(5.0, 5.0), (4.0, 4.5)])
        _write_raw_run(raw_dir, method="random_search", seed=seed, points=[(6.0, 6.0)])

    generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tmp_path / "tables", figures_dir=tmp_path / "figures"
    )
    assert (tmp_path / "reference_fronts" / "jahs_bench_201.json").exists()


def test_frozen_front_is_reused_rather_than_rebuilt_when_an_arm_is_added(tmp_path):
    """Adding an arm that finds strictly better points must not change the
    metric already reported for the existing arms."""
    raw_dir = tmp_path / "raw"
    tables_dir = tmp_path / "tables"
    raw_dir.mkdir()
    for seed in (1, 2, 3):
        _write_raw_run(raw_dir, method="p3net", seed=seed, points=[(5.0, 5.0), (4.0, 6.0)])
        _write_raw_run(raw_dir, method="random_search", seed=seed, points=[(6.0, 6.0), (5.0, 7.0)])

    generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=tmp_path / "f1"
    )
    before = (tables_dir / "fixed_budget_summary.md").read_text(encoding="utf-8")
    p3net_before = next(l for l in before.splitlines() if l.startswith("| p3net |"))

    for seed in (1, 2, 3):
        _write_raw_run(raw_dir, method="tpe", seed=seed, points=[(1.0, 1.0)])

    generate_report.generate_report(
        raw_results_dir=raw_dir, tables_dir=tables_dir, figures_dir=tmp_path / "f2"
    )
    after = (tables_dir / "fixed_budget_summary.md").read_text(encoding="utf-8")
    p3net_after = next(l for l in after.splitlines() if l.startswith("| p3net |"))
    assert p3net_before == p3net_after

