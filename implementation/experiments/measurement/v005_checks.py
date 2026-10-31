"""Level 4 (v005-verification-protocol.md §3): checks evaluated on every v005 run, stored
in the run's diagnostics under "level4" (`run_experiment.run_single`). Each check is
{"ok": bool | None, "detail": ...}; None = not applicable to this method.

- budget (K-2): never more evaluations (main track) / cost (MF track) than the budget.
- stop: a run that ended before its budget names its reason (#36: exploration collapse,
  search space exhausted, budget exhausted in the MF track, algorithm finished).
- initial_design (BB-4): the initial design is at most floor(0.25 b) (Bartnik's warm-up,
  B-2 a, is 0.2 b).
- f2_source (#6): the method saw f2 only through real evaluations -- no call of the
  substrate's analytic f2 during the run (`analytic_cost_queries == 0`).
- surrogate_share (P3Net, S-6): mixing steps answered by the surrogate are < 100 % and
  > 0 % of all mixing steps (one real evaluation per level, D-3 b); n/a when there are no
  more mixing steps than levels (P3 (2b), 2026-10-31).
- resources (A8): the resource fields of the run are present.
"""

from __future__ import annotations

from typing import Any

#: method kind -> the config() key holding its initial design size (BB-4 table and
#: library-adapters.md §3); methods not listed have no initial design in the BB-4 sense.
INITIAL_DESIGN_KEY = {
    "v005_mo_dsa": "warmup", "v005_mo_psa": "warmup", "v005_nsganetv2": "n_doe",
    "v005_shemoa": "population_size", "v005_mobananas": "initial_samples", "v005_motpe": "n_startup_trials",
    "v005_smac3_parego": "initial_design_size", "v005_qnehvi": "n_initial", "v005_qparego": "n_initial",
    "v005_mo_bohb": "num_initial_samples", "v005_mosh_bananas": "initial_samples", "v005_shemoa_mf": "population",
}
P3NET_SURROGATE = {"v005_p3net", "v005_p3net_nolink"}
RESOURCE_FIELDS = ("wall_seconds", "cpu_seconds", "process_peak_rss_mb")


def level4_checks(*, kind: str, budget: int, evaluations_used: int, cost_used: float | None, multi_fidelity: bool,
                  info: dict[str, Any], resources: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    spent = cost_used if multi_fidelity else evaluations_used
    out["budget"] = {"ok": spent is not None and spent <= budget + 1e-9, "detail": {"spent": spent, "budget": budget}}

    reason = info.get("stop_reason")
    early = (spent or 0) < budget - (1.0 if multi_fidelity else 0.0)
    out["stop"] = {"ok": (not early) or bool(reason), "detail": {"early": early, "reason": reason}}

    key = INITIAL_DESIGN_KEY.get(kind)
    cfg = info.get("config") if isinstance(info.get("config"), dict) else {}
    if key is None:
        out["initial_design"] = {"ok": None, "detail": "no initial design (BB-4 n/a)"}
    else:
        n = cfg.get(key)
        out["initial_design"] = {"ok": isinstance(n, (int, float)) and n <= budget // 4,
                                 "detail": {"key": key, "size": n, "limit": budget // 4}}

    q = resources.get("analytic_cost_queries")
    out["f2_source"] = {"ok": q == 0, "detail": {"analytic_cost_queries": q}}

    if kind in P3NET_SURROGATE:
        ev = info.get("events", {})
        steps, levels = ev.get("cluster_step_changed", 0), ev.get("level_mix", 0)
        # n/a when no mixing step goes beyond the mandatory real one per level (D-3 b): no step
        # at all (FIHC of the first solution used the whole budget), or as few steps as levels
        # (A8, b = 100: one step, real by definition -> share 0 is not a failure)
        share = None if steps <= levels else 1.0 - levels / steps
        out["surrogate_share"] = {"ok": None if share is None else 0.0 < share < 1.0,
                                  "detail": {"mixing_steps": steps, "real_per_level": levels, "surrogate_share": share}}
    else:
        out["surrogate_share"] = {"ok": None, "detail": "n/a"}

    missing = [f for f in RESOURCE_FIELDS if resources.get(f) is None]
    out["resources"] = {"ok": not missing, "detail": {"missing": missing}}
    return out


def all_ok(checks: dict[str, dict[str, Any]]) -> bool:
    return all(c["ok"] is not False for c in checks.values())
