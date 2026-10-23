"""BM-3 outcome (results/checks/bm3_jahs_size_vs_hp_cifar10.md): JAHS-Bench-201's
`size_MB` varies with the hyperparameters for a fixed cell, so f2 on JAHS becomes
the parameter count computed from the cell.

Network: the NAS-Bench-201 cell network that JAHS-Bench-201 trains, at the frozen
N = 5, W = 16 (decision #31), built with xautodl `infer.tiny`. Activation,
learning rate, weight decay, TrivialAugment and Resolution add no parameters; the
number of classes changes only the classifier, so one table per task.

Runs in vendor/energy-env/.venv (has torch + xautodl):

    vendor/energy-env/.venv/Scripts/python.exe scripts/build_jahs_param_counts.py \
        --out results/benchmark_tables/jahs_param_counts.json
"""

from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

from xautodl.models import get_cell_based_tiny_net

OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3", "avg_pool_3x3")
N_CLASSES = {"cifar10": 10, "colorectal_histology": 8, "fashion_mnist": 10}


class _Dict(dict):
    __getattr__ = dict.get


def arch_str(ops: tuple[int, ...]) -> str:
    o = [OPS[i] for i in ops]
    return f"|{o[0]}~0|+|{o[1]}~0|{o[2]}~1|+|{o[3]}~0|{o[4]}~1|{o[5]}~2|"


def n_params(ops: tuple[int, ...], n_classes: int) -> int:
    cfg = {"name": "infer.tiny", "C": 16, "N": 5, "arch_str": arch_str(ops), "num_classes": n_classes}
    net = get_cell_based_tiny_net(_Dict(cfg))
    return sum(p.numel() for p in net.parameters())


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    args = p.parse_args()
    table: dict[str, dict[str, int]] = {}
    for ops in itertools.product(range(len(OPS)), repeat=6):
        base = n_params(ops, 10)
        head_10 = 64 * 10 + 10  # classifier of the C=16, N=5 network: 64 features -> classes
        table[arch_str(ops)] = {
            task: base - head_10 + (64 * k + k) for task, k in N_CLASSES.items()
        }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"network": "xautodl infer.tiny C=16 N=5", "ops": OPS, "params": table}, indent=0))
    print(f"{len(table)} cells -> {out}")


if __name__ == "__main__":
    main()
