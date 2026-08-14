"""
p3net.methods -- the P3Net algorithm itself.

Only p3net.py lives here. Every baseline and ablation used to evaluate
P3Net against alternatives (NSGA-Net, NSGANetV2, P3-alone, P3+absolute
regressor, SH-EMOA, MO-BOHB, random search, TPE) is specific to the paper's
comparison and lives in experiments/methods/ instead, built by combining
this library's search_engines/surrogates with experiments-only components
(experiments/search_engines/nsga2/, experiments/methods/external/).

TODO:
- Re-export P3Net's entry point once methods/p3net.py is implemented.

Reference: chapters/v003/proposed_optimizer/main.tex (P3Net as a whole).
"""
