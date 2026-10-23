"""Level 3 (v005-verification-protocol.md §3): every v005 method x every search space x
{smallest, largest} budget, one seed, through the production runner
(scripts/run_experiment.py:run_single). Each run is a separate process with a time
limit; JAHS-Bench-201 runs are limited in parallel (one bridge holds ~12 GB).

Checks per run: finished without an exception; main track -- evaluations_used ==
budget, or a stop reason the protocol allows (exploration collapse, #36); MF track --
0 < cost_used <= budget and every full-fidelity result counted. A run that hits the time
limit is reported as TIMEOUT (to the resource test, A8), not as a failure.

  python scripts/run_level3_v005.py --out results/level3_v005 [--budgets 50 350] [--timeout 1800]
      [--workers 8] [--jahs-workers 1] [--methods ...] [--spaces ...]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from methods.v005_adapter import V005_METHODS  # noqa: E402

SPACES = ["nas_bench_201_v005", "nas_hpo_bench_ii_v005", "jahs_bench_201_v005", "jahs_bench_201_colorectal_v005",
          "jahs_bench_201_fashion_v005",
          "fcnet_naval_propulsion_v005", "fcnet_parkinsons_telemonitoring_v005", "fcnet_protein_structure_v005",
          "fcnet_slice_localization_v005"]
MF_EXCLUDED = {"nas_bench_201", "nas_bench_201_v005"}  # mf-track.md: NB201 outside the MF track (single fidelity)

CHILD = r"""
import json, sys, time, traceback, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts")
import run_experiment as re
kind, space, budget, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
t0 = time.time()
rec = {"method": kind, "space": space, "budget": budget}
try:
    r = re.run_single(re.load_method_config(kind), re.load_yaml(re.CONFIGS_DIR / "search_spaces" / f"{space}.yaml"), budget, 1)
    d = re._diagnostics(r)
    info = d.get("v005", {})
    rec.update(status="ok", evaluations_used=r.state.evaluations_used, history=len(r.state.history),
               cost_used=d.get("cost_used"), stop_reason=info.get("stop_reason"),
               resources={k: v for k, v in r.resources.items() if isinstance(v, (int, float, str)) or v is None})
except Exception:
    rec.update(status="error", error=traceback.format_exc()[-3000:])
rec["seconds"] = time.time() - t0
open(out, "w").write(json.dumps(rec))
"""


def verdict(rec: dict, mf: bool) -> str:
    if rec["status"] != "ok":
        return rec["status"].upper()
    b = rec["budget"]
    if mf:
        cost = rec.get("cost_used") or 0.0
        ok = 0 < cost <= b + 1e-9 and rec["history"] == rec["evaluations_used"]
        return "PASS" if ok else "FAIL"
    if rec["evaluations_used"] == b:
        return "PASS"
    reason = str(rec.get("stop_reason") or "")
    return "PASS-COLLAPSE" if "collapse" in reason or "exhausted" in reason else "FAIL"


def run_one(kind: str, space: str, budget: int, out_dir: Path, timeout: int) -> dict:
    out = out_dir / f"{kind}__{space}__b{budget}.json"
    if out.exists():
        rec = json.loads(out.read_text())
    else:
        t0 = time.time()
        try:
            subprocess.run([sys.executable, "-c", CHILD, kind, space, str(budget), str(out)], cwd=ROOT,
                           timeout=timeout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            rec = json.loads(out.read_text()) if out.exists() else {
                "method": kind, "space": space, "budget": budget, "status": "error", "error": "no result file"}
        except subprocess.TimeoutExpired:
            rec = {"method": kind, "space": space, "budget": budget, "status": "timeout", "seconds": time.time() - t0}
            out.write_text(json.dumps(rec))
    rec["verdict"] = verdict(rec, V005_METHODS[kind][2])
    print(f"{rec['verdict']:<14} {kind:<20} {space:<32} b={budget:<4} {rec.get('seconds', 0):8.1f}s", flush=True)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/level3_v005")
    ap.add_argument("--budgets", type=int, nargs="+", default=[50, 350])
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--jahs-workers", type=int, default=1)
    ap.add_argument("--methods", nargs="*", default=list(V005_METHODS))
    ap.add_argument("--spaces", nargs="*", default=SPACES)
    a = ap.parse_args()
    out_dir = ROOT / a.out
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(m, s, b) for s in a.spaces for m in a.methods for b in a.budgets
            if not (V005_METHODS[m][2] and s in MF_EXCLUDED)]
    jahs = [j for j in jobs if j[1].startswith("jahs")]
    rest = [j for j in jobs if not j[1].startswith("jahs")]
    with ThreadPoolExecutor(a.workers) as ex, ThreadPoolExecutor(a.jahs_workers) as exj:
        futs = [ex.submit(run_one, *j, out_dir, a.timeout) for j in rest]
        futs += [exj.submit(run_one, *j, out_dir, a.timeout) for j in jahs]
        recs = [f.result() for f in futs]
    summary = {}
    for r in recs:
        summary[r["verdict"]] = summary.get(r["verdict"], 0) + 1
    (out_dir / "summary.json").write_text(json.dumps({"counts": summary, "runs": recs}, indent=1))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
