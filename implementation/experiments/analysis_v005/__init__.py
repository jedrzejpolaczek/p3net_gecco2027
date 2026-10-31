"""v005 analysis code: everything notes/plans/v005-preregistration.md promises, one module per part.

spec       -- arms, families, spaces and metric of each space, exactly as pre-registered
fronts     -- K1 oracle fronts of the v005 objectives, K2 JAHS bounds (built once, before the run)
metrics    -- normalised HV (JAHS) and IGD+ (oracle spaces)
per_run    -- K3 one row per run: metric, budget use, duplicates, surrogate share, resources
tests      -- K4 Mann-Whitney U + Holm + Cliff's delta per family and cell; K5 TOST
secondary  -- K6 anytime and cost to target, K7 costs, K9 HV decomposition and sensitivity, regret,
              generalisation gaps, Q7 (eLyMPuS) medians

CLI: scripts/analyze_v005.py.
"""
