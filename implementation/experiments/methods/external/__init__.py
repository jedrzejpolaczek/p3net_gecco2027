"""
Thin wrappers around established external baseline implementations -- not
reimplementations. Only for algorithms complex enough that reimplementing
them from scratch would risk an unfair comparison (a subtly wrong
reimplementation making a baseline look weaker or stronger than it really
is). Random search does not meet that bar and lives directly in
experiments/methods/random_search.py instead, as a small own
implementation.

TODO:
- Re-export sh_emoa, mo_bohb, tpe entry points once implemented.

Reference: chapters/v003/related_work/main.tex ("A systematic comparison of
solvers on this setting [guerreroviu2021bagofbaselines]...").
"""
