"""A5 (audit): cost table of the v004 timing stage (s9_timing: every arm at budget 350, one
run at a time in a fresh process) from a run root's `timing/raw/`, with the gaps of the
quality grid stated next to it.

  python scripts/cost_table_v004.py results/runs/b4d25cac [--out results/tables/cost_s9.md]

Per arm: median over search spaces of wall time, optimiser time (wall minus benchmark
queries) and peak process memory (+ JAHS bridge memory where present), and the spaces
with the largest values. The note lists arms whose quality-grid columns are missing and
why (configs/pipeline/v004-gp-small.yaml: the GP arms ran only at budgets 50 and 100).
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path

#: Arms the quality grid ran only at budgets 50 and 100 (v004-gp-small.yaml, commit 1bba34af):
#: at 200 and 350 they did not fit the 30 GB machine next to the other workers.
GRID_GAPS = {
    "oss_vizier": "quality grid only at budgets 50/100 (~30 GB per run at 350; does not fit beside other workers)",
    "botorch_qnehvi": "quality grid only at budgets 50/100 (8419 s per run at 350; serialised GPU slot)",
    "botorch_qparego": "quality grid only at budgets 50/100 (3192 s per run at 350; serialised GPU slot)",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_root", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    per = defaultdict(list)
    for f in sorted((a.run_root / "timing" / "raw").glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        r = d["diagnostics"].get("resources", {})
        per[d["method"]].append((d["search_space"], r.get("wall_seconds"), r.get("optimizer_seconds"),
                                 r.get("process_peak_rss_mb"), r.get("bridge_peak_rss_mb"), d["evaluations_used"]))
    lines = ["| Arm | Wall s (median) | Optimiser s (median) | Peak RSS MB (max) | Bridge RSS MB (max) | "
             "Slowest space | Note |", "|---|---|---|---|---|---|---|"]
    for m in sorted(per, key=lambda m: -statistics.median(x[1] for x in per[m])):
        xs = per[m]
        slow = max(xs, key=lambda x: x[1])
        bridges = [x[4] for x in xs if x[4] is not None]
        bridge = f"{max(bridges):.0f}" if bridges else "n/r"
        lines.append(f"| {m} | {statistics.median(x[1] for x in xs):.0f} | {statistics.median(x[2] for x in xs):.0f} | "
                     f"{max(x[3] for x in xs):.0f} | {bridge} | {slow[0]} ({slow[1]:.0f} s) | "
                     f"{GRID_GAPS.get(m, '')} |")
    text = ("# v004 cost (s9_timing: budget 350, one run per arm and space, sequential)\n\n" + "\n".join(lines) +
            "\n\nn/r = not recorded (v004 did not record the JAHS bridge memory, #29; recorded in v005).\n"
            "Arms with a note have measured costs here but **no quality results at budgets 200 and 350** "
            "(the Holm family of those cells is smaller by these arms).\n")
    out = a.out or Path("results/tables/cost_s9.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
