"""
Persisted tables for every diagnostic number the Results and Conclusions
sections quote.

Motivation (audit finding R1): the headline fixed-budget table has always
been generated from results/raw/ and re-checkable against it, but eight
further numbers the paper quotes -- acceptance-gate precision, magnitude
calibration, the pyramid bootstrap share, the per-arm vs-random-search
record, the cross-baseline margin correlation, the duplication rate, the
architecture-involving epistasis proxy, and the interaction-feature arm's
own comparison -- existed only as prose in the .tex, or at best as a PNG.
A number with no regenerable artifact behind it cannot be checked, and
exactly that gap is how the Results narrative drifted out of sync with the
tables it describes.

Every function here reads the same results/raw/*.json the headline table
reads, and every one of them is rendered to results/tables/*.md by
scripts/generate_report.py. Rule for the paper: if a number appears in the
.tex, it appears in one of these files first.

Reference: chapters/v003/results/main.tex (Diagnostics paragraphs);
chapters/v003/conclusions/main.tex.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from reporting._common import RawRun

# ---------------------------------------------------------------------------
# Genotype layout: which coordinates are architecture edges.
#
# Both benchmark families put the cell's categorical edge choices first and
# the training hyperparameters after them (search_spaces/nas_genotype.py,
# search_spaces/nas_hpo_bench_ii_genotype.py). The epistasis proxy below
# needs to know where that boundary sits to restrict its interaction terms
# to pairs touching at least one architecture edge.
# ---------------------------------------------------------------------------
ARCHITECTURE_EDGE_COUNTS: Mapping[str, int] = {
    "jahs_bench_201": 6,
    "jahs_bench_201_colorectal": 6,
    "jahs_bench_201_fashion": 6,
    "nas_hpo_bench_ii": 6,
    "nas_bench_201": 6,
}

HISTORY_BINS = 10


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else float("nan")


# ---------------------------------------------------------------------------
# 1. Proposal-time genotype duplication rate (Results, "Diagnostics:
#    genotype duplication" -- previously only a PNG).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DuplicationRow:
    method: str
    mean_rate: float
    n_runs: int


def duplication_rate_table(runs: Sequence[RawRun]) -> list[DuplicationRow]:
    by_method: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        rate = run.diagnostics.get("duplication_rate")
        if rate is not None:
            by_method[run.method].append(float(rate))
    return [
        DuplicationRow(method=m, mean_rate=_mean(v), n_runs=len(v))
        for m, v in sorted(by_method.items())
    ]


def render_duplication_rate_markdown(rows: Sequence[DuplicationRow]) -> str:
    lines = [
        "| Method | Mean proposal-time duplication rate | n runs |",
        "|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: -r.mean_rate):
        lines.append(f"| {r.method} | {r.mean_rate:.4f} | {r.n_runs} |")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 2. Population-pyramid bootstrap share (Results, "Diagnostics:
#    population-pyramid bootstrap share"; Conclusions).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BootstrapShareRow:
    method: str
    search_space: str
    budget: int
    bootstrap_proposals: int
    mixing_proposals: int
    bootstrap_share: float
    n_runs: int


def bootstrap_share_table(
    runs: Sequence[RawRun], *, methods: Sequence[str] = ("p3net",)
) -> list[BootstrapShareRow]:
    """Share of a run's proposals that came from uniform-random level
    bootstrap rather than from a surrogate-guided optimal-mixing sweep.
    Summed across seeds first, then divided -- not a mean of per-seed
    ratios, which would weight a short run the same as a long one."""
    wanted = set(methods)
    by_group: dict[tuple[str, str, int], list[tuple[int, int]]] = defaultdict(list)
    for run in runs:
        if run.method not in wanted:
            continue
        boot = run.diagnostics.get("bootstrap_proposals")
        mix = run.diagnostics.get("mixing_proposals")
        if boot is None or mix is None:
            continue
        by_group[(run.method, run.search_space, run.budget)].append((int(boot), int(mix)))

    rows: list[BootstrapShareRow] = []
    for (method, space, budget), pairs in sorted(by_group.items()):
        boot_total = sum(b for b, _ in pairs)
        mix_total = sum(m for _, m in pairs)
        total = boot_total + mix_total
        rows.append(
            BootstrapShareRow(
                method=method,
                search_space=space,
                budget=budget,
                bootstrap_proposals=boot_total,
                mixing_proposals=mix_total,
                bootstrap_share=(boot_total / total) if total else float("nan"),
                n_runs=len(pairs),
            )
        )
    return rows


def render_bootstrap_share_markdown(rows: Sequence[BootstrapShareRow]) -> str:
    lines = [
        "| Method | Search space | Budget | Bootstrap proposals | Mixing proposals | "
        "Bootstrap share | n runs |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.method} | {r.search_space} | {r.budget} | {r.bootstrap_proposals} | "
            f"{r.mixing_proposals} | {r.bootstrap_share:.4f} | {r.n_runs} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 3. Acceptance-gate precision (Results, "Surrogate quality").
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GatePrecisionRow:
    scope: str
    history_size_lo: float
    history_size_hi: float
    precision: float
    n_predictions: int


def acceptance_gate_precision_table(
    runs: Sequence[RawRun], *, method: str = "p3net", bins: int = HISTORY_BINS
) -> list[GatePrecisionRow]:
    """Precision of the step-3 acceptance gate: of the modifications the
    surrogate let through (every logged prediction is, by construction, a
    predicted improvement), what fraction genuinely improved. Pooled
    first, then binned by |H_t| at prediction time."""
    points: list[tuple[float, bool]] = []
    for run in runs:
        if run.method != method:
            continue
        for entry in run.diagnostics.get("surrogate_quality_log") or []:
            h = float(entry["history_size"])
            agree = (float(entry["predicted_delta"]) >= 0) == (float(entry["true_delta"]) >= 0)
            points.append((h, agree))
    if not points:
        return []

    rows = [
        GatePrecisionRow(
            scope="pooled",
            history_size_lo=min(h for h, _ in points),
            history_size_hi=max(h for h, _ in points),
            precision=_mean([1.0 if a else 0.0 for _, a in points]),
            n_predictions=len(points),
        )
    ]
    lo, hi = rows[0].history_size_lo, rows[0].history_size_hi
    width = (hi - lo) / bins if hi > lo else 1.0
    for i in range(bins):
        b_lo = lo + i * width
        b_hi = lo + (i + 1) * width
        in_bin = [a for h, a in points if (b_lo <= h < b_hi or (i == bins - 1 and h == b_hi))]
        if not in_bin:
            continue
        rows.append(
            GatePrecisionRow(
                scope=f"bin{i + 1}",
                history_size_lo=b_lo,
                history_size_hi=b_hi,
                precision=_mean([1.0 if a else 0.0 for a in in_bin]),
                n_predictions=len(in_bin),
            )
        )
    return rows


def render_gate_precision_markdown(rows: Sequence[GatePrecisionRow]) -> str:
    lines = [
        "| Scope | History size from | History size to | Gate precision | n predictions |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.scope} | {r.history_size_lo:.1f} | {r.history_size_hi:.1f} | "
            f"{r.precision:.4f} | {r.n_predictions} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 4. Magnitude calibration (Results, "Surrogate quality: magnitude
#    calibration"), by search space and by sweeping pyramid level size.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CalibrationRow:
    grouping: str
    key: str
    calibration_r2: float
    mean_squared_error: float
    n_predictions: int


def _r2(predicted: Sequence[float], true: Sequence[float]) -> float:
    if len(true) < 2:
        return float("nan")
    mean_true = _mean(true)
    ss_tot = sum((t - mean_true) ** 2 for t in true)
    ss_res = sum((t - p) ** 2 for p, t in zip(predicted, true))
    if ss_tot == 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def surrogate_calibration_table(
    runs: Sequence[RawRun], *, method: str = "p3net", budget: int | None = None
) -> list[CalibrationRow]:
    """R-squared between predicted and true delta, grouped two ways: by
    search space, and by the target size of the pyramid level whose sweep
    produced the prediction (the level_size_log entry paired index-for-
    index with surrogate_quality_log)."""
    by_space: dict[str, list[tuple[float, float]]] = defaultdict(list)
    by_level: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for run in runs:
        if run.method != method:
            continue
        if budget is not None and run.budget != budget:
            continue
        log = run.diagnostics.get("surrogate_quality_log") or []
        levels = run.diagnostics.get("level_size_log") or []
        for i, entry in enumerate(log):
            pair = (float(entry["predicted_delta"]), float(entry["true_delta"]))
            by_space[run.search_space].append(pair)
            if i < len(levels) and levels[i] is not None:
                by_level[int(levels[i])].append(pair)

    rows: list[CalibrationRow] = []
    for space, pairs in sorted(by_space.items()):
        pred = [p for p, _ in pairs]
        true = [t for _, t in pairs]
        rows.append(
            CalibrationRow(
                grouping="search_space",
                key=space,
                calibration_r2=_r2(pred, true),
                mean_squared_error=_mean([(t - p) ** 2 for p, t in pairs]),
                n_predictions=len(pairs),
            )
        )
    for size, pairs in sorted(by_level.items()):
        pred = [p for p, _ in pairs]
        true = [t for _, t in pairs]
        rows.append(
            CalibrationRow(
                grouping="pyramid_level_size",
                key=str(size),
                calibration_r2=_r2(pred, true),
                mean_squared_error=_mean([(t - p) ** 2 for p, t in pairs]),
                n_predictions=len(pairs),
            )
        )
    return rows


def render_calibration_markdown(rows: Sequence[CalibrationRow]) -> str:
    lines = [
        "| Grouping | Key | Calibration R2 | MSE | n predictions |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.grouping} | {r.key} | {r.calibration_r2:.4f} | "
            f"{r.mean_squared_error:.4f} | {r.n_predictions} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 5. Squared error by telescoping chain depth (Results, "Surrogate
#    quality: magnitude calibration").
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChainDepthRow:
    chain_depth: int
    median_squared_error: float
    n_predictions: int


def chain_depth_error_table(
    runs: Sequence[RawRun], *, method: str = "p3net"
) -> list[ChainDepthRow]:
    by_depth: dict[int, list[float]] = defaultdict(list)
    for run in runs:
        if run.method != method:
            continue
        log = run.diagnostics.get("surrogate_quality_log") or []
        depths = run.diagnostics.get("chain_depth_log") or []
        for i, entry in enumerate(log):
            if i >= len(depths) or depths[i] is None:
                continue
            err = (float(entry["true_delta"]) - float(entry["predicted_delta"])) ** 2
            by_depth[int(depths[i])].append(err)
    return [
        ChainDepthRow(
            chain_depth=d, median_squared_error=statistics.median(v), n_predictions=len(v)
        )
        for d, v in sorted(by_depth.items())
    ]


def render_chain_depth_markdown(rows: Sequence[ChainDepthRow]) -> str:
    lines = ["| Chain depth | Median squared error | n predictions |", "|---|---|---|"]
    for r in rows:
        lines.append(
            f"| {r.chain_depth} | {r.median_squared_error:.4f} | {r.n_predictions} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 6. Architecture-involving epistasis proxy (Results, "Diagnostics:
#    surrogate representational capacity").
#
# Held-out R-squared gained by adding second-order interaction terms that
# touch at least one architecture edge, over a main-effects-only model of
# f1. Recomputed here from the same evaluated (genotype, objectives) pairs
# the runs already persist, so the number in the paper has a regenerable
# source; the original measurement was ad-hoc and never committed.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EpistasisRow:
    search_space: str
    main_effects_r2: float
    with_interactions_r2: float
    architecture_involving_gain: float
    n_samples: int
    n_features_main: int
    n_features_interaction: int


def epistasis_table(
    runs: Sequence[RawRun],
    *,
    objective_index: int = 0,
    max_samples: int = 20000,
    folds: int = 5,
    seed: int = 0,
) -> list[EpistasisRow]:
    """One row per search space. Both models are ridge-regularised linear
    fits on one-hot features, scored by k-fold cross-validation on held-out
    folds -- the gain is a genuine out-of-sample gain, not an in-sample
    one, which would rise mechanically with any added feature."""
    import numpy as np
    from sklearn.linear_model import RidgeCV
    from sklearn.model_selection import KFold, cross_val_score

    by_space: dict[str, list[tuple[tuple[int, ...], float]]] = defaultdict(list)
    for run in runs:
        for obs in run.history:
            by_space[run.search_space].append(
                (tuple(obs.genotype.values), float(obs.objectives[objective_index]))
            )

    rng = np.random.default_rng(seed)
    rows: list[EpistasisRow] = []
    for space, samples in sorted(by_space.items()):
        unique = dict(samples)  # deterministic dedup: one row per distinct genotype
        items = list(unique.items())
        if len(items) > max_samples:
            idx = rng.choice(len(items), size=max_samples, replace=False)
            items = [items[i] for i in sorted(idx)]
        if len(items) < folds * 2:
            continue

        genotypes = [g for g, _ in items]
        y = np.asarray([v for _, v in items], dtype=float)
        n_coords = len(genotypes[0])
        n_arch = ARCHITECTURE_EDGE_COUNTS.get(space, n_coords)

        columns: list[np.ndarray] = []
        for i in range(n_coords):
            values = sorted({g[i] for g in genotypes})
            for v in values[:-1]:  # drop one level per coordinate (reference coding)
                columns.append(np.asarray([1.0 if g[i] == v else 0.0 for g in genotypes]))
        x_main = np.column_stack(columns) if columns else np.zeros((len(genotypes), 0))

        inter_columns: list[np.ndarray] = []
        for i in range(n_coords):
            for j in range(i + 1, n_coords):
                if i >= n_arch and j >= n_arch:
                    continue  # neither coordinate is an architecture edge
                vals_i = sorted({g[i] for g in genotypes})[:-1]
                vals_j = sorted({g[j] for g in genotypes})[:-1]
                for vi in vals_i:
                    for vj in vals_j:
                        inter_columns.append(
                            np.asarray(
                                [1.0 if (g[i] == vi and g[j] == vj) else 0.0 for g in genotypes]
                            )
                        )
        x_inter = (
            np.column_stack([x_main] + inter_columns)
            if inter_columns
            else x_main
        )

        cv = KFold(n_splits=folds, shuffle=True, random_state=seed)
        alphas = (0.1, 1.0, 10.0, 100.0)
        r2_main = float(
            cross_val_score(RidgeCV(alphas=alphas), x_main, y, cv=cv, scoring="r2").mean()
        )
        r2_inter = float(
            cross_val_score(RidgeCV(alphas=alphas), x_inter, y, cv=cv, scoring="r2").mean()
        )
        rows.append(
            EpistasisRow(
                search_space=space,
                main_effects_r2=r2_main,
                with_interactions_r2=r2_inter,
                architecture_involving_gain=r2_inter - r2_main,
                n_samples=len(items),
                n_features_main=x_main.shape[1],
                n_features_interaction=x_inter.shape[1] - x_main.shape[1],
            )
        )
    return rows


def render_epistasis_markdown(rows: Sequence[EpistasisRow]) -> str:
    lines = [
        "| Search space | Main-effects R2 | With interactions R2 | "
        "Architecture-involving gain | n samples | n main features | n interaction features |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.search_space} | {r.main_effects_r2:.4f} | {r.with_interactions_r2:.4f} | "
            f"{r.architecture_involving_gain:+.4f} | {r.n_samples} | "
            f"{r.n_features_main} | {r.n_features_interaction} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 7. Cross-baseline margin correlation (Results, "Diagnostics:
#    population-pyramid bootstrap share"; Conclusions).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarginCorrelationResult:
    reference_method: str
    control_method: str
    spearman_rho: float
    p_value: float
    n_pairs: int


def margin_correlation(
    reference_rows: Sequence[object],
    control_rows: Sequence[object],
    *,
    reference_method: str = "p3net",
    control_method: str = "random_search",
) -> MarginCorrelationResult | None:
    """How closely the reference arm's margin against each baseline tracks
    that same baseline's margin against the control arm. Takes the two
    already-computed summary-row sets (reference-vs-all and
    control-vs-all) rather than recomputing metrics, so the correlation is
    guaranteed to be over exactly the numbers the two tables report."""
    from scipy.stats import spearmanr

    ref = {
        (r.method, r.search_space, r.budget): r.effect_size
        for r in reference_rows
        if getattr(r, "effect_size", None) is not None
    }
    ctl = {
        (r.method, r.search_space, r.budget): r.effect_size
        for r in control_rows
        if getattr(r, "effect_size", None) is not None
    }
    shared = sorted(
        k for k in (set(ref) & set(ctl)) if k[0] not in {reference_method, control_method}
    )
    if len(shared) < 3:
        return None
    # Sign convention: both tables report "positive favours the reference
    # arm of that table". A baseline that beats the control arm has a
    # negative delta there, and one that beats the reference arm has a
    # negative delta here -- so the two series are already on the same
    # orientation and no flip is needed.
    a = [ref[k] for k in shared]
    b = [ctl[k] for k in shared]
    rho, p = spearmanr(a, b)
    return MarginCorrelationResult(
        reference_method=reference_method,
        control_method=control_method,
        spearman_rho=float(rho),
        p_value=float(p),
        n_pairs=len(shared),
    )


def render_margin_correlation_markdown(result: MarginCorrelationResult | None) -> str:
    lines = ["| Reference arm | Control arm | Spearman rho | p | n pairs |", "|---|---|---|---|---|"]
    if result is not None:
        lines.append(
            f"| {result.reference_method} | {result.control_method} | "
            f"{result.spearman_rho:.4f} | {result.p_value:.3e} | {result.n_pairs} |"
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# 8. Per-arm record against the control arm (Results, "Diagnostics:
#    population-pyramid bootstrap share" -- the "54 of 160" check).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RejectionCountRow:
    method: str
    cells_significant: int
    cells_total: int


def rejection_counts(rows: Sequence[object]) -> list[RejectionCountRow]:
    """Per-arm count of (search space, budget) cells in which that arm's
    comparison against the table's reference arm rejects H0."""
    total: dict[str, int] = defaultdict(int)
    hits: dict[str, int] = defaultdict(int)
    for r in rows:
        if getattr(r, "reject_null", None) is None:
            continue
        total[r.method] += 1
        if r.reject_null:
            hits[r.method] += 1
    return [
        RejectionCountRow(method=m, cells_significant=hits[m], cells_total=total[m])
        for m in sorted(total)
    ]


def render_rejection_counts_markdown(rows: Sequence[RejectionCountRow]) -> str:
    lines = ["| Method | Cells rejecting H0 | Cells total |", "|---|---|---|"]
    for r in sorted(rows, key=lambda r: (-r.cells_significant, r.method)):
        lines.append(f"| {r.method} | {r.cells_significant} | {r.cells_total} |")
    total_sig = sum(r.cells_significant for r in rows)
    total_all = sum(r.cells_total for r in rows)
    lines.append(f"| **all arms** | **{total_sig}** | **{total_all}** |")
    return "\n".join(lines) + "\n"
