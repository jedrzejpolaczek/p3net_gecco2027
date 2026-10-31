# v005 — tabela „zdanie ↔ test” (protokół §4)

Każde zdanie artykułu, które opisuje działanie metody lub benchmarku, ma test, który by nie przeszedł, gdyby zdanie było
fałszywe. Zdanie bez testu nie trafia do artykułu albo dostaje sformułowanie ostrożne i status „niesprawdzalne testem”
z uzasadnieniem. Bramka `checks` (`run_pipeline.py`, `cards: true`) wymaga, by każdy wiersz `C-…` miał test i status ✅.

Zdania są w brzmieniu roboczym (po angielsku, jak w artykule); etap C może je przeredagować, ale nie zmieni ich treści
bez zmiany tego pliku. Testy: poziom 1 — `implementation/lib/tests/v005/level1/<plik>::<test>`; poziom 2 —
`implementation/lib/tests/v005/level2/…` (wyniki w `v005-level2-criteria.md`). Status: ✅ = test przechodzi
(ostatni przebieg w kolumnie „Weryfikacja” na końcu pliku).

## P3 i P3Net (karty `p3-canonical.md`, `p3net.md`, `p3net-surrogate.md`)

| ID | Zdanie (artykuł, sekcja) | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-01 | Each iteration adds one new random solution, improves it with a first-improvement hill climber and inserts it into the lowest level if it is not yet in the pyramid. (Methods, P3) | P3, P3Net | test_p3net.py::test_W1_one_new_solution_per_iteration_enters_P0_iff_not_in_hashset; test_W6_fihc_ends_in_local_optimum | ✅ |
| C-02 | The solution is then mixed with every level of the pyramid, whether or not it improved. (Methods, P3) | P3, P3Net | test_p3net.py::test_W2_solution_is_mixed_with_every_level_even_without_improvement | ✅ |
| C-03 | It is promoted to the next level only if it dominates its value before mixing and is not yet in the pyramid. (Methods, P3) | P3, P3Net | test_p3net.py::test_W3_promotion_only_on_dominance_and_only_if_not_in_hashset; test_W4_pyramid_add_rejects_solution_present_on_any_level | ✅ |
| C-04 | The pyramid has no target level sizes. (Methods, P3) | P3, P3Net | test_p3net.py::test_W5_pyramid_has_no_target_sizes | ✅ |
| C-05 | Linkage clusters are built per level with P3's entropy distance; all singletons are used, the root is not, and children of a zero-distance merge are dropped. (Methods, P3) | P3, P3Net | test_p3net.py::test_W7_cluster_distance_matches_eq1_on_hand_example; test_W8_useful_has_all_singletons_and_no_root; test_W9_clusters_with_zero_distance_removed | ✅ |
| C-06 | Clusters are applied smallest first, ties in random order, with a donor that differs from the solution on the cluster. (Methods, P3) | P3, P3Net | test_p3net.py::test_W10_clusters_ordered_smallest_first_ties_random; test_W11_donor_differs_on_cluster | ✅ |
| C-07 | With two objectives, a hill-climbing move and a promotion require Pareto dominance; a mixing step is kept under the MO-GOMEA acceptance rule. (Methods, P3) | P3, P3Net | test_p3net.py::test_W6_fihc_accepts_only_strict_improvement_and_stops_after_one_quiet_pass; test_W12_mogomea_accept_rule | ✅ |
| C-08 | Canonical P3 evaluates every changing mixing step and uses no surrogate. (Baselines) | P3 | test_p3_canonical.py::test_WK1_no_surrogate_object_and_no_surrogate_calls; test_WK2_each_changing_mixing_step_costs_one_real_evaluation | ✅ |
| C-09 | Our P3 implementation matches Goldman's code: on deceptive traps the evaluations to the optimum agree within 1 % of the median (7000 runs). (Verification, suppl.) | P3 | level2: elympus_vs_islandga.py (p3 vs p3goldman), wynik w v005-level2-criteria.md | ✅ |
| C-10 | P3Net replaces the evaluations of mixing steps by a pairwise surrogate and evaluates the solution for real once per level. (Methods, P3Net) | P3Net | test_p3net.py::test_W14_p3net_real_evaluations_per_iteration; test_p3net_surrogate.py::test_WS1_predictions_never_consume_budget | ✅ |
| C-11 | With the surrogate replaced by an exact oracle, P3Net reproduces the trajectory of canonical P3. (Methods, P3Net) | P3Net | test_p3_canonical.py::test_WK3_oracle_surrogate_reproduces_canonical_trajectory | ✅ |
| C-12 | The surrogate predicts differences of both objectives from pairs of solutions, with interaction features only within linkage clusters, in log scale, and is antisymmetric. (Methods, surrogate) | P3Net | test_p3net_surrogate.py::test_WS2_predicts_both_objectives_f2_from_model; test_WS3_interaction_features_only_within_clusters; test_WS5_log_scale_predictions_are_scale_invariant; test_WS9_model_is_antisymmetric | ✅ |
| C-13 | P3Net never sees f2 of a solution it has not evaluated. (Methods, protocol) | P3Net | test_p3net_surrogate.py::test_WS2_p3net_has_no_access_to_f2_of_unevaluated; level 4 `f2_source` | ✅ |
| C-14 | The no-linkage variant uses no interaction features. (Ablation) | P3NetNoLink | test_p3net_surrogate.py::test_WS3_nolink_variant_has_no_interactions | ✅ |
| C-15 | The surrogate is validated with grouped cross-validation (no solution in both training and validation). (Methods, surrogate) | P3Net | test_p3net_surrogate.py::test_WS6_grouped_cv_no_solution_in_train_and_validation | ✅ |

