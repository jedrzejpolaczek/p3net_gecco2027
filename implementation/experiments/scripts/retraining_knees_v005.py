"""K10 step 1 (pre-registration §5.8): pick the knee point to retrain for every arm on NAS-Bench-201 and
NAS-HPO-Bench-II, from the finished v005 run roots. Reads records only; no benchmark queries, no GPU.

Rules (§5.8, decision 2026-11-16 in notes/archive/v005/plans/v005-todo.md):
  * budget: the arm's largest budget -- 350; GP arms (Vizier, qNEHVI, qParEGO) 100;
  * median run: the arm's 30 runs in the cell sorted by the primary metric (IGD+, then seed); the run at
    index (n - 1) // 2 (for n = 30 the better of the two middle runs);
  * final front: non-dominated set of the run's full-fidelity points (MF arms: configurations trained to
    full length), objectives normalised to the oracle front's [ideal, nadir] range, as in IGD+;
  * knee: the front point farthest from the line through the front's two extremes; a front of one point
    is its own knee; with two points (both at distance 0) the one with lower f1;
  * genotype: the first evaluation in the run's history with the knee's objectives.

    uv run python scripts/retraining_knees_v005.py results/runs/c674c91e results/runs/c674c91e-vizier \
        --out results/retraining/knees_v005.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from analysis_v005 import fronts, spec  # noqa: E402
from analysis_v005.metrics import IGDPlus  # noqa: E402
from analysis_v005.per_run import points, records  # noqa: E402

SPACES = ("nas_bench_201_v005", "nas_hpo_bench_ii_v005")
ELYMPUS = "v005_p3_elympus"


def arms(space: str) -> list[str]:
    """Main track (P3Net, Q1, Q2) + eLyMPuS; MF track only on NAS-HPO-II (no MF track on NB201)."""
    out = [spec.REF, *spec.Q1, *spec.Q2, ELYMPUS]
    return out + (list(spec.Q4) if space == "nas_hpo_bench_ii_v005" else [])


def budget_for(method: str) -> int:
    return 100 if method in spec.GP else max(spec.BUDGETS)


def knee(front_norm: np.ndarray) -> int:
    """Index of the knee in a front sorted by f1 (normalised objectives)."""
    if len(front_norm) <= 2:
        return 0
    a, b = front_norm[0], front_norm[-1]
    d = b - a
    norm = float(np.hypot(*d))
    if norm == 0.0:
        return 0
    dist = np.abs(d[0] * (front_norm[:, 1] - a[1]) - d[1] * (front_norm[:, 0] - a[0])) / norm
    return int(np.argmax(dist))


def pick(runs: list[dict], igd: IGDPlus) -> dict:
    scored = sorted(((igd(points(r)), r["seed"], r) for r in runs), key=lambda t: (t[0], t[1]))
    value, seed, rec = scored[(len(scored) - 1) // 2]
    front = fronts.nondominated(points(rec))
    norm = (np.asarray(front, float) - igd.lo) / igd.span
    k = front[knee(norm)]
    entry = next(h for h in rec["history"] if tuple(map(float, h["objectives"])) == k)
    return dict(method=rec["method"], search_space=rec["search_space"], budget=rec["budget"], seed=seed,
                n_runs=len(runs), median_run_igd_plus=value, front_size=len(front),
                genotype=entry["genotype"], benchmark_f1=k[0], benchmark_f2=k[1],
                **training_spec(rec["search_space"], entry["genotype"]), record=Path(rec["_path"]).name)


def training_spec(space: str, genotype: list) -> dict:
    """What scripts/retrain_v005.py needs, so that it imports nothing from this project:
    the xautodl arch string (NAS-HPO-II: its cellcode digits 0-3 are nor_conv_3x3, avg_pool_3x3,
    skip_connect, none -- the same names), and for NAS-HPO-II the learning rate and batch size.
    `train_key` identifies one training job; arms with the same genotype share it."""
    from search_spaces.nas_bench_201_genotype import genotype_to_arch_str
    from search_spaces.nas_hpo_bench_ii_genotype import genotype_to_cellcode

    arch = genotype_to_arch_str(tuple(genotype[:6]))
    if space == "nas_hpo_bench_ii_v005":
        lr, bs = float(genotype[6]), int(genotype[7])
        return dict(arch_str=arch, cellcode=genotype_to_cellcode(tuple(genotype[:6])), learning_rate=lr,
                    batch_size=bs, train_key=f"nhb__{genotype_to_cellcode(tuple(genotype[:6])).replace('|', '-')}"
                                             f"__lr{lr}__bs{bs}")
    return dict(arch_str=arch, train_key="nb201__" + "-".join(
        op.replace("nor_conv_", "c").replace("avg_pool_3x3", "ap").replace("skip_connect", "id")
        for op in genotype[:6]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="+", type=Path)
    ap.add_argument("--out", type=Path, default=EXPERIMENTS_ROOT / "results" / "retraining" / "knees_v005.json")
    args = ap.parse_args(argv)

    wanted = {(m, s, budget_for(m)) for s in SPACES for m in arms(s)}
    cells: dict[tuple[str, str, int], list[dict]] = {k: [] for k in wanted}
    for rec in records(args.roots):
        key = (rec["method"], rec["search_space"], rec["budget"])
        if key in cells:
            rec.pop("evaluation_metrics", None)
            rec.pop("diagnostics", None)
            cells[key].append(rec)

    igd = {s: IGDPlus(fronts.load_oracle(s)) for s in SPACES}
    knees, problems = [], []
    for key in sorted(cells):
        runs = cells[key]
        if len(runs) != len(spec.SEEDS):
            problems.append(f"{key}: {len(runs)} runs, expected {len(spec.SEEDS)}")
        if runs:
            knees.append(pick(runs, igd[key[1]]))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"rules": __doc__.split("Rules", 1)[1].split("    uv run", 1)[0].strip(),
                                    "roots": [str(r) for r in args.roots], "problems": problems,
                                    "knees": knees}, indent=1), encoding="utf-8")
    for s in SPACES:
        print(f"{s}: {sum(k['search_space'] == s for k in knees)} knee point(s)")
    for p in problems:
        print("PROBLEM", p)
    print(f"-> {args.out}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
