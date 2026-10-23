"""BM-3 (notes/plans/v005-sources/benchmarks.md): does JAHS-Bench-201's
`size_MB` change with the hyperparameters when the cell is fixed?

Decision rule, fixed before running: if the spread of `size_MB` over the HP
combinations of every sampled cell is below 1e-6 MB, f2 stays `size_MB`;
otherwise f2 becomes the parameter count computed analytically from the cell.

Runs in the JAHS environment (vendor/jahsbench-env/.venv), without the query
server. Loading one dataset needs about 12 GB of RAM.

    vendor/jahsbench-env/.venv/Scripts/python.exe scripts/check_jahs_size_vs_hp.py \
        --data-dir data/cache/jahs_bench_201 --task cifar10
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

import jahs_bench
from jahs_bench.lib.core.constants import OP_NAMES

N_EDGES = 6
# The grids of search_spaces/nas_genotype.py (decision #31): LR 8 log points over
# [1e-3, 1], WD 6 log points over [1e-5, 1e-2].
LR_GRID = tuple(math.exp(math.log(1e-3) + i * (math.log(1.0) - math.log(1e-3)) / 7) for i in range(8))
WD_GRID = tuple(math.exp(math.log(1e-5) + i * (math.log(1e-2) - math.log(1e-5)) / 5) for i in range(6))
ACTIVATIONS = ("ReLU", "Hardswish", "Mish")
THRESHOLD_MB = 1e-6


def config(ops: tuple[int, ...], lr: float, wd: float, act: str, ta: bool) -> dict:
    # N, W, Resolution frozen at their maxima, as in the query server (#31).
    cfg = {"Optimizer": "SGD", "N": 5, "W": 16, "Resolution": 1.0}
    for i, op in enumerate(ops, start=1):
        cfg[f"Op{i}"] = op
    cfg.update(LearningRate=lr, WeightDecay=wd, Activation=act, TrivialAugment=ta)
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--task", default="cifar10")
    parser.add_argument("--cells", type=int, default=200)
    parser.add_argument("--hp-per-cell", type=int, default=10)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", default="results/checks")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    t0 = time.time()
    bench = jahs_bench.Benchmark(task=args.task, download=False, save_dir=args.data_dir)
    load_s = time.time() - t0

    cells = []
    for _ in range(args.cells):
        ops = tuple(rng.randrange(len(OP_NAMES)) for _ in range(N_EDGES))
        sizes = []
        for _ in range(args.hp_per_cell):
            cfg = config(ops, rng.choice(LR_GRID), rng.choice(WD_GRID), rng.choice(ACTIVATIONS), rng.random() < 0.5)
            sizes.append(float(bench(cfg, nepochs=200)[200]["size_MB"]))
        cells.append({"ops": ops, "sizes": sizes, "spread": max(sizes) - min(sizes)})

    spreads = sorted(c["spread"] for c in cells)
    max_spread = spreads[-1]
    n_varying = sum(s >= THRESHOLD_MB for s in spreads)
    rel = [c["spread"] / (sum(c["sizes"]) / len(c["sizes"])) for c in cells if min(c["sizes"]) > 0]
    verdict = "size_MB stays (constant per cell)" if max_spread < THRESHOLD_MB else "analytic parameter count (size_MB varies with HP)"

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"bm3_jahs_size_vs_hp_{args.task}"
    (out / f"{stem}.json").write_text(json.dumps({"args": vars(args), "cells": cells}, indent=1))
    lines = [
        f"# BM-3: JAHS `size_MB` vs hyperparameters ({args.task})",
        "",
        f"- cells: {args.cells}, HP combinations per cell: {args.hp_per_cell}, seed {args.seed}, nepochs 200",
        f"- benchmark load time: {load_s:.0f} s",
        f"- cells whose `size_MB` spread >= {THRESHOLD_MB} MB: {n_varying} / {args.cells}",
        f"- max spread: {max_spread:.6g} MB; median spread: {spreads[len(spreads) // 2]:.6g} MB",
        f"- max relative spread (spread / mean): {max(rel) if rel else float('nan'):.4g}",
        "",
        f"**Verdict (rule fixed in benchmarks.md before the run): {verdict}.**",
        "",
        f"Raw data: `{stem}.json`.",
    ]
    (out / f"{stem}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