## Bartnik MO-DSA / MO-PSA (karta `bartnik-mo-sa-p3-gomea.md`)

| ID | Zdanie | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-16 | 20 % of the budget is spent on random solutions before the first surrogate is trained. (Baselines) | MO-DSA, MO-PSA | test_bartnik.py::test_WB2_warmup_is_20_percent_all_real_before_first_training | ✅ |
| C-17 | MO-DSA evaluates a solution for real only if its prediction beats the (1−α)-quantile of the predictions for evaluated solutions on every objective; α starts at 1, decays by 0.999 and resets on improvement. (Baselines) | MO-DSA | test_bartnik.py::test_WB5_dsa_real_evaluation_iff_gate_passes; test_WB7_alpha_starts_at_one_decays_and_resets; test_WB10_quantile_threshold_is_alpha_quantile | ✅ |
| C-18 | MO-PSA reverts a mixing step when the probability that the reverted solution dominates exceeds the threshold. (Baselines) | MO-PSA | test_bartnik.py::test_WB9_psa_revert_iff_prevert_ge_tau_and_gt_pkeep; test_WB8_dominance_probability_hand_values | ✅ |
| C-19 | One random forest per objective, refitted after every real evaluation. (Baselines) | MO-DSA, MO-PSA | test_bartnik.py::test_WB13_two_independent_models_one_per_objective; test_WB11_surrogate_refit_after_every_real_evaluation | ✅ |
| C-20 | No reference code exists; against SAGOMEA (single-objective) our MO-DSA reaches a lower median (37 vs 40 on trap-5, n = 50, 500 evaluations). (Limitations) | MO-DSA | level2: modsa_vs_sagomea.py, wynik w v005-level2-criteria.md | ✅ |

## eLyMPuS (karta `elympus.md`)

