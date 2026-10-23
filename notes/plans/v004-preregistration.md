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

Recorded on 2026-10-16, after the v004 run finished and the three analysis passes
(`notes/analysis-v004/reports/01–03`) were complete. Deviations 1 and 2 were known earlier (dates
given); the others were found during the analysis. None of them was used to choose what to report.

| # | Deviation from this plan | Found | Reason | Effect on results | How it is handled |
|---|---|---|---|---|---|
| 1 | The three Gaussian-process arms (`oss_vizier`, `botorch_qnehvi`, `botorch_qparego`) were run only at budgets 50 and 100, in a separate run root (`results/runs/gp-small`, plan `configs/pipeline/v004-gp-small.yaml`, commit 1bba34af) | 2026-09-21 (Vizier out of memory at budget 350), 2026-09-25 (BoTorch timings), decided 2026-10-05 | Measured cost on the 30 GB machine: Vizier ~34 GB resident at budget 350; qNEHVI 8 419 s and 12 GB per run at 350; qParEGO 3 192 s per run at 350. The single-GPU slot serialises both BoTorch arms, so qNEHVI at 350 alone would take ~35 calendar days | Q1 Holm families have 24 arms at budgets 50/100 and 21 at 200/350; no GP result above budget 100; method code identical to the main run root | GP arms reported in a separate table for budgets 50/100; the missing columns are stated in Limitations |
| 2 | The repository's reporting code (`implementation/experiments/stats/significance.py`) still computes the paired Wilcoxon signed-rank test, not the two-sided Mann–Whitney U required by §4 | before phase 4 (audit checklist A1, 2026-10-07); not fixed before the run | Planned for phase 5, not done yet | No v004 number has been produced with it; the analysis reports use Mann–Whitney U from separate scripts | Fix the reporting code (and its tests and captions) before any v004/v005 number enters the paper |
| 3 | The NAS-Bench-201 frozen front cannot be built "from s1, s3 and s7" (§3): NAS-Bench-201 is run only in s5 | 2026-10-16 | Plan error: §3 did not anticipate that the descriptive benchmark has its own stage | Front built from all s5 runs on seeds 1–30 (15 points). The benchmark's exact oracle front (15 625 architectures) was not used | NB201 stays descriptive (§6); the front source is stated with the results |
| 4 | Knee-point retraining on the GPU (§5, phase 4b) was not done | 2026-10-16 | No training code matching each benchmark was prepared; the task had no owner date or script | No retrained accuracies | Reported as missing; planned as an explicitly partial retraining in the next pre-registration |
| 5 | Surrogate decision quality (§5) and generalisation gaps were not computed: `scripts/posthoc_metrics.py` was never run | 2026-10-16 | No checklist tied each §5 analysis to a script and an output file | No labelled decision metrics or test-set fronts in the repository | Partial exploratory substitute in report 02 (§4.3, §4.5) for the tabular spaces only; JAHS-Bench-201 not labelled |
| 6 | The sequential timing stage s9 did not record bridge memory (`bridge_peak_rss_mb`) or GPU memory (`gpu_peak_memory_mb`); the JAHS-Bench-201 bridge loading time is not reported separately (§5) | 2026-10-16 | Fields empty in every s9 record; no post-run check of the resource fields | Process memory on JAHS-Bench-201 excludes the ~12 GB bridge; no GPU figures | Stated in the cost table; resource fields to be asserted non-empty in the next run |
| 7 | The JAHS-Bench-201 frozen fronts include points of the GP arms from `gp-small` (seeds 1–30, budgets 50/100) | 2026-10-16 | Consistent with the letter of §3 (they are s1 arms), recorded because they come from a separate run root | Changes the HV denominator for every arm equally | Stated with the front definition |

**Status of v004 after the implementation audit (2026-10-16).** Report 01 found that several
implementations differ from their sources or from the paper's description: P3Net's linkage subsets
include the root (so the surrogate's subset restriction is inactive), SMAC3 runs only its initial design
at budgets ≤ 100, MOEA/D stops before the budget on FCNet, and the Bartnik reconstruction and several
baselines are simplified. The author decided to correct the implementations, verify them against their
sources, and rerun under a new pre-registration (v005) with new confirmatory seeds. v004 results are
therefore kept as the record of this pre-registration, but are not the main results of the paper; they
are cited only as exploratory evidence that motivated the corrections.
