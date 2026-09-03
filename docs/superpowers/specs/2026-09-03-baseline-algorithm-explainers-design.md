# Design: Baseline algorithm explainer pages (PL)

## Goal

`implementation/lib/docs/explanations/pl/` currently explains P3 (`p3.html`) and
P3Net (`p3net.html`) as long-form, fully interactive single-file HTML essays.
The GECCO 2027 paper's nine-arm ablation grid compares P3Net against six other
methods (see `implementation/lib/README.md`): **Random search, TPE, MO-BOHB,
SH-EMOA, NSGA-Net, NSGANetV2**. None of those have an explainer yet. This spec
covers writing one matching page per algorithm, in the same series.

## Shared template (all six pages)

Each page is a standalone, self-contained `.html` file (no shared JS/CSS
files — copy the P3/P3Net scaffold, same fonts, same CSS custom-property
structure, same light/dark theme handling) with the same six sections and nav
pattern as `p3.html`:

1. **Kontekst** — what the algorithm is, one sentence on where it sits in the
   optimization landscape, and (new vs. P3/P3Net pages) a short note on its
   role as one arm of the nine-arm ablation grid against P3Net.
2. **Ogólny obraz** — the algorithm as one loop/diagram, comparable in spirit
   to how `p3.html` section 2 draws GA-vs-P3 as two loops side by side.
3. **Komponenty** — the algorithm broken into its constituent procedures.
4. **Zobacz na żywo** — a bespoke interactive step/run demo of the actual
   mechanism (see table below — this is NOT a reskin of the P3 demo; each
   algorithm gets a demo built around what it actually computes).
5. **Pseudokod** — the algorithm written out, same style as `p3.html` §5.
6. **Co wymyślasz sam** — closing "ustalone przez algorytm" vs. "ty
   decydujesz" table, plus a short closing paragraph naming the specific
   blind spot of this algorithm that P3Net's design (linkage-aware relative
   surrogate, parameter-less pyramid) targets — mirroring how `p3.html`
   closes by pointing at P3Net.

Visual identity: reuse the exact CSS variable structure from `p3.html`, only
retuning `--accent` (and matching soft/line variants) per page so the series
reads as one family while each page is visually distinguishable. No shared
external stylesheet/script — each file stays fully self-contained, consistent
with the existing two pages.

## Per-algorithm content outline

| Algorithm | Core idea (sections 1-3) | Live demo (section 4) | Closing link to P3Net |
|---|---|---|---|
| **Random search** | No structure, no memory of history; every sample is independent of all prior ones | Sample points in a toy search space live, plot best-so-far curve; explicitly show it never builds a model or reuses linkage info | P3Net's blind spot it exposes: is structure/learning paying for itself at all? |
| **TPE** | Split observed evaluations into good/bad by a quantile `γ`, fit density estimates `l(x)` (good) and `g(x)` (bad), sample the next point maximizing `l(x)/g(x)` | Step-by-step: points accumulate, split into two clouds at the quantile line, two density curves are drawn, next candidate sampled from their ratio | Sequential single-objective model over raw configs vs. P3Net's structural (linkage-tree) model over genotype dependencies |
| **MO-BOHB** | Hyperband-style budget brackets (successive halving across fidelities) with TPE-based sampling for the multi-objective case | A budget bracket: many cheap configs enter, waves of promotion at each fidelity rung, survivors get the next larger budget | Fidelity-driven pruning vs. P3Net's relative, linkage-aware surrogate — different way of cutting evaluation cost |
| **SH-EMOA** | Standard EMOA population loop (non-dominated sorting + crowding) with successive-halving fidelity cuts folded into each generation | Population + Pareto fronts evolving across generations, with a visible low-fidelity elimination wave before survivors get full evaluation | Combines evolution with budget-cutting but no linkage learning — mutation/crossover stay naive vs. P3Net's tree-guided crossover |
| **NSGA-Net** | NSGA-II (non-dominated sorting, crowding distance) applied directly to architecture genotypes, every candidate fully trained | Pareto front advancing generation over generation; explicit trained-cost counter climbing with population size | No population-size-free growth, no surrogate — pure full-fidelity multi-objective evolution; contrast with P3's pyramid growth and P3Net's surrogate |
| **NSGANetV2** | Same NSGA-II loop as NSGA-Net, but real training is replaced by a cheap predictor/weight-sharing supernet query | Same loop as NSGA-Net demo, but with a highlighted swap point where "real evaluation" becomes "predictor query," and a cost counter that barely moves | Predictor-based surrogate that is *not* linkage-aware or relative — direct contrast with what makes P3Net's surrogate different |

## Non-goals

- No shared/linked index page across the seven explainer pages (none exists
  today either — each page is standalone, matching current convention).
- No changes to `p3.html`/`p3net.html` themselves beyond using them as the
  structural/CSS template to copy from.
- No claim of matching the paper's actual experimental numbers — these are
  conceptual explainers, same spirit as the existing two pages, not a results
  report.

## Execution plan

Six independent, same-shaped files with no shared state between them — build
via one subagent per page in parallel, each hard-briefed with: this spec's
shared template, its row from the per-algorithm table, and `p3.html` as the
concrete style/structure reference to copy from (CSS scaffold, section
numbering, nav pattern, tone of the Polish prose).
