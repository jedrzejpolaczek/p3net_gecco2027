"""
Regression gate before re-running the design-variant round: the default
`p3net` config must reproduce its already-persisted raw runs exactly.

The design-decision ablation flags (truncation, stall_recovery, donor_pool,
cascade, use_analytic_cost) were restored into P3Net / build_method on
2026-09-13 with defaults intended to equal the single retained behaviour.
If that intent is wrong anywhere -- an extra RNG draw, a changed iteration
order -- every headline number for P3Net would silently stop matching its
own code. Both benchmarks are deterministic and runs are seeded, so the
check is strict: the full evaluated history must be identical, point for
point, not just statistically similar.

Writes nothing to results/raw/. Exits 1 on any mismatch.

Usage (PowerShell, from implementation/experiments):
    uv run python scripts/verify_p3net_unchanged.py
    uv run python scripts/verify_p3net_unchanged.py --search-spaces nas_hpo_bench_ii --seeds 1 2 3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

import yaml  # noqa: E402

from scripts.run_experiment import _observation_to_dict, build_substrate, run_single  # noqa: E402

RAW_DIR = EXPERIMENTS_ROOT / "results" / "raw"
CONFIGS = EXPERIMENTS_ROOT / "configs"


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--search-spaces",
        nargs="+",
        default=["nas_hpo_bench_ii", "jahs_bench_201"],
        help="configs/search_spaces/<name>.yaml stems",
    )
    parser.add_argument("--budgets", nargs="+", type=int, default=[50, 100])
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 2, 3])
    args = parser.parse_args(argv)

    method_config = _load_yaml(CONFIGS / "methods" / "p3net.yaml")
    failures = 0
    checked = 0
    for space in args.search_spaces:
        space_config = _load_yaml(CONFIGS / "search_spaces" / f"{space}.yaml")
        substrate = build_substrate(space_config)
        try:
            for budget in args.budgets:
                for seed in args.seeds:
                    stored_path = RAW_DIR / f"p3net__{space}__budget{budget}__seed{seed}.json"
                    if not stored_path.exists():
                        print(f"SKIP  {stored_path.name} (no stored run)")
                        continue
                    stored = json.loads(stored_path.read_text(encoding="utf-8"))["history"]
                    result = run_single(method_config, space_config, budget, seed, substrate=substrate)
                    # Round-trip through the exact serialiser run_experiment.py
                    # persists with, so the comparison is on the stored
                    # representation rather than on in-memory types.
                    fresh = json.loads(
                        json.dumps([_observation_to_dict(obs) for obs in result.state.history])
                    )
                    stored_norm = stored
                    checked += 1
                    if fresh == stored_norm:
                        print(f"OK    {stored_path.name} ({len(fresh)} evaluations identical)")
                    else:
                        failures += 1
                        first = next(
                            (i for i, (a, b) in enumerate(zip(fresh, stored_norm)) if a != b),
                            min(len(fresh), len(stored_norm)),
                        )
                        print(
                            f"FAIL  {stored_path.name}: first divergence at evaluation {first} "
                            f"(fresh {len(fresh)} vs stored {len(stored_norm)})"
                        )
        finally:
            close = getattr(substrate, "close", None)
            if callable(close):
                close()

    print(f"\n{checked} run(s) checked, {failures} mismatch(es)")
    if failures or not checked:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
