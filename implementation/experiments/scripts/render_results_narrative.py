"""
Render the Results section's data-bearing sentences straight from the
generated tables.

Audit finding B1/B2: the "Fixed-budget summary" and per-dataset ranking
paragraphs were written by hand against one reporting pass and never
reconciled with the next one. Eleven separate figures in them disagreed
with the tables printed on the same page -- including the headline count
of significant comparisons.

Rather than fix those sentences once by hand and reintroduce the same
failure mode, this script generates them. The output is a LaTeX fragment
meant to be pasted into (or \\input from) chapters/v003/results/main.tex,
so the number in the prose and the number in the table have one source.

Usage:
    python scripts/render_results_narrative.py
    python scripts/render_results_narrative.py --out ../../chapters/v003/results/_generated_summary.tex
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
TABLES_DIR = EXPERIMENTS_ROOT / "results" / "tables"

#: How each arm is spelled in the paper.
DISPLAY_NAMES = {
    "mo_bohb": "MO-BOHB",
    "nsga_net": "NSGA-Net",
    "nsganetv2": "NSGANetV2",
    "p3_absolute": "P3+abs.\\ regressor",
    "p3_alone": "P3-alone",
    "p3_alone_pop20": "P3-alone-pop20",
    "p3_alone_pop40": "P3-alone-pop40",
    "p3net": "P3Net",
    "random_search": "random search",
    "sh_emoa": "SH-EMOA",
    "tpe": "TPE",
}

SPACE_NAMES = {
    "jahs_bench_201": "CIFAR-10",
    "jahs_bench_201_colorectal": "Colorectal-Histology",
    "jahs_bench_201_fashion": "Fashion-MNIST",
    "nas_hpo_bench_ii": "NAS-HPO-Bench-II",
}

#: Arms that share P3Net's own search engine -- the ablation family the
#: central question is staked on. Everything else is "differently
#: engineered".
P3_ENGINE_FAMILY = {"p3_alone", "p3_alone_pop20", "p3_alone_pop40", "p3_absolute"}

NUMBER_WORDS = {
    0: "none", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
    7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
}


@dataclass(frozen=True)
class Row:
    method: str
    search_space: str
    budget: int
    metric: str
    median: float
    iqr: float
    n: int
    adj_p: float | None
    effect: float | None
    reject: bool | None


def read_table(path: Path) -> list[Row]:
    rows: list[Row] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 10 or cells[0] in {"Method", "---"} or set(cells[0]) <= {"-"}:
            continue
        rows.append(
            Row(
                method=cells[0],
                search_space=cells[1],
                budget=int(cells[2]),
                metric=cells[3],
                median=float(cells[4]),
                iqr=float(cells[5]),
                n=int(cells[6]),
                adj_p=None if cells[7] == "--" else float(cells[7]),
                effect=None if cells[8] == "--" else float(cells[8]),
                reject=None if cells[9] == "--" else (cells[9] == "yes"),
            )
        )
    return rows


def _word(n: int) -> str:
    return NUMBER_WORDS.get(n, str(n))


def _cell_label(row: Row) -> str:
    return f"{SPACE_NAMES.get(row.search_space, row.search_space)}, budget~{row.budget}"


def render_fixed_budget_paragraph(rows: list[Row]) -> str:
    comparisons = [r for r in rows if r.reject is not None]
    rejected = [r for r in comparisons if r.reject]
    favour_ref = [r for r in rejected if (r.effect or 0) > 0]
    favour_base = [r for r in rejected if (r.effect or 0) < 0]

    ref_internal = [r for r in favour_ref if r.method in P3_ENGINE_FAMILY]
    ref_external = [r for r in favour_ref if r.method not in P3_ENGINE_FAMILY]
    base_internal = [r for r in favour_base if r.method in P3_ENGINE_FAMILY]
    base_external = [r for r in favour_base if r.method not in P3_ENGINE_FAMILY]

    def listing(items: list[Row], limit: int = 4) -> str:
        parts = [
            f"{DISPLAY_NAMES.get(r.method, r.method)}, {_cell_label(r)}, "
            f"$\\delta={r.effect:+.3f}$, $p={r.adj_p:.3f}$"
            for r in sorted(items, key=lambda r: -abs(r.effect or 0))[:limit]
        ]
        return "; ".join(parts)

    out = [
        f"\\textbf{{{len(rejected)} of the {len(comparisons)} comparisons reject the null "
        f"hypothesis}} at $\\alpha=0.05$. "
        f"{_word(len(favour_base)).capitalize()} favour the baseline over P3Net; "
        f"{_word(len(favour_ref))} favour P3Net. "
        "The composition of each side matters more than the raw count. ",
        f"Of the {_word(len(favour_ref))} P3Net-favouring rejections, {_word(len(ref_internal))} "
        f"{'is' if len(ref_internal) == 1 else 'are'} internal to the P3 engine's own "
        "surrogate-type/population comparisons (P3-alone, P3-alone-pop20, P3-alone-pop40, or "
        "P3+absolute-regressor) -- exactly the family the central question "
        "(Section~\\ref{sec:introduction}) is staked on -- and "
        f"{_word(len(ref_external))} {'is' if len(ref_external) == 1 else 'are'} "
        "against a differently-engineered baseline",
    ]
    if ref_external:
        out.append(f" ({listing(ref_external)})")
    out.append(". ")
    out.append(
        f"Of the {_word(len(favour_base))} baseline-favouring rejections, "
        f"{_word(len(base_external))} "
        f"{'is a loss' if len(base_external) == 1 else 'are losses'} to a "
        "differently-engineered method (SH-EMOA, TPE, NSGA-Net, or NSGANetV2) and "
        f"{_word(len(base_internal))} "
        f"{'is a loss' if len(base_internal) == 1 else 'are losses'} \\emph{{within}} the "
        "P3-engine family itself -- cases where plain P3-alone, its population-size variants, "
        "or the absolute-regressor variant beats P3Net's own relative surrogate outright"
    )
    if base_internal:
        out.append(f" ({listing(base_internal)})")
    out.append(".")
    return "".join(out)


def render_ablation_family_paragraph(rows: list[Row]) -> str:
    by_space: dict[str, list[Row]] = defaultdict(list)
    for r in rows:
        if r.reject is not None and r.method in P3_ENGINE_FAMILY:
            by_space[r.search_space].append(r)

    sentences = []
    for space in sorted(by_space, key=lambda s: -sum(1 for r in by_space[s] if r.reject and (r.effect or 0) > 0)):
        wins = [r for r in by_space[space] if r.reject and (r.effect or 0) > 0]
        losses = [r for r in by_space[space] if r.reject and (r.effect or 0) < 0]
        per_arm: dict[str, int] = defaultdict(int)
        for r in wins:
            per_arm[r.method] += 1
        detail = ", ".join(
            f"{DISPLAY_NAMES.get(m, m)} at {v} of 4 budgets" for m, v in sorted(per_arm.items())
        )
        name = SPACE_NAMES.get(space, space)
        if wins and not losses:
            sentences.append(f"On {name}, P3Net significantly beats {detail}, with no ablation loss anywhere.")
        elif wins and losses:
            loss_detail = ", ".join(
                f"{DISPLAY_NAMES.get(r.method, r.method)} at budget~{r.budget} "
                f"($\\delta={r.effect:+.3f}$)"
                for r in sorted(losses, key=lambda r: r.budget)
            )
            sentences.append(
                f"On {name}, P3Net beats {detail}, but loses to {loss_detail}."
            )
        elif losses:
            loss_detail = ", ".join(
                f"{DISPLAY_NAMES.get(r.method, r.method)} at budget~{r.budget} "
                f"($\\delta={r.effect:+.3f}$)"
                for r in sorted(losses, key=lambda r: r.budget)
            )
            sentences.append(
                f"On {name}, no ablation comparison favours P3Net at any budget, and it loses to "
                f"{loss_detail}."
            )
        else:
            sentences.append(
                f"On {name}, no ablation comparison reaches significance in either direction."
            )
    return " ".join(sentences)


def render_external_trend_paragraph(rows: list[Row]) -> str:
    """How losses to differently-engineered baselines grow with budget, and
    the primary-baseline (NSGANetV2) record per search space."""
    external = {"sh_emoa", "tpe", "nsga_net", "nsganetv2"}
    budgets = sorted({r.budget for r in rows})
    losses = {
        b: sum(
            1
            for r in rows
            if r.budget == b and r.method in external and r.reject and (r.effect or 0) < 0
        )
        for b in budgets
    }
    trend = ", ".join(
        (f"none at budget~{b}" if losses[b] == 0 else f"{losses[b]} at budget~{b}") for b in budgets
    )

    nsga2 = [r for r in rows if r.method == "nsganetv2" and r.reject is not None]
    by_space: dict[str, list[Row]] = defaultdict(list)
    for r in nsga2:
        by_space[r.search_space].append(r)
    lost_everywhere_from: list[str] = []
    never: list[str] = []
    other: list[str] = []
    for space, space_rows in sorted(by_space.items()):
        sig_losses = sorted(r.budget for r in space_rows if r.reject and (r.effect or 0) < 0)
        sig_wins = [r for r in space_rows if r.reject and (r.effect or 0) > 0]
        name = SPACE_NAMES.get(space, space)
        if not sig_losses and not sig_wins:
            never.append(name)
        elif sig_losses and not sig_wins and sig_losses == [b for b in budgets if b >= sig_losses[0]]:
            lost_everywhere_from.append(f"{name} (from budget~{sig_losses[0]})")
        else:
            other.append(name)

    parts = [f"Significant losses to SH-EMOA, TPE, NSGA-Net, or NSGANetV2 grow with budget: {trend}."]
    if lost_everywhere_from or never:
        clause = "Against NSGANetV2 specifically, P3Net"
        pieces = []
        if lost_everywhere_from:
            pieces.append(
                "loses significantly at every budget on " + " and ".join(lost_everywhere_from)
            )
        if never:
            pieces.append("does not separate at any budget on " + " or ".join(never))
        parts.append(clause + " " + ", and ".join(pieces) + ".")
    if other:
        parts.append("The NSGANetV2 comparison is mixed on " + ", ".join(other) + ".")
    return " ".join(parts)


def render_ranking_paragraph(rows: list[Row]) -> str:
    """Ranks are reported only as a compact per-space trajectory. The
    prose version of this paragraph was wrong in every one of its four
    claims; a generated trajectory is both correct and shorter."""
    by_cell: dict[tuple[str, int], list[Row]] = defaultdict(list)
    for r in rows:
        by_cell[(r.search_space, r.budget)].append(r)

    lines = []
    for space in sorted({s for s, _ in by_cell}):
        budgets = sorted({b for s, b in by_cell if s == space})
        ranks = []
        n_arms = 0
        for b in budgets:
            group = by_cell[(space, b)]
            minimised = group[0].metric == "igd_plus"
            ordered = sorted(group, key=lambda r: r.median, reverse=not minimised)
            n_arms = len(ordered)
            ranks.append(next(i + 1 for i, r in enumerate(ordered) if r.method == "p3net"))
        lines.append(
            f"{SPACE_NAMES.get(space, space)} {'/'.join(str(x) for x in ranks)} of {n_arms}"
        )
    return (
        "P3Net's rank by median primary metric, per search space across the four budget tiers "
        "(50/100/200/350): " + "; ".join(lines) + "."
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    rows = read_table(args.tables_dir / "fixed_budget_summary.md")
    if not rows:
        raise SystemExit("no rows -- run scripts/generate_report.py first")

    fragment = "\n".join(
        [
            "% GENERATED by scripts/render_results_narrative.py -- do not edit by hand.",
            "% Regenerate after every reporting pass; the numbers here and the numbers in",
            "% results/tables/fixed_budget_summary.md have one source by construction.",
            "",
            render_fixed_budget_paragraph(rows),
            "",
            render_ablation_family_paragraph(rows),
            "",
            render_ranking_paragraph(rows),
            "",
        ]
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(fragment, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(fragment)


if __name__ == "__main__":
    main()
