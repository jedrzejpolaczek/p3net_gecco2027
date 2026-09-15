"""
Faithfulness gate for the Design Evolution stages.

Each early stage of P3Net (S1, S2) is now a configuration of the CURRENT
codebase rather than the code that originally produced its results. That is
only legitimate if the configuration really reproduces the original engine.
Both benchmarks are deterministic and every run is seeded, so the test is
strict: re-running the stage config must reproduce the archived raw runs
point for point -- same genotypes, same objectives, same order.

A mismatch means the stage flags do not capture the old engine exactly, and
the stage must not be reported as "the original P3Net" until it is resolved.

Usage (from implementation/experiments):
    uv run python scripts/verify_stage_reproduces_archive.py \
        --method p3net_s1_initial \
        --archive results/archive/p3net-pre-analytic-cost_2026-08-17 \
        --archived-method p3net
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from scripts.run_experiment import (  # noqa: E402
    _observation_to_dict,
    build_substrate,
    load_method_config,
    load_search_space_config,
    run_single,
)


def _find_archived(archive: Path, name: str) -> Path | None:
    for candidate in (archive / name, archive / "raw" / name):
        if candidate.exists():
            return candidate
    return None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--method", required=True, help="stage config to run (configs/methods/<name>.yaml)"
    )
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--archived-method", default="p3net", help="method name used in the archived filenames"
    )
    parser.add_argument(
        "--search-spaces", nargs="+", default=["nas_hpo_bench_ii", "jahs_bench_201"]
    )
    parser.add_argument("--budgets", nargs="+", type=int, default=[50, 100])
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    args = parser.parse_args(argv)

    archive = args.archive if args.archive.is_absolute() else EXPERIMENTS_ROOT / args.archive
    method_config = load_method_config(args.method)
    checked = failures = 0
    for space in args.search_spaces:
        space_config = load_search_space_config(space)
        substrate = build_substrate(space_config)
        try:
            for budget in args.budgets:
                for seed in args.seeds:
                    name = f"{args.archived_method}__{space}__budget{budget}__seed{seed}.json"
                    stored_path = _find_archived(archive, name)
                    if stored_path is None:
                        print(f"SKIP  {name} (not in archive)")
                        continue
                    stored = json.loads(stored_path.read_text(encoding="utf-8"))["history"]
                    result = run_single(
                        method_config, space_config, budget, seed, substrate=substrate
                    )
                    fresh = json.loads(
                        json.dumps([_observation_to_dict(o) for o in result.state.history])
                    )
                    checked += 1
                    if fresh == stored:
                        print(f"OK    {name} ({len(fresh)} evaluations identical)")
                        continue
                    failures += 1
                    first = next(
                        (i for i, (a, b) in enumerate(zip(fresh, stored)) if a != b),
                        min(len(fresh), len(stored)),
                    )
                    print(
                        f"FAIL  {name}: first divergence at evaluation {first} (fresh {len(fresh)}, archived {len(stored)})"  # noqa: E501
                    )
        finally:
            close = getattr(substrate, "close", None)
            if callable(close):
                close()

    print(f"\n{args.method} vs {archive.name}: {checked} run(s) checked, {failures} mismatch(es)")
    if failures or not checked:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