| ID | Zdanie | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-21 | eLyMPuS answers a hill-climbing comparison from a stored pair when the context of its dependencies matches, and evaluates otherwise. (Methods, eLyMPuS) | P3-eLyMPuS | test_elympus.py::test_WE2_hit_costs_nothing_miss_costs_real_evaluations; test_WE7b_entry_orders_all_k_values_from_one_fihc_step | ✅ |
| C-22 | A stored answer that turns out wrong reveals a missing dependency, found by recursive halving in at most ⌈log₂ #D⌉ splits (#D = number of differing variables); discovered dependencies are true dependencies. (Methods, eLyMPuS) | P3-eLyMPuS | test_elympus.py::test_WE5_recursive_ll_finds_the_missing_dependency; test_WE5_recursive_ll_needs_at_most_log2_D_splits; test_WE4_discovered_edges_are_true_dependencies | ✅ |
| C-23 | Answers are verified on a 1/x schedule, always while the VIG is empty and right after a discovery. (Methods, eLyMPuS) | P3-eLyMPuS | test_elympus.py::test_WE7_always_verify_while_vig_empty; test_WE7_verify_right_after_a_discovery; test_WE7_gap_grows_by_one_after_each_fruitless_verification | ✅ |
| C-24 | With verification always on, the hill climber follows exactly the trajectory of the plain one. (Methods, eLyMPuS) | P3-eLyMPuS | test_elympus.py::test_WE12_always_verify_equals_plain_fihc | ✅ |
| C-25 | Each objective has its own VIG; a pair of variables counts as dependent for linkage if either VIG holds it, and unknown pairs get linkage distance + 1 (as in OLyMPuS). (Methods, eLyMPuS) | P3-eLyMPuS | test_elympus.py::test_WE10_separate_vig_per_objective; test_E4_unknown_pair_distance_plus_one; test_E4_known_if_in_either_objective_vig; test_E4_p3_elympus_pyramid_uses_vig_known | ✅ |
| C-26 | Compared with the authors' OLyMPuS code, our P3-eLyMPuS discovers no false dependencies and returns true local optima; it needs 13 % fewer evaluations because its hill-climbing loop is Goldman's. (Verification, suppl.) | P3-eLyMPuS | level2: elympus_vs_islandga.py + elympus_cost_breakdown.py, wynik w v005-level2-criteria.md | ✅ |

## Baseline'y (karty `nsga-net.md`, `nsganetv2.md`, `reinforce.md`, `regevo.md`, `mo-ls.md`, `bag-of-baselines.md`, `library-adapters.md`, `mf-track.md`)

