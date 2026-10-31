"""All analyses of notes/plans/v005-preregistration.md (§3-§5) from the v005 run roots.

    uv run python scripts/analyze_v005.py results/runs/<commit> results/runs/<commit>-vizier \
        --out results/runs/<commit>/analysis

Before the run, once: `--build-references` (K1 oracle fronts, K2 JAHS bounds; benchmark tables only).
Outputs (one CSV each): per_run, missing, q_tests (Q1, Q2, Q4, Q5), q3_tost, anytime, cost_to_target,
costs, hv_decomposition, hv_sensitivity, regret_generalisation, q7_elympus, budget_use; plus
summary.md (counts and where each file comes from). The posthoc surrogate decision quality (§5.4, K8)
is scripts/posthoc_metrics.py; retraining (§5.8, K10) is separate.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
if str(EXPERIMENTS_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS_ROOT))

from analysis_v005 import fronts, per_run, secondary, spec, tests  # noqa: E402

PLANS = [EXPERIMENTS_ROOT / "configs" / "pipeline" / "v005.yaml",
         EXPERIMENTS_ROOT / "configs" / "pipeline" / "v005-vizier.yaml"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("roots", nargs="*", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--build-references", action="store_true")
    ap.add_argument("--skip-anytime", action="store_true", help="skip §5.1-5.2 (the slow part)")
    args = ap.parse_args(argv)

    if args.build_references:
        print(fronts.build_jahs_bounds())
        for s in spec.ORACLE_SPACES:
            print(fronts.build_oracle(s))
        if not args.roots:
            return 0
    if not args.roots or args.out is None:
        ap.error("run roots and --out are required")
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    log, t0 = [], time.time()

    def save(name, df):
        df.to_csv(out / f"{name}.csv", index=False)
        log.append(f"| {name}.csv | {len(df)} | {time.time() - t0:.0f} s |")
        print(f"{name}: {len(df)} rows ({time.time() - t0:.0f} s)", flush=True)

    df = per_run.per_run(args.roots)
    save("per_run", df)
    save("missing", per_run.missing(df, per_run.expected_points(PLANS)))
    save("duplicates", per_run.duplicates(df))
    save("q_tests", tests.family_tests(df))
    save("q3_tost", tests.tost(df))
    if not args.skip_anytime:
        curves, targets = secondary.anytime_and_targets(args.roots, df)
        save("anytime", curves)
        save("cost_to_target", targets)
    save("costs", secondary.costs(df))
    save("hv_decomposition", secondary.hv_decomposition(args.roots, df))
    save("hv_sensitivity", secondary.hv_sensitivity(args.roots))
    save("regret_generalisation", secondary.regret_and_generalisation(args.roots))
    save("q7_elympus", secondary.q7(df))
    save("budget_use", secondary.budget_use(df))
    (out / "summary.md").write_text(
        "# v005 analysis outputs\n\nRun roots: " + ", ".join(map(str, args.roots))
        + "\n\nPre-registration: notes/plans/v005-preregistration.md\n\n| file | rows | elapsed |\n|---|---|---|\n"
        + "\n".join(log) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
