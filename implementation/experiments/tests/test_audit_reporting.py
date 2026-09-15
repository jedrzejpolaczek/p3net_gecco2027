"""Tests for the reporting additions made in response to the v0.0.3 review
audit: effect-size orientation for minimised metrics, the reference-arm
parameter, frozen fronts, the diagnostics tables, the narrative/TeX
generators, and the paper-number guard.

Each test pins one failure mode that actually occurred or was one edit
away from occurring, named in its docstring."""

from __future__ import annotations

import pytest

from p3net.harness.runner import Observation
from p3net.metrics import igd_plus
from p3net.problem.genotype import Genotype
from reporting import (
    RawRun,
    acceptance_gate_precision_table,
    bootstrap_share_table,
    chain_depth_error_table,
    duplication_rate_table,
    fixed_budget_summary_table,
    margin_correlation,
    rejection_counts,
    surrogate_calibration_table,
)
from reporting.reference_fronts import freeze_fronts, load_fronts, save_fronts


def _run(method, space, budget, seed, points, **diagnostics) -> RawRun:
    history = tuple(
        Observation(genotype=Genotype(values=(method, seed, i)), objectives=tuple(p))
        for i, p in enumerate(points)
    )
    return RawRun(
        method=method,
        search_space=space,
        budget=budget,
        seed=seed,
        evaluations_used=len(points),
        history=history,
        diagnostics=diagnostics,
    )


# -- IGD+ normalisation ----------------------------------------------------


def test_igd_plus_normalise_rescales_each_objective_to_the_oracle_range():
    """Unnormalised, a unit error on a large-range objective swamps an
    equally-large *relative* error on a small-range one."""
    oracle = [(0.0, 0.0), (10.0, 1000.0)]
    # Worse by 10% of range on f1 only, vs. worse by 10% of range on f2 only.
    worse_on_f1 = [(1.0, 0.0), (11.0, 1000.0)]
    worse_on_f2 = [(0.0, 100.0), (10.0, 1100.0)]
    assert igd_plus(worse_on_f2, oracle) > 10 * igd_plus(worse_on_f1, oracle)
    assert igd_plus(worse_on_f1, oracle, normalise=True) == pytest.approx(
        igd_plus(worse_on_f2, oracle, normalise=True)
    )


def test_igd_plus_default_keeps_the_raw_scale_definition():
    oracle = [(0.0, 0.0)]
    assert igd_plus([(3.0, 4.0)], oracle) == pytest.approx(5.0)


# -- effect-size orientation -----------------------------------------------


def _paired_runs(space, better_method, worse_method, better_points, worse_points, seeds=range(1, 9)):
    runs = []
    for s in seeds:
        runs.append(_run(better_method, space, 10, s, better_points))
        runs.append(_run(worse_method, space, 10, s, worse_points))
    return runs


def test_positive_effect_favours_the_reference_arm_on_a_minimised_metric():
    """IGD+ is minimised. cliffs_delta measures raw magnitude, so without
    re-orientation a reference arm with LOWER (better) IGD+ would show a
    NEGATIVE delta -- silently inverting every NAS-HPO-Bench-II heatmap
    cell once that benchmark moved to IGD+."""
    oracle = [(0.0, 0.0), (1.0, -1.0)]
    runs = _paired_runs(
        "space", "p3net", "baseline",
        better_points=[(0.1, 0.0), (1.1, -1.0)],
        worse_points=[(0.9, 0.5), (1.9, -0.5)],
    )
    rows = fixed_budget_summary_table(runs, oracle_fronts={"space": oracle})
    baseline = next(r for r in rows if r.method == "baseline")
    assert baseline.metric == "igd_plus"
    assert baseline.effect_size > 0


def test_positive_effect_favours_the_reference_arm_on_a_maximised_metric():
    runs = _paired_runs(
        "space", "p3net", "baseline",
        better_points=[(0.1, 0.1), (0.2, 0.05)],
        worse_points=[(0.9, 0.9), (0.95, 0.85)],
    )
    rows = fixed_budget_summary_table(runs)
    baseline = next(r for r in rows if r.method == "baseline")
    assert baseline.metric == "hypervolume_relative"
    assert baseline.effect_size > 0


def test_reference_method_parameter_changes_which_arm_is_compared_against():
    runs = _paired_runs(
        "space", "random_search", "p3net",
        better_points=[(0.1, 0.1)],
        worse_points=[(0.9, 0.9)],
    )
    rows = fixed_budget_summary_table(runs, reference_method="random_search")
    p3net = next(r for r in rows if r.method == "p3net")
    random_search = next(r for r in rows if r.method == "random_search")
    assert random_search.effect_size is None  # it is the reference now
    assert p3net.effect_size is not None and p3net.effect_size > 0


