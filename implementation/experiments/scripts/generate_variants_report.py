"""
Single-axis P3Net design-variant comparisons, with explicit provenance.

Audit finding P4: the design-decision ablation round reported in Results
was measured against a `p3net` baseline from BEFORE the population-pyramid
warm-start/hypervolume-contribution fix. The headline grid was re-run
after that fix; the variants round was not. Comparing a pre-fix variant
against the post-fix baseline is not a like-for-like test, and quoting
both in the same section without saying so is the kind of silent
condition change this project's own fairness controls exist to prevent.

This script therefore splits the variants by provenance rather than
pooling them:

* variants whose raw runs postdate the pyramid fix are compared against
  the current `p3net` baseline and reported as valid;
* variants whose raw runs predate it are reported separately, labelled,
  and NOT presented as current -- re-running them is tracked as open work.

The provenance boundary is read from the raw files' own recorded run
date, not hardcoded per method, so adding a re-run variant later moves it
into the valid table automatically.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
import sys

if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from reporting import (
    PRIMARY_SEARCH_SPACES,
    fixed_budget_summary_table,
    load_raw_runs,
    render_summary_table_markdown,
)
from reporting.reference_fronts import load_fronts, load_oracle_fronts

RAW_DIR = EXPERIMENTS_ROOT / "results" / "raw"
TABLES_DIR = EXPERIMENTS_ROOT / "results" / "tables"

BASELINE = "p3net"

#: The population-pyramid warm-start + hypervolume-contribution redesign
#: (Results, "Diagnostics: population-pyramid bootstrap share"). Raw runs
#: written before this date were produced by the pre-fix engine.
PYRAMID_FIX_DATE = dt.date(2026, 8, 18)

#: Everything in configs/methods/ that is a single-axis variant of p3net.
VARIANT_PREFIX = "p3net_"
#: Prefixes of method names that belong to a separate multi-point sweep
#: rather than a single-axis variant. Reported as one line each in the
#: stale table instead of one line per grid point.
SWEEP_PREFIXES = ("p3net_kappa_sensitivity",)


def _run_date(method: str) -> dt.date | None:
    paths = sorted(RAW_DIR.glob(f"{method}__*.json"))
    if not paths:
        return None
    stamps = [dt.date.fromtimestamp(p.stat().st_mtime) for p in paths]
    return min(stamps)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    args = parser.parse_args(argv)

    all_runs = [r for r in load_raw_runs(RAW_DIR) if r.search_space in PRIMARY_SEARCH_SPACES]
    def _group(method: str) -> str:
        for prefix in SWEEP_PREFIXES:
            if method.startswith(prefix):
                return prefix
        return method

    variants = sorted(
        {_group(r.method) for r in all_runs if r.method.startswith(VARIANT_PREFIX)}
        - {BASELINE}
    )
    if not variants:
        raise SystemExit("no p3net_* variant runs found under results/raw/")

    frozen = load_fronts()
    frozen_fronts = {k: v.front for k, v in frozen.items()}
    frozen_references = {k: v.reference_point for k, v in frozen.items()}
    oracle_fronts = load_oracle_fronts()
    baseline_date = _run_date(BASELINE)

    comparable: list[str] = []
    stale: list[tuple[str, dt.date | None]] = []
    for variant in variants:
        when = _run_date(variant)
        if when is not None and when >= PYRAMID_FIX_DATE:
            comparable.append(variant)
        else:
            stale.append((variant, when))

    args.tables_dir.mkdir(parents=True, exist_ok=True)

    header = [
        f"<!-- baseline `{BASELINE}` raw runs dated {baseline_date}; "
        f"pyramid fix boundary {PYRAMID_FIX_DATE}. -->",
        "",
    ]

    if comparable:
        runs = [r for r in all_runs if r.method in {BASELINE, *comparable}]
        # A grouped sweep is never "comparable" as a single arm -- it has
        # many grid points, each its own arm -- so only plain variants
        # reach this table.
        rows = fixed_budget_summary_table(
            runs,
            oracle_fronts=oracle_fronts,
            frozen_fronts=frozen_fronts,
            frozen_references=frozen_references,
            reference_method=BASELINE,
        )
        path = args.tables_dir / "p3net_variants_comparable.md"
        body = "\n".join(
            header
            + [
                "Variants whose raw runs postdate the population-pyramid fix, and are therefore",
                f"directly comparable against the current `{BASELINE}` baseline:",
                "",
                ", ".join(f"`{v}`" for v in comparable),
                "",
                render_summary_table_markdown(rows),
            ]
        )
        path.write_text(body, encoding="utf-8")
        print(f"wrote {path} ({len(comparable)} comparable variant(s))")

    if stale:
        lines = header + [
            "Variants whose raw runs PREDATE the population-pyramid warm-start /",
            "hypervolume-contribution fix. They were measured against a different",
            f"`{BASELINE}` engine than the one the headline grid now reports, so their",
            "numbers are NOT directly comparable with the current baseline and must not",
            "be quoted as current. Re-running them is open work.",
            "",
            "| Variant | Raw runs dated | Status |",
            "|---|---|---|",
        ]
        for variant, when in stale:
            lines.append(f"| {variant} | {when} | pre-fix, needs re-run |")
        path = args.tables_dir / "p3net_variants_stale.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(stale)} stale variant(s))")


if __name__ == "__main__":
    main()
