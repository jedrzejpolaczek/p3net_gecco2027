"""experiments.methods -- the eight baselines/ablations P3Net is compared
against (everything in Table tab:ablation-grid except P3Net itself, which
is p3net.methods.p3net from the library)."""

from methods.external import (
    MOEAD,
    botorch_method,
    mo_bohb_method,
    nsga3_method,
    smac_parego_method,
    tpe_method,
    vizier_method,
)
from methods.mo_ls import MOLocalSearch
from methods.nsga_net import NSGANet
from methods.nsganetv2 import NSGANetV2
from methods.p3_absolute import P3Absolute
from methods.p3_alone import P3Alone
from methods.random_search import RandomSearch
from methods.regularized_evolution_mo import RegularizedEvolutionMO
from methods.sh_emoa import SHEMOA

__all__ = [
    "MOEAD",
    "MOLocalSearch",
    "RegularizedEvolutionMO",
    "botorch_method",
    "nsga3_method",
    "smac_parego_method",
    "vizier_method",
    "NSGANet",
    "NSGANetV2",
    "P3Absolute",
    "P3Alone",
    "RandomSearch",
    "SHEMOA",
    "mo_bohb_method",
    "tpe_method",
]