# -- frozen fronts -----------------------------------------------------------


def test_frozen_fronts_round_trip_and_record_their_source(tmp_path):
    runs = [_run("a", "space", 10, s, [(1.0, 2.0), (2.0, 1.0)]) for s in (1, 2)]
    frozen = freeze_fronts(runs)
    save_fronts(frozen, tmp_path)
    loaded = load_fronts(tmp_path)
    assert loaded["space"].front == frozen["space"].front
    assert loaded["space"].n_source_runs == 2
    assert loaded["space"].source_run_digest == frozen["space"].source_run_digest


def test_frozen_front_pins_the_metric_when_a_better_arm_is_added():
    base = [_run("p3net", "space", 10, s, [(5.0, 5.0)]) for s in (1, 2, 3)]
    base += [_run("rs", "space", 10, s, [(6.0, 6.0)]) for s in (1, 2, 3)]
    frozen = freeze_fronts(base)
    fronts = {k: v.front for k, v in frozen.items()}
    refs = {k: v.reference_point for k, v in frozen.items()}

    extended = base + [_run("tpe", "space", 10, s, [(1.0, 1.0)]) for s in (1, 2, 3)]
    pinned = fixed_budget_summary_table(extended, frozen_fronts=fronts, frozen_references=refs)
    unpinned = fixed_budget_summary_table(extended)
    original = fixed_budget_summary_table(base, frozen_fronts=fronts, frozen_references=refs)

    def median(rows, m):
        return next(r.median for r in rows if r.method == m)

    assert median(pinned, "p3net") == pytest.approx(median(original, "p3net"))
    assert median(unpinned, "p3net") != pytest.approx(median(original, "p3net"))


# -- diagnostics tables -------------------------------------------------------


def test_duplication_rate_table_averages_per_method():
    runs = [
        _run("a", "s", 10, 1, [(1, 1)], duplication_rate=0.2),
        _run("a", "s", 10, 2, [(1, 1)], duplication_rate=0.4),
        _run("b", "s", 10, 1, [(1, 1)], duplication_rate=0.0),
    ]
    rows = {r.method: r for r in duplication_rate_table(runs)}
    assert rows["a"].mean_rate == pytest.approx(0.3)
    assert rows["a"].n_runs == 2


def test_bootstrap_share_sums_across_seeds_before_dividing():
    """A mean of per-seed ratios would weight a 2-proposal run the same as
    a 200-proposal run."""
    runs = [
        _run("p3net", "s", 10, 1, [(1, 1)], bootstrap_proposals=1, mixing_proposals=1),
        _run("p3net", "s", 10, 2, [(1, 1)], bootstrap_proposals=99, mixing_proposals=1),
    ]
    (row,) = bootstrap_share_table(runs)
    assert row.bootstrap_share == pytest.approx(100 / 102)


def test_acceptance_gate_precision_counts_sign_agreement():
    log = [
        {"history_size": 2, "predicted_delta": 1.0, "true_delta": 0.5},
        {"history_size": 3, "predicted_delta": 1.0, "true_delta": -0.5},
        {"history_size": 4, "predicted_delta": 0.5, "true_delta": 2.0},
        {"history_size": 5, "predicted_delta": 0.1, "true_delta": -1.0},
    ]
    runs = [_run("p3net", "s", 10, 1, [(1, 1)], surrogate_quality_log=log)]
    pooled = acceptance_gate_precision_table(runs)[0]
    assert pooled.scope == "pooled"
    assert pooled.precision == pytest.approx(0.5)
    assert pooled.n_predictions == 4


def test_surrogate_calibration_groups_by_level_size():
    log = [
        {"history_size": 2, "predicted_delta": 1.0, "true_delta": 1.0},
        {"history_size": 3, "predicted_delta": 2.0, "true_delta": 2.0},
        {"history_size": 4, "predicted_delta": 5.0, "true_delta": -5.0},
        {"history_size": 5, "predicted_delta": -5.0, "true_delta": 5.0},
    ]
    runs = [_run("p3net", "s", 10, 1, [(1, 1)], surrogate_quality_log=log, level_size_log=[2, 2, 16, 16])]
    rows = {(r.grouping, r.key): r for r in surrogate_calibration_table(runs)}
    assert rows[("pyramid_level_size", "2")].calibration_r2 == pytest.approx(1.0)
    assert rows[("pyramid_level_size", "16")].calibration_r2 < 0


