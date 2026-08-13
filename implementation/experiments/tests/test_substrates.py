"""
TODO:
- Test JAHS-Bench-201 adapter fixes f2 at the r_K resolution setting
  regardless of the fidelity level f1 is queried at.
- Test NAS-HPO-Bench-II adapter never queries the benchmark's 200-epoch
  surrogate extrapolation -- only its tabulated <=12-epoch range.
- Test both adapters expose whether they answer deterministically (both
  should, here: s = 1).

Reference: experiments/substrates/*; chapters/v003/related_work/main.tex
("Classifying NAS-HPO-Bench-II as Category 1...").
"""
