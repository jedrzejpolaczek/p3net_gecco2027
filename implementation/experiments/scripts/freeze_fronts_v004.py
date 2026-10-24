"""A6 (audit): freeze the v004 best-known fronts and HV reference points exactly as the v004
preregistration §3 defines them, before the held-out seeds 31-60 are read:

- JAHS-Bench-201 (3 datasets): all points of stages s1_headline, s3_final and
  s7_multi_fidelity on seeds 1-30 -- from the main run root and from the GP run root
  (deviation 7: the GP arms of s1, budgets 50/100);
- NAS-Bench-201: all points of stage s5_nas_bench_201 on seeds 1-30 (deviation 3);
- reference point = nadir of the same points.

Writes results/reference_fronts/<space>.json (oracle fronts untouched) and
results/tables/reference_front_provenance.md (front size, pooled points, source runs,
run-set digest, reference point).

  python scripts/freeze_fronts_v004.py --run-root results/runs/b4d25cac --gp-root results/runs/gp-small
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from reporting._common import load_raw_run  # noqa: E402
from reporting.reference_fronts import describe_fronts, freeze_fronts, save_fronts  # noqa: E402
from scripts import run_pipeline as rp  # noqa: E402

JAHS_STAGES = ("s1_headline", "s3_final", "s7_multi_fidelity")
NB201_STAGE = "s5_nas_bench_201"
SEEDS = range(1, 31)


def stage_keys(plan_path: Path, stages: tuple[str, ...]) -> set[tuple[str, str, int, int]]:
    plan = rp.load_plan(plan_path)
    keys = set()
    for st in plan["stages"]:
        if st["name"] in stages and st.get("kind", "grid") == "grid":
            keys |= {(p.method, p.search_space, p.budget, p.seed) for p in rp.expand_stage(st) if p.seed in SEEDS}
    return keys


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", type=Path, required=True)
    ap.add_argument("--gp-root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, default=ROOT / "results" / "reference_fronts")
    ap.add_argument("--tables-dir", type=Path, default=ROOT / "results" / "tables")
    a = ap.parse_args()
    plans = ROOT / "configs" / "pipeline"
    want_jahs = stage_keys(plans / "v004.yaml", JAHS_STAGES) | stage_keys(plans / "v004-gp-small.yaml", JAHS_STAGES)
    want_nb = stage_keys(plans / "v004.yaml", (NB201_STAGE,))
    # read only the files of the wanted points (the run roots hold ~52 000 files)
    chosen, missing = [], []
    for m, s, b, seed in sorted(k for k in want_jahs | want_nb
                                if k[1].startswith("jahs") and k in want_jahs or k[1].startswith("nas_bench_201")):
        name = f"{m}__{s}__budget{b}__seed{seed}.json"
        path = next((r / "raw" / name for r in (a.run_root, a.gp_root) if (r / "raw" / name).exists()), None)
        if path is None:
            missing.append(name)
        else:
            chosen.append(load_raw_run(path))
    print(f"loaded {len(chosen)} runs; missing {len(missing)}: {missing[:10]}")
    frozen = freeze_fronts(chosen)
    for path in save_fronts(frozen, a.out_dir):
        print("wrote", path)
    a.tables_dir.mkdir(parents=True, exist_ok=True)
    table = a.tables_dir / "reference_front_provenance.md"
    table.write_text("# v004 frozen best-known fronts (preregistration §3; deviations 3 and 7)\n\n"
                     f"Sources: {a.run_root.name} stages {', '.join(JAHS_STAGES)} (JAHS) and {NB201_STAGE} (NB201), "
                     f"{a.gp_root.name} (GP arms), seeds 1-30 only.\n\n" + describe_fronts(frozen), encoding="utf-8")
    print(table.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
