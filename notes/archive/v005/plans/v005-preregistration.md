# P3Net v0.0.5 — pre-registered analysis plan

**Status: treść zatwierdzona przez autora 2026-10-31.** Wersja obowiązująca = stan tego pliku w commicie, z którego startuje
przebieg v005 (manifest pipeline'u zapisuje ten commit przy każdym wyniku). Zmiany przed startem (np. wynikłe z pisania
skryptów analiz) — z datą w tym nagłówku.

## Decyzje autora (2026-10-31) i sprawy otwarte

Rozstrzygnięte (`v005-todo.md`, decyzje 2026-10-31): R1 a, R2 a, R3 b, R4 a, R6 (3 pary), R7 a, R8 b, R9 a.
R5 = b1 (punkt (1.1, 1.1), HV / 1.21). R5′: analiza wrażliwości HV (§5.6a). Posthoc JAHS: 10 seedów (62–71). Zamrożenie dopiero po skryptach analiz (decyzja P8; poz. 5a w `v005-todo.md`).

## 1. Questions

No pass/fail thresholds are set. Every result below is reported in full, whatever its direction.

- **Q1 (comparison).** How does P3Net (`v005_p3net`) compare with each joint NAS+HPO comparison arm of the main track,
  per search space and budget? Comparison arms: MO-DSA, MO-PSA (Bartnik), NSGA-Net, NSGANetV2, REINFORCE, RegEvo, MO-LS,
  SH-EMOA, MO-BANANAS, MOTPE, NSGA-III, SMAC3-ParEGO, OSS Vizier, qNEHVI, qParEGO, MOEA/D, random search.
- **Q2 (what the surrogate contributes).** How does P3Net compare with (a) canonical P3 with real evaluations only
  (`v005_p3_canonical`), (b) P3Net-gate (same surrogate, quantile acceptance gate instead of replacement, D-3 a),
  (c) P3Net-nolink (pair model without linkage-tree features, S-2 c)?
- **Q3 (equivalence).** For the three Q2 pairs: is the difference smaller than a pre-set margin (TOST, §4)?
- **Q4 (multi-fidelity track).** At equal cost in full-evaluation equivalents, how do Hyperband, ASHA, SH-EMOA (MF),
  MOSH-BANANAS and MO-BOHB compare with P3Net?
- **Q5 (generalisation).** Does the Q1 comparison on FCNet (4 tasks) agree with the one on the primary spaces?
- **Q6 (practical cost).** What does each arm cost in wall-clock time, optimiser overhead, memory and simulated training
  time, and how much cost does it need to reach a given quality?
- **Q7 (eLyMPuS, supplement).** How does P3-eLyMPuS compare with canonical P3? Descriptive (plan A7).

## 2. Seeds

- All v005 results use seeds **62–91**, never used for any design decision in v004 or v005 (plan A1). All Q1–Q5 tests
  are **confirmatory** on these seeds.
- Seed 61 was run in the resource measurement A8 (2026-10-24…29, `v005-a8-analysis.md`; time and memory only, quality not
  analysed). It is replaced by seed 91 so that no confirmatory seed has been run before (author's decision R3 b,
  2026-10-31). After A8 the level-4 check `surrogate_share` was changed to return "not applicable" when there are no
  more mixing steps than levels (false failure at b = 100) — a check, not a method.
- v004 results (seeds 1–60) are exploratory and are cited only as the motivation for the corrections.

## 3. Metrics

Each run's result is the set of configurations it evaluated at full fidelity (MF arms: those trained to full length).

| Search spaces | Objectives (card `benchmarks.md`) | Primary metric | Direction |
|---|---|---|---|
| NAS-HPO-Bench-II; FCNet (4 tasks) | f1 validation error / MSE; f2 training time | IGD+ against the exact oracle front, objectives normalised to the oracle front's range | lower is better |
| JAHS-Bench-201 (C10, CRC, FMN) | f1 = 100 − valid acc. (200 epochs); f2 = analytic parameter count (BM-3) | hypervolume with objectives normalised by the space bounds: f1 by [0, 100], f2 by [min, max] parameter count of the task's table; reference point (1.1, 1.1), HV divided by 1.21 so that HV ∈ [0, 1] (A12, decisions P4 and R5 b1; following the practice "space bounds plus a small margin", Bartnik 2026 §7.1.2; a point exactly at the bounds gives the extreme points of a front zero contribution) | higher is better |
| NAS-Bench-201 | f1 = validation error (`cifar10-valid`, mean over seeds); f2 = edge-GPU inference energy from HW-NAS-Bench (BM-2, decision P1 a) | IGD+ against the exact oracle front of the 15 625 cells, normalised to the oracle front's range | lower is better |

