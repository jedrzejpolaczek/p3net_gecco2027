"""Real wrappers around external baseline implementations -- MO-BOHB
(hpbandster), TPE and NSGA-III (optuna), qNEHVI and qParEGO (BoTorch),
SMAC3 with ParEGO, MOEA/D (pymoo), and OSS Vizier's default designer.
SH-EMOA and random search don't live here: random search is too simple to
carry reimplementation risk (methods/random_search.py); no published SH-EMOA
package exists to wrap (methods/sh_emoa.py, a real from-scratch
implementation instead)."""

from methods.external._ask_tell_shared import AskTellMethod
from methods.external.botorch_mo import botorch_method
from methods.external.mo_bohb import mo_bohb_method
from methods.external.moead import MOEAD
from methods.external.nsga3 import nsga3_method
from methods.external.smac_parego import smac_parego_method
from methods.external.tpe import tpe_method
from methods.external.vizier_mo import vizier_method

__all__ = [
    "MOEAD",
    "AskTellMethod",
    "botorch_method",
    "mo_bohb_method",
    "nsga3_method",
    "smac_parego_method",
    "tpe_method",
    "vizier_method",
]
