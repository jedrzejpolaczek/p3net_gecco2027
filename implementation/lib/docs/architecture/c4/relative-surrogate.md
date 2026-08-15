# C4 — Relative Linkage-Aware Surrogate (δ̂_F)

`RelativeLinkageAwareSurrogate` predicts `f1(x) - f1(x')` for a pair that
differs only within a linkage subset `F`, trained on pairwise differences
drawn from `H_t`. It is P3Net's own contribution, distinct from the
`AbsoluteRegressorSurrogate` used by the NSGANetV2-style baselines.

```mermaid
classDiagram
  class RelativeLinkageAwareSurrogate {
    +model_factory: Callable
    -_model
    -_vocab: list~dict~
    -_fitted_subsets: set~frozenset~
    +fit(observations, subsets, objective_index) None
    +predict(x, x_prime, subset) float
  }

  class NoLinkageTreeError {
    <<exception>>
  }

  class _encoding {
    <<module, shared with AbsoluteRegressorSurrogate>>
    +build_vocab(observations) list~dict~
    +one_hot(genotype, vocab) list~float~
  }

  class telescoping {
    <<module>>
    +telescoped_estimate(ancestor, chain, surrogate, known_evaluated) float
    +ChainStep
  }

  class AncestorNotEvaluatedError {
    <<exception>>
  }

  RelativeLinkageAwareSurrogate --> _encoding : one_hot(x) + one_hot(x_prime), concatenated
  RelativeLinkageAwareSurrogate ..> NoLinkageTreeError : raised by fit()/predict() before a linkage tree exists
  telescoping --> RelativeLinkageAwareSurrogate : predict() per chain step
  telescoping ..> AncestorNotEvaluatedError : raised if x0 is not in H_t
```

## Training data construction

`fit(observations, subsets)` builds training pairs `(a, b)` from every
*ordered* pair of observations whose differing coordinates are a subset of
one of the given linkage subsets (`_matching_subset`) — i.e. pairs that
differ *only* within one `F`, as the paper requires ("restricted to the
one linkage subset that was modified"). The target is
`a.objectives[i] - b.objectives[i]`.

## A real bug found and fixed here during implementation

The first version encoded each training pair as a **diff mask**: `1.0`
where a coordinate differs between `x` and `x'`, `0.0` otherwise. This
seemed reasonable but is wrong: the mask for `x → x'` and `x' → x` is
*identical* (the same coordinates differ either way), while their targets
are opposite in sign (`+Δ` vs `-Δ`). A linear model fit on a constant
feature with an alternating-sign target collapses to predicting the mean —
which is exactly what `tests/test_relative_surrogate.py::test_trains_on_pairwise_diffs_restricted_to_subset`
caught (`predicted_delta == 0.0` instead of the expected `-10.0`).

**Fix**: encode both endpoints' actual values (one-hot each, concatenate),
not just which coordinates changed:

```python
def _pair_features(x, x_prime, vocab):
    return one_hot(x, vocab) + one_hot(x_prime, vocab)
```

This is now shared, alongside `AbsoluteRegressorSurrogate`'s identical
one-hot-vocabulary logic, in `surrogates/_encoding.py` — extracted after
the maintainability audit found the same `build_vocab`/`one_hot` code
duplicated verbatim in both surrogate files.

## A real performance issue found and fixed here during implementation

`fit()`'s pairwise loop calls `_pair_features` (equivalently: `one_hot`)
once per *pair* in `H_t`, but the number of distinct genotypes only grows
linearly while the number of pairs grows quadratically — the same
genotype gets re-encoded from scratch every time it reappears in a new
pair. `cProfile` on the 200-budget integration test (2026-08-15) found
this was the single largest cost in a full run: `one_hot` called ~5.4M
times, ~77% of `fit()`'s own profiled cost. Fixed by encoding each
distinct genotype once per `fit()` call into a local cache, then building
every pair's feature vector from that cache instead of re-encoding
(`RelativeLinkageAwareSurrogate.fit()`, not shown in the `_pair_features`
snippet above — `predict()` still calls `_pair_features` directly, since
it only ever scores one pair at a time and has no cache to benefit from).
Pure caching change: same fitted model, same predictions, verified by the
full test suite staying green unchanged. Cut the 200-budget integration
test's wall time from 116.53s to 65.55s.

## Telescoping reconstruction

`telescoped_estimate` reduces a chain of tentatively-accepted modifications
back to the nearest fully-evaluated ancestor:

```
f_hat_1(x_m) = f1(x_0) - sum_i delta_hat_{F_i}(x_{i-1}, x_i)
```

`ancestor` (`x_0`) is checked against `known_evaluated` (the current
`H_t`) and rejected with `AncestorNotEvaluatedError` if it isn't a real,
fully-evaluated genotype — the hard invariant the paper requires ("the
telescoping construction therefore never bottoms out on a surrogate
estimate"). In `methods.p3net.P3Net`, this exception is caught narrowly
(not via a blanket `except Exception`) and logged at `WARNING` level if it
ever fires, since — given the invariant is enforced by construction
elsewhere in `P3Net` — its firing would itself indicate a real bug, not an
expected condition.
