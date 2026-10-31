"""A8 analysis (notes/plans/v005-a8-runbook.md): projected wall time of the v005 grid under grid variants, and
per-method memory above the benchmark's own footprint.

Time model per (method, space): measured wall times at b=100 and b=350 (one seed), t(b) = t(b0) (b / b0)^k with
b0 = 100 for b <= 100 and b0 = 350 above; k from the space's own pair, else the method's median k. NB201 in the
grid (nas_bench_201_v005, energy objective) is timed from the A8 runs on nas_bench_201 (FLOPs; same lookup cost).
A point whose measurement is missing at its reference budget (Vizier at b=350 on JAHS: out of memory) is listed,
not projected.

Memory: process peak RSS minus random search's on the same space and budget (the benchmark data loaded into the
worker process is common to both); the JAHS bridge memory was not recorded in A8.

  python scripts/analyze_a8_v005.py results/a8/ec1ba9cb results/a8/e6734ccd results/a8/7b7abd84  (moved out of results/runs/ 2026-10-31)
"""

from __future__ import annotations

import argparse
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.summarize_resources_v005 import load, plan_points  # noqa: E402

GP = {"v005_vizier", "v005_qnehvi", "v005_qparego"}
ALIAS = {"nas_bench_201_v005": "nas_bench_201"}
SOLO = {"v005_vizier"}  # ~30 GB per run: one at a time, nothing beside it


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_roots", type=Path, nargs="+")
    ap.add_argument("--plan", type=Path, default=ROOT / "configs" / "pipeline" / "v005.yaml")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    runs = {}
    for root in a.run_roots:
        for key, r in load(root).items():
            runs.setdefault(key, r)
    t = {(m, s, b): r["wall"] for (m, s, b), r in runs.items() if r["wall"]}

    def k_space(m, s):
        if (m, s, 100) in t and (m, s, 350) in t:
            return math.log(t[(m, s, 350)] / t[(m, s, 100)]) / math.log(3.5)
        return None

    methods = sorted({m for m, _, _ in t})
    k_med = {m: statistics.median([k for s in {s for mm, s, _ in t if mm == m}
                                   if (k := k_space(m, s)) is not None] or [1.0]) for m in methods}

    def seconds(m, s, b):
        s = ALIAS.get(s, s)
        b0 = 100 if b <= 100 else 350
        if (m, s, b0) not in t:
            return None
        k = k_space(m, s)
        return t[(m, s, b0)] * (b / b0) ** (k if k is not None else k_med[m])

    points = plan_points(a.plan)
    variants = {
        "S0: v005.yaml as drafted (all budgets for all methods)": lambda m, b: True,
        "S1: GP arms (Vizier, qNEHVI, qParEGO) only at b = 50, 100": lambda m, b: m not in GP or b <= 100,
    }
    print(f"plan {a.plan.name}: {len(points)} points, seeds {min(p[3] for p in points)}-{max(p[3] for p in points)}\n")
    for name, keep in variants.items():
        lane, solo, missing = defaultdict(float), defaultdict(float), set()
        for m, s, b, _ in points:
            if not keep(m, b):
                continue
            sec = seconds(m, s, b)
            if sec is None:
                missing.add((m, s, b))
                continue
            (solo if m in SOLO else lane)[m] += sec / 3600
        main_h, solo_h = sum(lane.values()), sum(solo.values())
        print(f"## {name}")
        print(f"   {args_line(main_h, solo_h, a.workers)}")
        top = sorted({**lane, **solo}.items(), key=lambda x: -x[1])[:6]
        print("   largest: " + ", ".join(f"{m.removeprefix('v005_')} {h:.0f} h" for m, h in top))
        if missing:
            grouped = defaultdict(set)
            for m, s, b in missing:
                grouped[m].add(f"{s}@{b}")
            print("   not projected (no measurement): " + "; ".join(f"{m}: {sorted(v)}" for m, v in grouped.items()))
        print()

    print("## memory above random search (same space and budget), MB: max over spaces at b=350 (b=100 if absent)")
    rss = {(m, s, b): r["rss"] for (m, s, b), r in runs.items() if r["rss"]}
    rows = []
    for m in methods:
        over = []
        for (mm, s, b), v in rss.items():
            if mm == m and ("v005_random_search", s, b) in rss:
                over.append((v - rss[("v005_random_search", s, b)], s, b))
        if over:
            d, s, b = max(over)
            rows.append((d, m, s, b))
    for d, m, s, b in sorted(rows, reverse=True):
        print(f"   {m.removeprefix('v005_'):16s} {d:8.0f}  ({s}, b={b})")


def args_line(main_h: float, solo_h: float, workers: int) -> str:
    days_main = main_h / workers / 24
    days_solo = solo_h / 24
    return (f"{main_h:.0f} worker-hours on {workers} workers = {days_main:.1f} days; Vizier alone (1 worker): "
            f"{solo_h:.0f} h = {days_solo:.1f} days -> one machine sequentially {days_main + days_solo:.1f} days, "
            f"two machines {max(days_main, days_solo):.1f} days")


if __name__ == "__main__":
    main()
