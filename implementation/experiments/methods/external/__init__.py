"""Thin wrappers around established external baseline implementations --
not reimplementations. Only for algorithms complex enough that
reimplementing them from scratch would risk an unfair comparison. Random
search does not meet that bar and lives directly in
methods/random_search.py instead."""

from methods.external._ask_tell_shared import AskTellMethod, default_valid_sampler
from methods.external.mo_bohb import mo_bohb_method
from methods.external.sh_emoa import sh_emoa_method
from methods.external.tpe import tpe_method

__all__ = [
    "AskTellMethod",
    "default_valid_sampler",
    "mo_bohb_method",
    "sh_emoa_method",
    "tpe_method",
]
