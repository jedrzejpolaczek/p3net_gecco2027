"""experiments.methods -- the eight baselines/ablations P3Net is compared
against (everything in Table tab:ablation-grid except P3Net itself, which
is p3net.methods.p3net from the library)."""

from methods.external import mo_bohb_method, tpe_method
from methods.nsga_net import NSGANet
from methods.nsganetv2 import NSGANetV2
from methods.p3_absolute import P3Absolute
from methods.p3_alone import P3Alone
from methods.random_search import RandomSearch
from methods.sh_emoa import SHEMOA

__all__ = [
    "NSGANet",
    "NSGANetV2",
    "P3Absolute",
    "P3Alone",
    "RandomSearch",
    "SHEMOA",
    "mo_bohb_method",
    "tpe_method",
]
