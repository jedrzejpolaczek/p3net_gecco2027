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
