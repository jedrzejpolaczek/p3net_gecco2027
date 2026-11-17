"""
Freeze the current results/{raw,tables,figures}/ into a single,
self-contained, identifiable folder under results/archive/<name>/.

results/raw/ is a live, additive database (scripts/run_grid.py only ever
adds points, never removes or rewrites an unrelated one) and
results/tables/ + results/figures/ are point-in-time computed views over
it, fully overwritten by scripts/generate_report.py on every run. Neither
fact makes the *current* state easy to recover once the grid moves on.
scripts/generate_report.py now calls archive_snapshot() with an
auto-generated name (auto_snapshot_name(), below) after every report
regeneration by default, so there is no separate step to remember to run --
`--no-archive` opts back out for quick, throwaway iteration that shouldn't
clutter results/archive/. archive_snapshot() also remains directly callable
(or runnable as this script's CLI) with an explicit, human-chosen name for
a deliberately labelled snapshot, same as the two existing ones below.

Every snapshot is self-contained (raw + tables + figures together, not raw
kept apart in some other archive) precisely because the two earlier
snapshots, R10_budgets-50-100-200_2026-08-16 and
R30_budgets-50-100-200-350_2026-08-16, were not: raw/ lived in a separate
results/raw_archive/ folder in between, discovered awkward to work with in
practice and consolidated back in on 2026-08-16 (results/archive/*/MANIFEST.md
of both snapshots record exactly how). This module exists so that
consolidation only has to happen once.

Only copies files -- writes results/archive/<name>/MANIFEST.md as a
template with the mechanically-derivable facts (file counts, git commit,
timestamp) already filled in and the narrative sections (headline result,
known gaps, what motivated this snapshot) left as prompts for whoever wants
a fully documented snapshot to fill in by hand; summarising what changed and
why is a judgement call this script has no way to make on its own, and is
not expected to be filled in for every auto-archived snapshot -- only ones
worth writing up, same as the two existing hand-labelled ones.

Reference: results/archive/R10_budgets-50-100-200_2026-08-16/MANIFEST.md,
results/archive/R30_budgets-50-100-200-350_2026-08-16/MANIFEST.md (the two
manually-assembled snapshots this module generalises).
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = EXPERIMENTS_ROOT / "results"
ARCHIVE_DIR = RESULTS_DIR / "archive"
BUDGETS_CONFIG = EXPERIMENTS_ROOT / "configs" / "experiment" / "budgets.yaml"


def auto_snapshot_name(*, budgets_config: Path = BUDGETS_CONFIG, now: datetime | None = None) -> str:
    """<R{seeds}>_budgets-<tiers>_<timestamp to the second>, e.g.
    R30_budgets-50-100-200-350_2026-08-16T143005 -- matches the naming
    convention of the two hand-labelled snapshots this generalises
    (`R{n}_budgets-...`_<date>`), with a to-the-second timestamp appended so
    repeated auto-archiving on an unchanged config (results/raw/ simply
    grew) never collides. Falls back to a bare timestamp if budgets.yaml
    can't be read, since a naming detail shouldn't block archiving the
    actual data."""
    now = now or datetime.now()
    stamp = now.strftime("%Y-%m-%dT%H%M%S")
    try:
        config = yaml.safe_load(budgets_config.read_text(encoding="utf-8")) or {}
        n_seeds = len(config["seeds"])
        tiers = "-".join(str(t) for t in config["budget_tiers"])
        return f"R{n_seeds}_budgets-{tiers}_{stamp}"
    except (OSError, KeyError, yaml.YAMLError):
        return f"snapshot_{stamp}"

MANIFEST_TEMPLATE = """\
# Archived report snapshot: {name}

Self-contained frozen copy of `raw/`, `tables/`, and `figures/`, taken {date}.

## Experiment configuration

- `configs/experiment/budgets.yaml`: <!-- TODO: budget_tiers, seeds/R -->
- `configs/methods/*.yaml`: <!-- TODO: which arms, anything non-default -->
- `configs/search_spaces/*.yaml`: <!-- TODO: which benchmarks/datasets -->
- {raw_count} raw runs, {table_count} table file(s), {figure_count} figure file(s).

## Code state

- Git commit: `{git_commit}`{git_dirty_note}

## Why this snapshot

<!-- TODO: what changed since the last snapshot, and what question this run
     was meant to answer -->

## Headline result at this snapshot

<!-- TODO -->

## Known gaps at this snapshot

<!-- TODO: copy forward from the previous snapshot's MANIFEST.md and note
     what's newly available vs. still missing -->
"""


def _git_commit() -> tuple[str, bool]:
    """(short commit hash, has_uncommitted_changes). Best-effort: falls back
    to placeholders if git isn't available or this isn't a git checkout,
    since a missing commit hash shouldn't block archiving the actual data."""
    try:
        commit = (
            subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=EXPERIMENTS_ROOT,
                capture_output=True,
                text=True,
                check=True,
            )
            .stdout.strip()
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=EXPERIMENTS_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        return commit, bool(status.strip())
    except (OSError, subprocess.CalledProcessError):
        return "unknown", False


def _copy_tree(src: Path, dst: Path) -> int:
    if not src.exists():
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in src.iterdir():
        if f.is_file():
            shutil.copy2(f, dst / f.name)
            count += 1
    return count


def archive_snapshot(
    name: str,
    *,
    raw_dir: Path | None = None,
    tables_dir: Path | None = None,
    figures_dir: Path | None = None,
    results_dir: Path = RESULTS_DIR,
    archive_dir: Path = ARCHIVE_DIR,
) -> Path:
    """Copies raw_dir/tables_dir/figures_dir (each defaulting to
    results_dir/{raw,tables,figures} -- the layout scripts/generate_report.py
    itself defaults to, but overridable independently since its own CLI lets
    each of the three be pointed elsewhere separately) into
    archive_dir/name/{raw,tables,figures}, and writes a MANIFEST.md template.
    Raises FileExistsError if archive_dir/name already exists, rather than
    silently merging into or overwriting a previous snapshot with the same
    name."""
    raw_dir = raw_dir if raw_dir is not None else results_dir / "raw"
    tables_dir = tables_dir if tables_dir is not None else results_dir / "tables"
    figures_dir = figures_dir if figures_dir is not None else results_dir / "figures"

    snapshot_dir = archive_dir / name
    if snapshot_dir.exists():
        raise FileExistsError(
            f"{snapshot_dir} already exists -- choose a different name rather than "
            "risk merging into an earlier snapshot"
        )

    raw_count = _copy_tree(raw_dir, snapshot_dir / "raw")
    table_count = _copy_tree(tables_dir, snapshot_dir / "tables")
    figure_count = _copy_tree(figures_dir, snapshot_dir / "figures")

    commit, dirty = _git_commit()
    dirty_note = " (uncommitted working-tree changes present at archival time)" if dirty else ""

    manifest = MANIFEST_TEMPLATE.format(
        name=name,
        date=datetime.now().date().isoformat(),
        raw_count=raw_count,
        table_count=table_count,
        figure_count=figure_count,
        git_commit=commit,
        git_dirty_note=dirty_note,
    )
    (snapshot_dir / "MANIFEST.md").write_text(manifest, encoding="utf-8")

    return snapshot_dir


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Snapshot folder name, e.g. R30_budgets-50-100-200-350_2026-08-16 "
        "(convention: <what changed>_<date>, matching the two hand-labelled snapshots). "
        "Defaults to an auto-generated name (auto_snapshot_name()) if omitted -- "
        "scripts/generate_report.py always omits it.",
    )
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--archive-dir", type=Path, default=ARCHIVE_DIR)
    args = parser.parse_args(argv)

    name = args.name or auto_snapshot_name()
    snapshot_dir = archive_snapshot(name, results_dir=args.results_dir, archive_dir=args.archive_dir)
    print(f"archived snapshot to {snapshot_dir}")
    print(f"fill in the TODOs in {snapshot_dir / 'MANIFEST.md'} by hand if this snapshot is worth documenting")


if __name__ == "__main__":
    main()
