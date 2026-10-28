"""A8 resource test, summary (notes/plans/v005-a8-runbook.md): reads the raw files of a
`configs/pipeline/v005-resources.yaml` run root and writes, per method,
- wall time and peak memory at budgets 100 and 350 (median and max over search spaces),
- the growth exponent k of wall time in the budget (t ~ b^k, from 100 -> 350, median),
- the projected worker-hours of a grid plan (default configs/pipeline/v005.yaml: its
  budgets x search spaces x seeds), interpolating t(b) = t(350) (b / 350)^k per space.

Several run roots: the first one wins where a point exists in more than one; later roots only fill the gaps
(e.g. a point re-run alone after an out-of-memory kill in the main root).

  python scripts/summarize_resources_v005.py RUN_ROOT [MORE_RUN_ROOTS ...] [--plan configs/pipeline/v005.yaml]
      [--workers 6] [--out RUN_ROOT/resources_summary.md]
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def load(run_root: Path) -> dict:
    runs = {}
    for f in (run_root / "raw").glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        res = d.get("diagnostics", {}).get("resources", {})
        runs[(d["method"], d["search_space"], int(d["budget"]))] = {
            "wall": res.get("wall_seconds"), "rss": res.get("process_peak_rss_mb"),
            "bridge": res.get("bridge_peak_rss_mb"), "evals": d.get("evaluations_used"),
            "level4_ok": all(c.get("ok") is not False for c in (d["diagnostics"].get("level4") or {}).values()),
        }
    return runs


def plan_points(plan_path: Path) -> list[tuple[str, str, int, int]]:
    from scripts import run_pipeline as rp

    plan = rp.load_plan(plan_path)
    return [(p.method, p.search_space, p.budget, p.seed) for st in plan["stages"]
            if st.get("kind", "grid") == "grid" for p in rp.expand_stage(st)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_roots", type=Path, nargs="+")
    ap.add_argument("--plan", type=Path, default=ROOT / "configs" / "pipeline" / "v005.yaml")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    runs = {}
    for root in a.run_roots:
        for key, r in load(root).items():
            runs.setdefault(key, r)
    by_method = defaultdict(dict)
    for (m, s, b), r in runs.items():
        by_method[m][(s, b)] = r

    def k_of(m: str, s: str) -> float | None:
        r1, r2 = by_method[m].get((s, 100)), by_method[m].get((s, 350))
        if not r1 or not r2 or not r1["wall"] or not r2["wall"]:
            return None
        return math.log(r2["wall"] / r1["wall"]) / math.log(350 / 100)

    hours = defaultdict(float)
    missing = set()
    for m, s, b, _seed in plan_points(a.plan):
        r350 = by_method.get(m, {}).get((s, 350))
        k = k_of(m, s) if m in by_method else None
        if not r350 or not r350["wall"] or k is None:
            missing.add((m, s))
            continue
        hours[m] += r350["wall"] * (b / 350) ** k / 3600.0

    lines = ["| method | wall b=100 median [s] | wall b=350 median / max [s] | k | peak RSS max [MB] | "
             "bridge RSS max [MB] | level 4 | grid worker-hours |", "|---|---|---|---|---|---|---|---|"]
    for m in sorted(by_method):
        rs = by_method[m]
        w100 = [r["wall"] for (s, b), r in rs.items() if b == 100 and r["wall"]]
        w350 = [r["wall"] for (s, b), r in rs.items() if b == 350 and r["wall"]]
        ks = [k for k in (k_of(m, s) for s in {s for s, _ in rs}) if k is not None]
        rss = max((r["rss"] or 0) for r in rs.values())
        bridge = max((r["bridge"] or 0) for r in rs.values())
        ok = all(r["level4_ok"] for r in rs.values())
        lines.append(
            f"| {m} | {statistics.median(w100):.0f} | {statistics.median(w350):.0f} / {max(w350):.0f} | "
            f"{statistics.median(ks):.2f} | {rss:.0f} | {bridge:.0f} | {'OK' if ok else 'FAIL'} | {hours[m]:.0f} |"
            if w100 and w350 and ks else f"| {m} | incomplete | | | | | | |")
    total = sum(hours.values())
    lines += ["", f"Grid `{a.plan.name}`: **{total:.0f} worker-hours**, i.e. {total / a.workers / 24:.1f} days at "
              f"{a.workers} workers (one machine).", ""]
    if missing:
        lines.append(f"Not projected (missing measurements): {sorted(missing)[:20]}")
    text = "\n".join(lines)
    out = a.out or a.run_roots[0] / "resources_summary.md"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
