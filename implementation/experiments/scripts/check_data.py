"""Check that every benchmark this project uses really answers queries here.

Runs one real query per benchmark against the substrate the experiments use,
so a new machine fails in seconds rather than hours into a pipeline run:
present files, readable format, correct environment (for JAHS-Bench-201, the
separate Python 3.10 bridge as well).

Prints one line per benchmark and returns a non-zero exit code if any failed.

Usage (from implementation/experiments):
    uv run python scripts/check_data.py
    uv run python scripts/check_data.py --skip jahs_bench_201   # skip the slow one
"""

from __future__ import annotations

import argparse
import random
import sys
import time
import traceback
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from scripts import run_experiment  # noqa: E402

#: One search space per benchmark family (the others share its data).
SPACES = {
    "nas_hpo_bench_ii": "nas_hpo_bench_ii",
    "nats_bench": "nas_bench_201",
    "fcnet": "fcnet_protein_structure",
    # Slowest: the bridge loads several GB of surrogate models on first query.
    "jahs_bench_201": "jahs_bench_201",
}


def check(space_name: str) -> tuple[bool, str]:
    space_config = run_experiment.load_search_space_config(space_name)
    search_space, _ = run_experiment.build_search_space(space_config)
    substrate = run_experiment.build_substrate(space_config)
    started = time.perf_counter()
    try:
        genotype = search_space.sample_uniform(random.Random(0))
        objectives = substrate.objectives(genotype)
        seconds = time.perf_counter() - started
        return True, f"f1={objectives[0]:.4g} f2={objectives[1]:.4g} in {seconds:.1f}s"
    except Exception as exc:  # noqa: BLE001 -- reported, not hidden
        return False, f"{exc.__class__.__name__}: {exc}"
    finally:
        close = getattr(substrate, "close", None)
        if callable(close):
            close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip", nargs="*", default=[], choices=sorted(SPACES))
    parser.add_argument("--traceback", action="store_true", help="print full tracebacks")
    args = parser.parse_args(argv)

    failed = 0
    for name, space_name in SPACES.items():
        if name in args.skip:
            print(f"SKIP {name}")
            continue
        try:
            ok, detail = check(space_name)
        except Exception:  # noqa: BLE001 -- building the substrate itself can fail
            ok, detail = False, traceback.format_exc(limit=1).strip().splitlines()[-1]
            if args.traceback:
                traceback.print_exc()
        print(f"{'OK  ' if ok else 'FAIL'} {name:18} {detail}", flush=True)
        failed += 0 if ok else 1
    print("all benchmarks answer queries" if not failed else f"{failed} benchmark(s) unusable")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
