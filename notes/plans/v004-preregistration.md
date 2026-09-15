# P3Net v0.0.4 — pre-registered analysis plan

Status: fixed before any run of `configs/pipeline/v004.yaml` (phase 4). Recorded at the commit that
contains this file; the pipeline manifest records that commit for every result. Anything computed
later that is not described here is reported as exploratory and labelled as such.

## 1. Questions

No pass/fail thresholds are set. Every result below is reported in full, whatever its direction.

- **Q1 (comparison).** How does the final P3Net (S5, `p3net_cascade`) compare with each joint NAS+HPO
  comparison arm, per search space and budget?
- **Q2 (design path).** How does quality change along the design stages S1 → S2 → S3 → S4 → S5, and in
  the dead-end stage S4′?
- **Q3 (design defence).** How does each single-axis variant and each κ × threshold cell compare with
  S5?
- **Q4 (surrogate).** How do the surrogate variants (absolute linear, absolute random forest, and the
  forest with plain FIHC or FIHC-eLyMPuS refinement) compare with S5, and how accurate are the
  surrogate decisions?
- **Q5 (generalisation).** Does the comparison on FCNet agree with the one on the NAS-Bench-201 cell
  space?
- **Q6 (practical cost).** What does each arm cost in wall-clock time, CPU time, optimiser overhead,
  memory and simulated training time, and how much cost does it need to reach a given quality?
- **Q7 (multi-fidelity).** At equal cost in full-evaluation equivalents, how do Hyperband, ASHA and BOHB
  compare with S5?

## 2. Seeds: exploratory vs confirmatory

- Seeds 1–30 were used, directly or through earlier versions of the same grid, while the design was
  developed. All results on them are **exploratory**.
- Seeds 31–60 (stage `s6_heldout_seeds`) were never used for any design decision. Q1, Q4 and Q7 on the
  four primary spaces are **confirmatory** on these seeds. Design-stage and design-defence arms are not
  re-run on them.
- If exploratory and confirmatory results disagree, both are reported side by side.

## 3. Metrics

Each run's result is the set of configurations it evaluated at full fidelity (for the multi-fidelity
arms: the configurations trained to full length).

| Search spaces | Primary metric | Direction |
|---|---|---|
| NAS-HPO-Bench-II, FCNet (4 tasks) | IGD+ against the exact oracle front, objectives normalised to the oracle front's range | lower is better |
| JAHS-Bench-201 (3 datasets) | hypervolume relative to a frozen best-known front | higher is better |
| NAS-Bench-201 | same as JAHS (descriptive only, §6) | higher is better |

Frozen best-known fronts (JAHS-Bench-201, NAS-Bench-201) are built **once**, from the non-dominated set
of all points evaluated by the stages `s1_headline`, `s3_final` and `s7_multi_fidelity` on seeds 1–30,
together with the nadir reference point from the same points. They are frozen before the held-out
results are read and are not rebuilt afterwards, so adding or removing an arm never changes another
arm's value.

## 4. Statistical protocol

- **Unit:** one cell = (search space, budget).
- **Reference arm:** `p3net_cascade` for Q1, Q3, Q4 and Q7. For Q2, each stage is compared with the
  stage before it.
- **Test:** two-sided Mann–Whitney U on the per-seed metric values (30 values per arm).
  - Runs of different arms with the same seed number are not paired: they share no common random
    numbers.
  - This replaces the paired Wilcoxon signed-rank test in the v0.0.3 reporting code
    (`stats/significance.py`), which is to be changed in phase 5 before any v0.0.4 number is produced.
- **Multiple comparisons:** Holm–Bonferroni within each cell, over that cell's comparisons with the
  reference arm; α = 0.05.
  - Families: Q1 = the comparison arms in the cell. Q3 = the 16 design-defence arms. Q4 = the 4
    surrogate variants. Q7 = the 3 multi-fidelity arms.
  - Q2 = one family per cell over the stage transitions S1→S2, S2→S3, S3→S4, S4→S4′ and S4→S5.
- **Effect size:** Cliff's δ with every test, oriented so that positive favours the reference arm.
- **Summaries:** medians and IQR per cell. Counts such as "significant in k of 16 cells" are
  descriptive, and are always given with the number of cells in each direction.
- **No aggregation** of p-values across cells or budgets.
- **Missing runs:** a run that fails `max_retries` times is reported as missing, with its error; no run
  is excluded for being an outlier.

## 5. Secondary analyses (descriptive, no tests)

- **Anytime quality:** the metric after every evaluation (every 1/100 of budget for the multi-fidelity
  arms); median curves per arm.
- **Cost to target:** simulated training time and number of evaluations until an arm first reaches 90%,
  95% and 99% of the best median final quality in the cell.
- **Practical cost (Q6)** comes only from the sequential timing stage `s9_timing` (budget 350, seed 1,
  one run per process): wall-clock time, CPU time, optimiser overhead (wall-clock minus benchmark
  query time), peak memory, GPU memory and simulated training time.
  - The JAHS-Bench-201 bridge's loading time in the first query is reported separately.
  - Money and energy are derived from these numbers under explicitly stated assumptions (hourly
    price; device power).
- **Surrogate decision quality (Q4):** from the logged decisions of seeds 1–30, labelled after the run
  outside the budget (`scripts/posthoc_metrics.py`).
  - Pooled per arm × search space × budget and per decision source (mixing, refinement, gate,
    predictor): TP, FP, TN, FN, precision, recall, F1, FPR, FNR, MCC, balanced accuracy, Spearman's ρ,
    Kendall's τ-b, calibration in 10 equal-count bins.
- **Generalisation gaps:** test-set metric of each arm's final front, plus train–validation and
  validation–test gaps of its members (where the benchmark records them).
- **Regret:** simple regret of f1 against the best f1 in the oracle front, or in the frozen best-known
  front.
- **Retraining (phase 4b):** for each arm × primary space, the knee point of the median run's final
  front is retrained once on the GPU. The retrained accuracy is compared with the benchmark's value,
  descriptively.

## 6. What is not a comparison

- **NAS-Bench-201** (`s5_nas_bench_201`) is architecture-only. It is used only to diagnose P3Net and to
  reproduce Bartnik; its results are descriptive and are not part of any family in §4 (plan decision
  D6).
- **Q5 (FCNet)** repeats the Q1 protocol on the four FCNet tasks. It is reported in its own block, and
  its agreement with Q1 is described rather than tested.

## 7. Deviations

Any change to this plan after phase 4 starts is recorded here with the date and the reason, and the
affected results are marked in the paper.