- Oracle fronts are rebuilt once for the v005 objectives (`scripts/build_oracle_front.py`) before the run and frozen.
  No front depends on the results of any arm.
- JAHS bounds are fixed before the run from the parameter-count table (`results/benchmark_tables/jahs_param_counts.json`).
  Points outside the bounds cannot occur (f1 ∈ [0, 100] by definition; f2 from the same table).
- "Closing the gap" on JAHS, descriptive: (HV_arm − HV_RS) / (HV_best − HV_RS) per cell, with HV_best the best median
  in the cell.

## 4. Statistical protocol

- **Unit:** one cell = (search space, budget); budgets 50, 100, 200, 350.
- **Primary spaces** (tests of Q1–Q4): JAHS-Bench-201 C10, CRC, FMN and NAS-HPO-Bench-II (decision R2 a). FCNet (4 tasks)
  is tested in its own block (Q5); NAS-Bench-201 is descriptive (§6).
- **Reference arm:** `v005_p3net` in Q1, Q2, Q4, Q5.
- **Test:** two-sided Mann–Whitney U on per-seed metric values (30 per arm); runs of different arms with the same
  seed number are not paired.
- **Multiple comparisons:** Holm–Bonferroni within each cell over that cell's comparisons with the reference arm,
  α = 0.05. Families: Q1 = the comparison arms present in the cell; Q2 = the three arms of Q2; Q4 = the five MF arms.
  - The GP arms (Vizier, qNEHVI, qParEGO) run only at budgets 50 and 100 (plan A8, decision P2 b), so Q1 families have
    17 arms at 50/100 and 14 at 200/350. Stated with every table.
- **Effect size:** Cliff's δ with every test, positive = better for P3Net.
- **Equivalence (Q3):** TOST via a 90 % bootstrap CI of Cliff's δ (4 000 resamples): **equivalent** if the CI lies within
  (−m, m); **different** if it excludes 0; otherwise **inconclusive**. Margin m = 0.33 ("small", Romano et al. 2006) is
  used in sentences of the paper; m = 0.147 ("negligible") is reported next to it (decision 2026-10-31).
- **Summaries:** median and IQR per cell. Counts such as "better in k of n cells" are descriptive and always given with
  the number of cells in each direction.
- **No aggregation** of p-values across cells or budgets.
- **Missing runs:** a run that fails `max_retries` times is reported as missing, with its error; no run is excluded as an
  outlier. A worker killed by the out-of-memory killer restarts from scratch and is not counted in `--max-retries`
  (A8); such restarts are logged and reported.

## 5. Secondary analyses (descriptive, no tests)

1. **Anytime quality:** primary metric after every evaluation (MF arms: every 1/100 of the cost budget); median curves.
2. **Cost to target:** evaluations and simulated training time until an arm first reaches 90 / 95 / 99 % of the best
   median final quality in the cell.
   For IGD+ (lower is better) "reaches q of the best" = IGD+ ≤ best / q (decided 2026-10-31).
3. **Practical cost (Q6):** from the run records of the grid (`resources`): optimiser wall-clock time (without benchmark
   queries), per-run process peak memory (`peak_memory_process_scope = "run"`), JAHS bridge memory (machine-level,
   shared by all workers), simulated training time. Times are measured with 6 workers sharing 16 vCPUs; Vizier runs
   alone in its own plan (`v005-vizier.yaml`). Money derived under a stated hourly price.
4. **Surrogate decision quality** (P3Net, P3Net-gate, P3Net-nolink, MO-DSA, MO-PSA, NSGANetV2): logged decisions labelled
   after the run outside the budget (`scripts/posthoc_metrics.py`) — confusion counts, precision, recall, MCC, balanced
   accuracy, Spearman ρ, Kendall τ-b, calibration in 10 bins. Tabular spaces (NHB, FCNet, NB201): all seeds; JAHS
   (each label needs a query to the JAHS surrogate): a subset of seeds (R8 b: seeds 62–71).
