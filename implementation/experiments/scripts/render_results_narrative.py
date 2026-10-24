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


def reference_method(rows: list[Row]) -> str:
    """A3 (audit): the reference arm, read from the data -- the method with no comparison of
    its own in every cell where other methods have one."""
    cells: dict[tuple[str, int], list[Row]] = defaultdict(list)
    for r in rows:
        cells[(r.search_space, r.budget)].append(r)
    candidates = None
    for cell_rows in cells.values():
        if not any(r.reject is not None for r in cell_rows):
            continue
        here = {r.method for r in cell_rows if r.reject is None and r.adj_p is None}
        candidates = here if candidates is None else candidates & here
    if not candidates or len(candidates) != 1:
        raise ValueError(f"cannot identify the reference arm from the table: {sorted(candidates or [])}")
    return next(iter(candidates))


def _name(method: str) -> str:
    return DISPLAY_NAMES.get(method, method)


def _favours_ref(r: Row) -> bool:
    return bool(r.reject) and (r.effect or 0) > 0


def _favours_base(r: Row) -> bool:
    return bool(r.reject) and (r.effect or 0) < 0


def render_fixed_budget_paragraph(rows: list[Row], families: dict[str, set[str]] | None = None) -> str:
    """A3: every count with its direction, every significant result listed (no top-k), the
    reference arm from the data; optional method families (e.g. the reference's own
    engine) come from the caller, not from the text."""
    ref = _name(reference_method(rows))
    comparisons = [r for r in rows if r.reject is not None]
    rejected = [r for r in comparisons if r.reject]
    favour_ref = [r for r in rejected if _favours_ref(r)]
    favour_base = [r for r in rejected if _favours_base(r)]

    def listing(items: list[Row]) -> str:
        return "; ".join(
            f"{_name(r.method)}, {_cell_label(r)}, $\\delta={r.effect:+.3f}$, $p={r.adj_p:.3f}$"
            for r in sorted(items, key=lambda r: (r.method, r.search_space, r.budget))
        )

    out = [
        f"\\textbf{{{len(rejected)} of the {len(comparisons)} comparisons reject the null hypothesis}} "
        f"at $\\alpha=0.05$. {_word(len(favour_base)).capitalize()} favour the baseline over {ref}; "
        f"{_word(len(favour_ref))} favour {ref}."
    ]
    for label, members in (families or {}).items():
        fr = [r for r in favour_ref if r.method in members]
        fb = [r for r in favour_base if r.method in members]
        n = sum(1 for r in comparisons if r.method in members)
        out.append(f" Within {label} ({n} comparisons): {_word(len(fr))} favour {ref}, "
                   f"{_word(len(fb))} favour the other arm.")
    if favour_ref:
        out.append(f" Significant in favour of {ref}: {listing(favour_ref)}.")
    if favour_base:
        out.append(f" Significant in favour of the baseline: {listing(favour_base)}.")
    return "".join(out)


def render_ablation_family_paragraph(rows: list[Row], family: set[str] | None = None) -> str:
    """Per search space, the reference arm against the given family (A3: the family is an
    argument, budget counts come from the data). Without a family: empty."""
    if not family:
        return ""
    ref = _name(reference_method(rows))
    sentences = []
    for space in sorted({r.search_space for r in rows}):
        space_rows = [r for r in rows if r.search_space == space and r.reject is not None and r.method in family]
        if not space_rows:
            continue
        n_budgets = len({r.budget for r in rows if r.search_space == space})
        wins = [r for r in space_rows if _favours_ref(r)]
        losses = [r for r in space_rows if _favours_base(r)]
        per_arm: dict[str, int] = defaultdict(int)
        for r in wins:
            per_arm[r.method] += 1
        detail = ", ".join(f"{_name(m)} at {v} of {n_budgets} budgets" for m, v in sorted(per_arm.items()))
        loss_detail = ", ".join(f"{_name(r.method)} at budget~{r.budget} ($\\delta={r.effect:+.3f}$)"
                                for r in sorted(losses, key=lambda r: (r.budget, r.method)))
        name = SPACE_NAMES.get(space, space)
        if wins and not losses:
            sentences.append(f"On {name}, {ref} significantly beats {detail}, with no loss in this family.")
        elif wins:
            sentences.append(f"On {name}, {ref} beats {detail}, but loses to {loss_detail}.")
        elif losses:
            sentences.append(f"On {name}, no comparison in this family favours {ref}; it loses to {loss_detail}.")
        else:
            sentences.append(f"On {name}, no comparison in this family reaches significance in either direction.")
    return " ".join(sentences)


def render_external_trend_paragraph(rows: list[Row], external: set[str] | None = None) -> str:
    """Significant results by budget, both directions (A3), over `external` arms (default: all
    non-reference arms)."""
    ref_key = reference_method(rows)
    ref = _name(ref_key)
    arms = external or {r.method for r in rows} - {ref_key}
    budgets = sorted({r.budget for r in rows})
    parts = []
    for b in budgets:
        cell = [r for r in rows if r.budget == b and r.method in arms and r.reject is not None]
        parts.append(f"budget~{b}: {sum(_favours_ref(r) for r in cell)} for {ref}, "
                     f"{sum(_favours_base(r) for r in cell)} against, of {len(cell)}")
    return "Significant comparisons by budget -- " + "; ".join(parts) + "."


def render_ranking_paragraph(rows: list[Row]) -> str:
    """Rank of the reference arm by median primary metric per search space (budgets and
    reference from the data)."""
    ref_key = reference_method(rows)
    by_cell: dict[tuple[str, int], list[Row]] = defaultdict(list)
    for r in rows:
        by_cell[(r.search_space, r.budget)].append(r)
    budgets_all = sorted({b for _, b in by_cell})
    lines = []
    for space in sorted({s for s, _ in by_cell}):
        budgets = sorted({b for s, b in by_cell if s == space})
        ranks, sizes = [], []
        for b in budgets:
            group = by_cell[(space, b)]
            minimised = group[0].metric == "igd_plus"
            ordered = sorted(group, key=lambda r: r.median, reverse=not minimised)
            sizes.append(len(ordered))
            ranks.append(next(i + 1 for i, r in enumerate(ordered) if r.method == ref_key))
        of = str(sizes[0]) if len(set(sizes)) == 1 else "/".join(str(x) for x in sizes)
        lines.append(f"{SPACE_NAMES.get(space, space)} {'/'.join(str(x) for x in ranks)} of {of}")
    return (f"{_name(ref_key)}'s rank by median primary metric, per search space across the budget tiers "
            f"({'/'.join(str(b) for b in budgets_all)}): " + "; ".join(lines) + ".")


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
