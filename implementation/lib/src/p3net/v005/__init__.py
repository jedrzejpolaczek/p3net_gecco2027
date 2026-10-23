"""v005: source-faithful reimplementation of P3Net, its variants and the baselines.

Every module follows a source card in `notes/plans/v005-sources/*.md`; public
signatures are fixed by `notes/plans/v005-interfaces.md` (version 2, §7 wins on
conflict). Genotypes are tuples of value indices 0..k_i-1 wrapped in
`p3net.problem.genotype.Genotype`. Objectives are minimised.

The v004 code elsewhere in `p3net` is kept for comparisons and is not imported here.
"""
