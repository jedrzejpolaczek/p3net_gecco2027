"""NB201 f2 table from HW-NAS-Bench (benchmarks.md BM-2, decision P1 a, 2026-10-31):
`edgegpu_energy` (Jetson TX2, TensorRT, batch 1, CIFAR-10, mJ per image) for all
15 625 cells, keyed by arch string, with an index check against NATS-Bench.

The pickle comes from `scripts/download_data.py --only hw_nas_bench` (SHA-256 verified).

    uv run python scripts/build_nb201_energy_table.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from p3net.v005.benchmarks import DEFAULT_TABLE, build_energy_table_hwnasbench  # noqa: E402
from scripts.download_data import HWNASBENCH_FILE  # noqa: E402
from substrates.nas_bench_201 import DEFAULT_DATA_DIR  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pickle", type=Path, default=HWNASBENCH_FILE)
    parser.add_argument("--out", type=Path, default=DEFAULT_TABLE)
    parser.add_argument("--nats-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)

    from nats_bench import create

    api = create(str(args.nats_dir), "tss", fast_mode=True, verbose=False)
    payload = build_energy_table_hwnasbench(args.pickle, args.out, nats_index=api.query_index_by_arch)
    meta = payload["metadata"]
    print(f"{meta['n_cells']} cells, index mismatches vs NATS: {meta['index_mismatches_vs_nats']} -> {args.out}")
    return 0 if meta["n_cells"] == 15625 and meta["index_mismatches_vs_nats"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