5. **Surrogate share:** fraction of mixing steps answered by the surrogate per run (level-4 field), per cell.
6. **HV decomposition (JAHS):** HV split at the median f2 of the cell's pooled front (cheap vs accurate end).
6a. **HV sensitivity (JAHS):** the primary HV recomputed with reference points (1.05, 1.05) and (1.2, 1.2) (normalised as
   in §3); medians per arm and cell and whether the order of arms changes; descriptive (decision R5′).
7. **Duplicates and budget use:** share of re-proposed solutions; `evaluations_used == budget` (main track).
8. **Retraining (A10, decision P5 a):** for each arm of the main and MF tracks on NAS-Bench-201 and NAS-HPO-Bench-II, the
   knee point of the median run's final front (run with the median primary metric; knee = point of the normalised front
   farthest from the line through its two extremes) is retrained **once** with the benchmark's public training protocol
   (NB201: 200 epochs, `cifar10-valid` split; NAS-HPO-II: 12 epochs) on a rented GPU. Retrained validation accuracy is
   compared with the benchmark's value, descriptively.
9. **Generalisation gaps:** test-set metric of each arm's final front (computed after the run; methods never see it):
   mean test f1 of the members of the run's final non-dominated set and mean (test − validation) gap of those members
   (decided 2026-10-31).
10. **Regret:** simple regret of f1 against the best f1 of the oracle front (tabular) or the best f1 seen in the cell
    (JAHS).

## 6. What is not a comparison

- **NAS-Bench-201** is architecture-only; its results are descriptive and are not in any Holm family (plan B2).
- **Q5 (FCNet)** repeats the Q1 protocol on the four FCNet tasks in its own block; agreement with Q1 is described.
- **Q7 (eLyMPuS)** is a supplement result.
- NB201 v005 is not comparable with v004 (f2 = FLOPs there, Spearman 0.55 with the energy).

## 7. Commitments: analysis → script → output → owner → date

Brak pliku wyniku w terminie = alarm i wpis do §8 w dniu wykrycia (protokół §6).

| # | Commitment | Script | Output | Owner | Due | Status |
|---|---|---|---|---|---|---|
| K1 | Oracle fronts for v005 objectives (NHB, FCNet ×4, NB201), through `substrate.objectives(g)` of the v005 configs | `analysis_v005/fronts.py` (`scripts/analyze_v005.py --build-references`) | `results/reference_fronts/oracle__*_v005.json` | Claude | before freeze | **done 2026-10-31**: NHB 25 points (188 496 valid; identical to v004 front), FCNet 21/24/15/28, NB201 30 (15 284 valid) |
| K2 | JAHS bounds (R5 b1) | `analysis_v005/fronts.py` | `results/reference_fronts/jahs_bounds_v005.json` | Claude | before freeze | **done 2026-10-31** |
| K3 | Per-run metrics (IGD+, HV), missing and duplicated grid points | `analysis_v005/per_run.py` | `analysis/per_run.csv`, `missing.csv`, `duplicates.csv` | Claude | before freeze | **done**, checked on A8 records |
| K4 | Q1, Q2, Q4, Q5 tests (MWU, Holm, δ) | `analysis_v005/tests.py` | `analysis/q_tests.csv` | Claude | before freeze | **done**, tested (`tests/test_analysis_v005.py`) |
| K5 | Q3 TOST | `analysis_v005/tests.py` | `analysis/q3_tost.csv` | Claude | before freeze | **done**, tested |
| K6 | §5.1–5.2 anytime, cost to target | `analysis_v005/secondary.py` | `analysis/anytime.csv`, `cost_to_target.csv` | Claude | before freeze | **done**, checked on A8 records |
| K7 | §5.3 cost table | `analysis_v005/secondary.py` | `analysis/costs.csv` | Claude | before freeze | **done** |
| K8 | §5.4 decision quality | `scripts/posthoc_metrics.py` | `results/runs/<root>/posthoc/` | autor uruchamia (serwer), Claude | ≤ 3 days after the run | exists, to check on v005 records |
| K9 | §5.6 HV decomposition, §5.6a HV sensitivity | `analysis_v005/secondary.py` | `analysis/hv_decomposition.csv`, `hv_sensitivity.csv` | Claude | before freeze | **done**, checked on A8 records |
| K9a | §5.5 surrogate share, §5.7 duplicates and budget use, level-4 failures | `analysis_v005/secondary.py` | `analysis/budget_use.csv` | Claude | before freeze | **done** (added 2026-10-31: promised in §5, had no row) |
| K9b | §5.9 generalisation gaps, §5.10 regret | `analysis_v005/secondary.py`; per-evaluation metrics written into each v005 run record (`evaluation_metrics`, `scripts/run_experiment.py`) | `analysis/regret_generalisation.csv` | Claude | before freeze | **done** (added 2026-10-31) |
| K9c | Q7 eLyMPuS vs canonical P3 | `analysis_v005/secondary.py` | `analysis/q7_elympus.csv` | Claude | before freeze | **done** (added 2026-10-31) |
| K10 | §5.8 retraining | NB201: xautodl / NATS-Bench training script; NHB: NAS-HPO-Bench-II training script — to prepare | `results/retraining/*.json` | Claude (scripts), autor (GPU) | ≤ 2 weeks after the run | to do; cost below |
| K11 | Post-run control (level 5) | pipeline `checks` + post-run check | `checks.json`, `postrun.json` | autor / Claude | at the end of each stage | exists |