| ID | Zdanie | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-27 | NSGA-Net as in the authors' code: binary tournament, two-point crossover, integer polynomial mutation, rank-and-crowding survival, population 20. (Baselines) | NSGA-Net | test_nsga_net.py::test_WN1_binary_tournament_dominance_then_crowding_then_random; test_WN2_two_point_crossover_structure_and_rate; test_WN3_integer_polynomial_mutation_in_range_local_and_rare; test_WN4_survival_is_rank_and_crowding_mu_plus_lambda; test_WN6_population_20_offspring_20_budget_respected | ✅ |
| C-28 | Our NSGA-Net matches the authors' code in hypervolume (100 runs, two problems). (Verification) | NSGA-Net | level2: test_nsganet_vs_reference.py | ✅ |
| C-29 | NSGANetV2 picks its surrogate by adaptive switching among RBF, GP and CART, optimises the predicted objectives with NSGA-II and selects K = 8 candidates by subset selection; its predictors equal the authors' (RBF, GP identical rankings). (Baselines) | NSGANetV2 | test_nsganetv2.py::test_WV2_adaptive_switching_pool; test_WV3_inner_nsga2_on_predicted_objectives; test_WV5_subset_selection_picks_K_minimising_gap_spread; level2: test_nsganetv2_vs_reference.py | ✅ |
| C-30 | REINFORCE as in the NAS-Bench-201 code (factorised policy, moving-average baseline, Adam, lr 0.5); the policy converges after 40–90 of 350 evaluations. (Baselines, Limitations) | REINFORCE | test_reinforce.py::test_WR1_factorised_policy_small_initial_logits; test_WR2_baseline_updated_before_advantage_adam_lr_05; level2: test_reinforce_regevo_vs_nb201.py; level 3 (PASS-COLLAPSE) | ✅ |
| C-31 | Regularized evolution: tournament of S members with replacement, mutation of one node edge as in the NAS-Bench-201 code, oldest member removed; the tournament winner is chosen by NSGA-II's crowded comparison on the population. (Baselines) | RegEvo | test_regevo.py::test_WRE2_sample_of_five_with_replacement; test_WRE4_cell_mutation_node_then_incoming_edge_nb201; test_WRE5_oldest_removed_population_constant; test_WRE3_rank_is_computed_on_the_population_not_the_sample | ✅ |
| C-32 | MO-LS: random scalarisation per round, every variable once with all values, a move only on strict improvement. (Baselines) | MO-LS | test_mo_ls.py::test_WL1_new_random_start_and_new_lambda_each_round; test_WL2_WL4_one_round_each_variable_once_all_values_then_restart; test_WL3_move_only_on_strict_improvement | ✅ |
| C-33 | SH-EMOA and MO-BANANAS follow the Bag-of-Baselines code; both match it in hypervolume (100 runs). (Baselines, Verification) | SH-EMOA, MO-BANANAS | test_bag_of_baselines.py::test_WBB1_steady_state_one_offspring_per_step; test_WBB6_mobananas_selects_four_per_iteration; level2: test_bob_loops_vs_reference.py | ✅ |
| C-34 | Library baselines (MOTPE, SMAC3-ParEGO, NSGA-III, MOEA/D, qNEHVI, qParEGO, Vizier, RS) run at library defaults; MOTPE and SMAC3 reproduce the native library loops exactly. (Baselines) | biblioteki | test_library_adapters.py::test_WA1_smac3_parego_configuration; test_WA5_motpe_adapter_matches_native_optuna_loop; test_WA5_smac3_adapter_matches_native_smac_loop; level2: test_moead_vs_pymoo.py | ✅ |
| C-35 | Every initial design is at most a quarter of the budget. (Protocol) | wszystkie z initial design | test_bag_of_baselines.py::test_WBB7_initial_design_size_rule; test_library_adapters.py::test_WA2_smac3_initial_design_size; level 4 `initial_design` | ✅ |
| C-36 | Hyperband follows Li et al.'s brackets; MO-BOHB follows the hpbandster code, including its initial design at full fidelity. (MF track) | Hyperband, MO-BOHB | test_mf_track.py::test_WMF4_hyperband_brackets_match_li_et_al; test_bag_of_baselines.py::test_WBB7_mobohb_initial_design_at_max_fidelity; level2: test_mf_schedules.py | ✅ |
| C-37 | In the multi-fidelity track the cost of a query is the fraction of full training it adds, and the front contains only full-fidelity results. (MF track) | tor MF | test_mf_track.py::test_WMF1_cost_is_resume_fraction; test_WMF2_front_only_from_full_fidelity | ✅ |

## Protokół i benchmarki (karta `benchmarks.md`, decyzje wspólne)

