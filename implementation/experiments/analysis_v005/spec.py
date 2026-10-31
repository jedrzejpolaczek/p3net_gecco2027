"""What the v005 pre-registration fixes (notes/plans/v005-preregistration.md §1-§6). Nothing here is
read from the results."""

from __future__ import annotations

REF = "v005_p3net"

#: Q1 comparison arms (17; decision R1 a)
Q1 = ["v005_mo_dsa", "v005_mo_psa", "v005_nsga_net", "v005_nsganetv2", "v005_reinforce", "v005_regevo", "v005_mo_ls",
      "v005_shemoa", "v005_mobananas", "v005_motpe", "v005_nsga3", "v005_smac3_parego", "v005_vizier", "v005_qnehvi",
      "v005_qparego", "v005_moead", "v005_random_search"]
#: Q2 what the surrogate contributes (decision R1 a); also the Q3 TOST pairs (decision R6)
Q2 = ["v005_p3_canonical", "v005_p3net_gate", "v005_p3net_nolink"]
#: Q4 multi-fidelity track
Q4 = ["v005_hyperband", "v005_asha", "v005_shemoa_mf", "v005_mosh_bananas", "v005_mo_bohb"]
#: Q7 (supplement, descriptive): P3-eLyMPuS vs canonical P3
Q7 = ("v005_p3_elympus", "v005_p3_canonical")
GP = {"v005_vizier", "v005_qnehvi", "v005_qparego"}

BUDGETS = (50, 100, 200, 350)
SEEDS = tuple(range(62, 92))  # decision R3 b
POSTHOC_JAHS_SEEDS = tuple(range(62, 72))  # decision R8 b (10 seeds)

#: space -> (group, metric, max epochs, JAHS task)
SPACES = {
    "jahs_bench_201_v005": ("primary", "hv", 200, "cifar10"),
    "jahs_bench_201_colorectal_v005": ("primary", "hv", 200, "colorectal_histology"),
    "jahs_bench_201_fashion_v005": ("primary", "hv", 200, "fashion_mnist"),
    "nas_hpo_bench_ii_v005": ("primary", "igd", 12, None),
    "fcnet_protein_structure_v005": ("fcnet", "igd", 100, None),
    "fcnet_naval_propulsion_v005": ("fcnet", "igd", 100, None),
    "fcnet_parkinsons_telemonitoring_v005": ("fcnet", "igd", 100, None),
    "fcnet_slice_localization_v005": ("fcnet", "igd", 100, None),
    "nas_bench_201_v005": ("nb201", "igd", 200, None),
}
ORACLE_SPACES = [s for s, v in SPACES.items() if v[1] == "igd"]
JAHS_SPACES = [s for s, v in SPACES.items() if v[1] == "hv"]

#: JAHS HV (decision R5 b1): reference point in the bound-normalised space, HV divided by r^2
HV_REF = 1.1
HV_SENSITIVITY_REFS = (1.05, 1.2)  # decision R5'

#: TOST (decision 2026-10-31): 90 % bootstrap CI of Cliff's delta
TOST_MARGINS = (0.33, 0.147)  # first = the one used in sentences of the paper
TOST_RESAMPLES = 4000
TOST_SEED = 20261031

#: cost to target (§5.2): fractions of the best median final quality in the cell
TARGETS = (0.90, 0.95, 0.99)
#: anytime curves of MF arms: every 1/100 of the cost budget (§5.1)
MF_GRID = 100

#: surrogate decision quality (§5.4): methods with logged surrogate decisions
SURROGATE_METHODS = ["v005_p3net", "v005_p3net_gate", "v005_p3net_nolink", "v005_mo_dsa", "v005_mo_psa",
                     "v005_nsganetv2"]

ALPHA = 0.05


def families() -> list[tuple[str, list[str], str]]:
    """(name, arms compared with REF, space group). Q5 = Q1 arms on FCNet."""
    return [("Q1", Q1, "primary"), ("Q2", Q2, "primary"), ("Q4", Q4, "primary"), ("Q5", Q1, "fcnet")]


def better_sign(metric: str) -> float:
    """+1 if larger is better (HV), -1 if smaller is better (IGD+)."""
    return 1.0 if metric == "hv" else -1.0
