"""
Guard: every number the paper quotes must exist in a generated table.

Audit finding R3. The Results narrative drifted out of sync with the
tables it describes -- the prose said "61 of 160 comparisons reject" while
the tables on the same page said 54, and eleven further per-comparison
figures disagreed too. Both had been correct at some point; the tables
were regenerated after a re-run and the prose was not.

This script extracts every numeric literal from the paper's data-bearing
chapters and checks it against the generated tables under
results/tables/. Anything with no match is reported as orphaned: either a
stale number, or a real number that still has no regenerable source.

It is deliberately a lint, not a proof. Matching is by rendered string at
the table's own precision, so it cannot tell a correct number from a
coincidentally-equal one, and it does not understand that "0.9577" in the
.tex should correspond to the P3Net row specifically. What it does catch
is exactly the failure mode that actually happened: a number that appears
in the paper and nowhere in the data.

Usage:
    python scripts/check_paper_numbers.py            # report orphans
    python scripts/check_paper_numbers.py --strict   # exit 1 if any
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent

#: Chapters whose numbers are claims about measured data. Chapters that
#: only cite the literature (related work, introduction) are excluded --
#: their numbers come from other people's papers, not from results/.
DATA_BEARING_CHAPTERS = (
    "chapters/v003/results/main.tex",
    "chapters/v003/conclusions/main.tex",
    "chapters/v003/abstract/main.tex",
)

TABLE_DIRS = (
    EXPERIMENTS_ROOT / "results" / "tables",
    EXPERIMENTS_ROOT.parent / "experiments-bartnik" / "results",
    EXPERIMENTS_ROOT.parent / "experiments-przewozniczek" / "results",
    EXPERIMENTS_ROOT / "results",
)

#: Numbers that are configuration, not measurement: budget tiers, seed
#: counts, arm counts, benchmark dimensions, years, section numbers. These
#: legitimately appear in the prose with no table behind them.
ALLOWED_LITERALS = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "14", "16",
    "20", "25", "30", "32", "35", "40", "50", "58", "64", "100", "128", "200", "256",
    "350", "500", "160", "144", "112", "2026", "2027", "201", "101", "360",
    "0.05", "0.5", "0.01", "1.0", "2.0",
}

NUMBER_RE = re.compile(r"(?<![\w.])(\d+\.\d+|\d+)(?![\w.])")
COMMENT_RE = re.compile(r"(?<!\\)%.*")


def _strip_latex(text: str) -> str:
    """Drop comments, \\label/\\ref/\\cite/\\includegraphics/\\texttt
    arguments, and colour specs -- all of them carry digits that are
    markup, not claims (e.g. `budget350.png`, `3987E5`, `tab:heatmap-jahs`)."""
    text = COMMENT_RE.sub("", text)
    # ACM classification metadata: concept ids and significance weights
    # (e.g. `\ccsdesc[300]{...}`, `<concept_significance>500`) are markup.
    text = re.sub(r"\\begin\{CCSXML\}.*?\\end\{CCSXML\}", " ", text, flags=re.S)
    text = re.sub(r"\\ccsdesc\[\d+\]", " ", text)
    for macro in ("label", "ref", "citep", "cite", "includegraphics", "texttt", "colorbox", "fcolorbox"):
        text = re.sub(r"\\" + macro + r"\s*(\[[^\]]*\])?\{[^{}]*\}", " ", text)
    text = re.sub(r"\[HTML\]\{[0-9A-Fa-f]+\}", " ", text)
    text = re.sub(r"\\makebox\[[^\]]*\]", " ", text)
    return text


def collect_paper_numbers(repo_root: Path) -> dict[str, list[str]]:
    """Number -> the chapters it appears in."""
    found: dict[str, list[str]] = {}
    for rel in DATA_BEARING_CHAPTERS:
        path = repo_root / rel
        if not path.exists():
            continue
        text = _strip_latex(path.read_text(encoding="utf-8"))
        for match in NUMBER_RE.finditer(text):
            literal = match.group(1)
            found.setdefault(literal, [])
            if rel not in found[literal]:
                found[literal].append(rel)
    return found


def collect_table_numbers(table_dirs=TABLE_DIRS) -> set[str]:
    """Every numeric literal appearing in a generated table, plus the same
    values re-rendered at coarser precision -- the paper legitimately
    quotes 0.497 for a table's 0.4970, or 91.0% for a share of 0.9100."""
    literals: set[str] = set()
    for directory in table_dirs:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.md")):
            for match in NUMBER_RE.finditer(path.read_text(encoding="utf-8")):
                raw = match.group(1)
                literals.add(raw)
                try:
                    value = float(raw)
                except ValueError:
                    continue
                # Coarser renderings with at least one decimal place only.
                # Rounding a non-integer to 0 places manufactures small
                # integers (61, 24, 37, ...) out of unrelated values, which
                # is exactly how stale integer counts slipped past an
                # earlier version of this check.
                for places in (1, 2, 3, 4):
                    literals.add(f"{value:.{places}f}")
                    literals.add(f"{abs(value):.{places}f}")
                    # percentage rendering of a [0,1] share
                    if 0.0 <= abs(value) <= 1.0:
                        literals.add(f"{abs(value) * 100:.{places}f}")
                # integer rendering, so a table's 54 matches prose "54"
                if value == int(value):
                    literals.add(str(int(value)))
    return literals


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--strict", action="store_true", help="Exit 1 if any orphaned number is found."
    )
    args = parser.parse_args(argv)

    paper = collect_paper_numbers(args.repo_root)
    tables = collect_table_numbers()
    if not tables:
        raise SystemExit(
            "no generated tables found -- run scripts/generate_report.py first"
        )

    orphans = {
        literal: chapters
        for literal, chapters in sorted(paper.items(), key=lambda kv: kv[0])
        if literal not in ALLOWED_LITERALS and literal not in tables
    }

    print(f"{len(paper)} distinct numbers in the paper's data-bearing chapters")
    print(f"{len(tables)} numeric literals available across generated tables")
    if not orphans:
        print("no orphaned numbers -- every quoted figure has a table behind it")
        return

    print(f"\n{len(orphans)} orphaned number(s) -- quoted in the paper, absent from every table:")
    for literal, chapters in orphans.items():
        print(f"  {literal:>12}   {', '.join(c.split('/')[-2] for c in chapters)}")
    if args.strict:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