**Retraining cost (szacunek, nie pomiar):** benchmark tables give the training time on the benchmark authors' GPU:
NB201 200 epochs — median 61 min per cell (p10 40, p90 81 min; 300 random cells); NAS-HPO-II 12 epochs — median 2.3 min
(p90 9 min). Knee points: NB201 22 arms (21 main + eLyMPuS; no MF track on NB201) ≈ 22 GPU-h; NAS-HPO-II 27 arms ≈ 1–4
GPU-h. Total ≈ 25 GPU-h on a GPU of the same class, plus environment set-up. GPU: Hetzner dedicated GPU server (decision 2026-10-31); offer and
price to be checked before ordering.

## 7a. Exploratory addendum E1 — the surrogate at a larger budget (written 2026-11-16, before any E1 run)

**Status: exploratory.** Planned after the v005 results were seen (`notes/archive/v005/analysis-v005/reports/02`, `03`); reported in
its own section, never as confirmatory; reported whatever its outcome (author's decision 2026-11-16, B5 a).

- **Why:** at b ≤ 350 P3Net takes few mixing steps (median per run on the primary spaces: 0, 0, 1, 8 at b = 50, 100,
  200, 350), and with no mixing step it is canonical P3 (report 03: same engine, shifted random stream). Q2/Q3 therefore
  cannot show what the surrogate contributes.
- **Question:** when the surrogate has room to act, does P3Net (or P3Net-gate, P3Net-nolink) differ from canonical P3?
- **Arms:** `v005_p3net`, `v005_p3net_gate`, `v005_p3net_nolink`, `v005_p3_canonical`, and `v005_random_search` as a
  reference point only. No other comparison arm: **E1 supports no claim about P3Net vs. the other methods.**
- **Grid:** the four primary spaces (JAHS C10, CRC, FMN; NAS-HPO-Bench-II) × b = 1 000 × seeds **92–121** (never used
  before) = 600 runs; same code as v005 (commit `c674c91e`; the working tree differs only in new analysis scripts and
  the E1 plan file, recorded in the run manifest); plan `configs/pipeline/v005-e1.yaml`, run root
  `results/runs/c674c91e-e1`.
- **Analysis (fixed now):** per space, the Q2 family (P3Net vs canonical P3, P3Net-gate, P3Net-nolink): two-sided
  Mann–Whitney U, Holm within the space, α = 0.05, Cliff's δ positive = P3Net better; TOST as in §4 (m = 0.33 and 0.147);
  descriptively: median mixing steps and surrogate share per arm, share of runs identical to P3Net, P3Net and canonical
  P3 vs random search (δ only). Metrics as §3.
- **Before the grid:** a timing pilot on seed 200 (outside 92–121; its results are not analysed); the grid runs only if
  the measured cost is acceptable to the author.

## 8. Deviations

Any change to this plan after the run starts is recorded here with the date and the reason, and the affected results
are marked in the paper.

1. **JAHS-Bench-201 CIFAR-10 points rerun with 2 workers (2026-11-03 decision, rerun 2026-11-09…11).** The
   out-of-memory killer stopped the shared JAHS bridge (13–15 GB) during the 6-worker run (`dmesg` 2026-11-02 and
   2026-11-06 02:27); every point queued for that bridge then failed its 3 attempts with "shared jahs-bench bridge
   closed the connection" — 3 000 points, all on `jahs_bench_201_v005`: main 2 160, MF 600, GP 120, eLyMPuS 120. The
   author decided (a): run unchanged, then rerun the failed points with `--retry-failed` and 2 workers, same commit and
   run root (`c674c91e`). All 3 000 completed; no other point failed. Effect: quality metrics are unaffected (the
   benchmark is deterministic and the methods do not depend on the worker count), but the wall-clock times of these
   3 000 points were measured with 2 workers instead of 6 sharing 16 vCPUs (§5.3). Q6 times on JAHS C10 are therefore
   reported separately from the other spaces and marked. Besides the bridge, the 6-worker run had 41 worker restarts
   after the out-of-memory killer (restart from scratch, §4); the 2-worker rerun had none.
2. **OSS Vizier worker restarts (2026-11-06…15).** The Vizier worker's memory grows to about 25 GB over a few points
   until the out-of-memory killer stops it; it is restarted and the interrupted point starts again from scratch (§4).
   118 restarts in total: 20 in the first attempt (2026-11-06, which then stopped at the default limit of 20 restarts
   per worker, 79 of 540 points done) and 98 in the second (2026-11-12…15, `--max-worker-restarts 1000`, same commit,
   run root `c674c91e-vizier`). All 540 points completed. Vizier wall-clock times include no time from interrupted
   attempts (each record is written by the attempt that finished).
3. **§5.4 surrogate decision quality not performed (decision 2026-11-16, K8).** The v005 methods (`p3net/v005/`) do not
   log surrogate decisions (`decision_log`; only the v004 class `p3net.methods.p3net` does), so no run record has
   `diagnostics.surrogate_decisions` and the posthoc files (`scripts/posthoc_metrics.py`) have `decisions = None`.
   Found after the run; rerunning the six surrogate arms with logging would change method code after the freeze. Instead
   the paper reports the surrogate share and the number of mixing steps per cell (§5.5, `budget_use.csv`). The posthoc
   queries were still run (JAHS seeds 62–71, R8 b; tabular spaces all seeds) and give `history_metrics` only.
4. **§5.8 retraining — details the plan left open (decision 2026-11-16).** The budget of the knee point was not stated:
   it is the arm's largest budget (350; GP arms 100). The median run of 30 is the one at index (n − 1) // 2 after sorting
   by IGD+ then seed; a front of two points takes the point with lower f1. Arms whose knee is the same configuration share
   one training (40 trainings for 49 knee points: NB201 16 of 22, NAS-HPO-II 24 of 27). One seed per training (NB201 777,
   NAS-HPO-II 222 — the first seed of each benchmark). The NAS-HPO-II network is built with xautodl's TinyNetwork (same
   skeleton and op set as the authors' `nasbench201like`), not the authors' module. Hardware: Intel Core i7-11800H
   (16 threads), 32 GB RAM, NVIDIA GeForce RTX 3050 Ti (4 GB), Windows 11. Data loading (2026-11-16): the
   first three NAS-HPO-II trainings ran with 4 non-persistent DataLoader workers, the rest with 8 persistent ones
   (3× faster on Windows); the protocol is unchanged, only the workers' augmentation random stream differs (recorded
   as `loader` in each result file; absent = the first setting). Script and sources:
   `scripts/retrain_v005.py`, `scripts/retraining_knees_v005.py`.
5. **P3Net-gate: description in Q2 (b) does not match the code that was run (found 2026-11-17, card audit
   `notes/archive/v005/plans/v005-audit-cards.md`, F1-F2).** §1 Q2 (b) describes P3Net-gate as a "quantile acceptance gate". The
   code used for every run (`p3net/v005/p3/engine.py`, `_mix_gate`, unchanged since commit b7f52553 and identical in
   `c674c91e`) has no quantile: a mixing step is evaluated for real only when its *predicted* objectives would pass the
   MO-GOMEA acceptance rule used in mixing (decision D-1 b), and the real values then decide acceptance. The source
   card was ambiguous (`p3net.md` D-3 a: "when the surrogate predicts an improvement (with a threshold)";
   `p3net-surrogate.md` §5: "quantile gate"), and the implementer resolved it without recording a question. In the
   same variant the surrogate is refitted before mixing with each level, not after every real evaluation inside the
   mixing loop (card S-7 a); for P3Net (D-3 b) the two are equivalent, because its real evaluation comes at the end of
   the level. Nothing is rerun: the Q2/Q3 results for P3Net-gate and E1 describe the gate as implemented, and the
   paper describes that gate. A level-1 test of the implemented gate (property W17) was added on 2026-11-17.