def test_chain_depth_error_uses_median_per_depth():
    log = [
        {"history_size": 2, "predicted_delta": 0.0, "true_delta": 1.0},
        {"history_size": 3, "predicted_delta": 0.0, "true_delta": 3.0},
        {"history_size": 4, "predicted_delta": 0.0, "true_delta": 2.0},
    ]
    runs = [_run("p3net", "s", 10, 1, [(1, 1)], surrogate_quality_log=log, chain_depth_log=[1, 1, 1])]
    (row,) = chain_depth_error_table(runs)
    assert row.chain_depth == 1
    assert row.median_squared_error == pytest.approx(4.0)


def test_rejection_counts_and_margin_correlation_use_the_rows_they_are_given():
    from reporting.tables import SummaryRow

    def row(method, space, budget, effect, reject):
        return SummaryRow(method, space, budget, "m", 0.0, 0.0, 30, 0.01, effect, reject)

    ref_rows = [row(f"b{i}", "s", 10 * (i + 1), 0.1 * i, i % 2 == 0) for i in range(5)]
    ctl_rows = [row(f"b{i}", "s", 10 * (i + 1), 0.1 * i + 0.01, False) for i in range(5)]
    counts = {c.method: c for c in rejection_counts(ref_rows)}
    assert counts["b0"].cells_significant == 1
    assert counts["b1"].cells_significant == 0

    result = margin_correlation(ref_rows, ctl_rows)
    assert result is not None
    assert result.n_pairs == 5
    assert result.spearman_rho == pytest.approx(1.0)


# -- narrative generator and number guard -------------------------------------


def _summary_markdown(rows):
    lines = [
        "| Method | Search space | Budget | Metric | Median | IQR | n | Adj. p | Effect size | Reject H0 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for m, space, b, eff, rej in rows:
        p = "--" if eff is None else "0.0100"
        e = "--" if eff is None else f"{eff:.3f}"
        r = "--" if rej is None else ("yes" if rej else "no")
        lines.append(f"| {m} | {space} | {b} | hypervolume_relative | 0.9000 | 0.0100 | 30 | {p} | {e} | {r} |")
    return "\n".join(lines) + "\n"


def test_narrative_counts_match_the_table(tmp_path):
    """The failure this generator exists to prevent: prose saying 61 of 160
    while the table on the same page says 54."""
    from scripts.render_results_narrative import read_table, render_fixed_budget_paragraph

    md = _summary_markdown(
        [
            ("p3net", "jahs_bench_201", 50, None, None),
            ("p3_alone", "jahs_bench_201", 50, 0.6, True),
            ("mo_bohb", "jahs_bench_201", 50, 0.4, True),
            ("sh_emoa", "jahs_bench_201", 50, -0.8, True),
            ("tpe", "jahs_bench_201", 50, -0.1, False),
        ]
    )
    path = tmp_path / "fixed_budget_summary.md"
    path.write_text(md, encoding="utf-8")
    text = render_fixed_budget_paragraph(read_table(path))
    assert "3 of the 4 comparisons reject" in text
    assert "one favour the baseline" in text.lower() or "One favour the baseline" in text
    assert "two favour P3Net" in text


def test_number_guard_flags_a_number_absent_from_every_table(tmp_path, monkeypatch):
    from scripts import check_paper_numbers as guard

    tables = tmp_path / "tables"
    tables.mkdir()
    (tables / "t.md").write_text("| x | 0.4976 | 54 |\n", encoding="utf-8")
    chapter = tmp_path / "chapters" / "v003" / "results"
    chapter.mkdir(parents=True)
    (chapter / "main.tex").write_text(
        "Precision is 0.498, 54 of 160 reject, and 61 is stale.", encoding="utf-8"
    )
    monkeypatch.setattr(guard, "TABLE_DIRS", (tables,))
    monkeypatch.setattr(guard, "DATA_BEARING_CHAPTERS", ("chapters/v003/results/main.tex",))

    paper = guard.collect_paper_numbers(tmp_path)
    table_numbers = guard.collect_table_numbers(guard.TABLE_DIRS)
    orphans = {n for n in paper if n not in guard.ALLOWED_LITERALS and n not in table_numbers}
    assert "61" in orphans
    assert "0.498" not in orphans  # coarser rendering of 0.4976
    assert "54" not in orphans
