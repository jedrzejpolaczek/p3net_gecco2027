"""NB201 (cifar10-valid) validation accuracy after 12 epochs for every architecture --
the reward of the NAS-Bench-201 reference REINFORCE / R-EA (`train_and_eval`,
hp="12"), deterministic (is_random=False: mean over the trial seeds). Used by the
level-2 tests of REINFORCE and RegEvo (v005-level2-criteria.md).

  python scripts/build_nb201_valid12_table.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "cache" / "nats_bench"
OUT = ROOT / "results" / "benchmark_tables" / "nb201_valid12_cifar10valid.json"


def main() -> None:
    from nats_bench import create

    api = create(str(DATA), "tss", fast_mode=True, verbose=False)
    table = {}
    for i in range(len(api)):
        info = api.get_more_info(i, "cifar10-valid", hp="12", is_random=False)
        table[api.meta_archs[i]] = float(info["valid-accuracy"])
        if i % 1000 == 0:
            print(i, flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"metadata": {"dataset": "cifar10-valid", "hp": "12", "metric": "valid-accuracy",
                                            "is_random": False, "n": len(table)}, "accuracy": table}))
    print("written", OUT, len(table))


if __name__ == "__main__":
    main()
