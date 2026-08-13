"""
TODO:
- Test the concrete NAS SearchSpace instantiation (six architecture edges +
  discretised Theta) produces a valid p3net.problem.SearchSpace / Genotype.
- Test Theta discretisation (e.g. log-spaced learning-rate grid) is fixed
  once and stable.
- Test the concrete Decoder D decodes a genotype to a network description
  consumable by experiments/substrates/.
- Test the concrete Validity g correctly flags structurally invalid
  genotypes (e.g. no input-output path).
- Test the continuous-Theta variant (for nsganetv2_continuous.yaml) is a
  genuinely separate encoding from the shared discretised one, not a thin
  wrapper that silently discretises anyway.

Reference: experiments/search_spaces/nas_genotype.py;
chapters/v003/problem_formulation/main.tex; chapters/v003/notes/main.tex
("Encoding in baselines").
"""