| ID | Zdanie | Metoda | Test(y) | Status |
|---|---|---|---|---|
| C-38 | No method ever exceeds the budget; a run stops at the b-th real evaluation. (Protocol) | wszystkie | test_p3_canonical.py::test_WK4_budget_never_exceeded_and_stops_mid_iteration; test_bag_of_baselines.py::test_WBB7_budget_never_exceeded; test_regevo.py::test_WRE6_budget_never_exceeded; level 4 `budget` | ✅ |
| C-39 | Re-evaluating an already evaluated solution costs no budget. (Protocol) | wszystkie | test_library_adapters.py::test_WA6_duplicates_free_budget_never_exceeded; test_reinforce.py::test_WR7_duplicates_free_and_budget; test_mo_ls.py::test_WL5_duplicates_free_budget_exact | ✅ |
| C-40 | No method receives the second objective of a solution it has not evaluated. (Protocol) | wszystkie | test_bag_of_baselines.py::test_WBB8_no_access_to_f2_outside_evaluation; test_bartnik.py::test_WB13_no_f2_access_and_budget; test_nsganetv2.py::test_WV6_no_f2_access_and_budget; level 4 `f2_source` | ✅ |
| C-41 | f1 is always a validation error; no method reads the test split. (Benchmarks) | benchmarki | test_benchmarks.py::test_WBM1_no_method_code_reads_the_test_split; test_WBM1_nb201_f1_is_validation_error_mean_over_seeds; test_WBM5_f1_validation_and_f2_low_fidelity | ✅ (2026-10-31, z tablicą HW-NAS-Bench) |
| C-42 | On NAS-Bench-201, f2 is the per-image inference energy on an edge GPU (Jetson TX2, batch 1) published in HW-NAS-Bench, not measured by us. (Benchmarks, Limitations) — treść zmieniona 2026-10-31 (P1 a); dawniej: „measured on one GPU with locked clocks and drift correction” | NB201 | test_benchmarks.py::test_WBM2_nb201_f2_from_complete_energy_table; test_WBM3_energy_measurement_protocol_and_quality (oba do przepisania w rundzie 8 wg nowych W-BM2, W-BM3 w `benchmarks.md`) | ⏳ runda 8 (obecne testy sprawdzają protokół laptopa i padają) |
| C-43 | On JAHS-Bench-201, f2 is the analytic parameter count, because the surrogate's model size varies with hyperparameters at a fixed cell. (Benchmarks) | JAHS | test_benchmarks.py::test_WBM4_jahs_f2_follows_bm3_check | ✅ |
| C-44 | A cell is valid if a path from input to output avoids `none` edges; invalid cells are never evaluated. (Benchmarks) | wszystkie | test_benchmarks.py::test_WBM6_validity_rejects_cells_without_path; test_WBM6_validity_same_rule_on_all_cell_spaces | ✅ |
| C-45 | Every run is deterministic given its seed. (Reproducibility) | wszystkie | bramka `checks`: determinizm 27/27 (`results/checks_determinism_v005*.log`) | ✅ |

## Weryfikacja

Ostatni przebieg (2026-10-23):
- poziom 1, `implementation/lib/tests/v005/level1`: **302 passed, 0 failed, 7 skipped** (pominięte = testy z danymi
  benchmarków); z `P3NET_BENCHMARK_DATA`: 8 passed, 3 failed (W-BM1 NB201, W-BM2, W-BM3 — brak tablicy energii),
  1 skipped (W-BM7: brak rekordów v005 w `results/runs`);
- poziom 2: wyniki w `v005-level2-criteria.md` (zdania C-09, C-20, C-26, C-28, C-29, C-33, C-34, C-36 opisują te wyniki
  zgodnie z nimi, także tam, gdzie kryterium zgodności nie zostało spełnione);
- poziom 3: 476 przebiegów v004-celów + powtórka JAHS z celami v005 (26 PASS, 1 TIMEOUT), 0 FAIL;
- determinizm + poziom 4: 27/27 metod.

C-41 i C-42 blokują bramkę `checks` do czasu zbudowania tablicy energii NB201 — zgodnie z zamierzeniem.
**2026-10-31:** P1 = a. Tablica `nb201_energy.json` zbudowana z HW-NAS-Bench (15 625, 0 rozbieżności indeksów).
Z `P3NET_BENCHMARK_DATA`: 10 passed, 3 failed — W-BM2, W-BM3 (stary protokół laptopa → runda 8), W-BM7 (puste
`peak_memory_server_mb` w rekordach A8 JAHS → poprawka P3 (2a), poz. 3b w `v005-todo.md`).
