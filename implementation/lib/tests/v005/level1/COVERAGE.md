# Pokrycie własności testami poziomu 1 (v005)

Każda własność z tabel „Własności do sprawdzenia testami” w `notes/plans/v005-sources/*.md` ma co najmniej jeden test
(plik generowany z nazw testów: identyfikator własności jest prefiksem nazwy, np. `test_W11_…`, `test_WL2_WL4_…`).

Uwagi: `Q-xx` — test oznaczony `needs_clarification` (pytanie w `QUESTIONS.md`); `dane` — `benchmark_data`
(pomijany bez danych benchmarków); `lib` — pomijany, gdy biblioteki nie ma w środowisku (`importorskip`; uruchamiać w
środowisku `implementation/experiments/.venv`); `Linux` — uruchamiany tylko na Linuksie.

| ID własności | karta | test(y) | uwagi |
|---|---|---|---|
| W1 | `p3net.md` | `test_p3net.py::test_W1_one_new_solution_per_iteration_enters_P0_iff_not_in_hashset` |  |
| W2 | `p3net.md` | `test_p3net.py::test_W2_solution_is_mixed_with_every_level_even_without_improvement` |  |
| W3 | `p3net.md` | `test_p3net.py::test_W3_promotion_only_on_dominance_and_only_if_not_in_hashset` |  |
| W4 | `p3net.md` | `test_p3net.py::test_W4_pyramid_add_rejects_solution_present_on_any_level`<br>`test_p3net.py::test_W4_levels_disjoint_after_a_run` |  |
| W5 | `p3net.md` | `test_p3net.py::test_W5_pyramid_has_no_target_sizes`<br>`test_p3net.py::test_W5_level_sizes_equal_number_of_inserts` |  |
| W6 | `p3net.md` | `test_p3net.py::test_W6_fihc_ends_in_local_optimum`<br>`test_p3net.py::test_W6_fihc_accepts_only_strict_improvement_and_stops_after_one_quiet_pass` |  |
| W7 | `p3net.md` | `test_p3net.py::test_W7_entropy_matches_eq2_on_hand_example`<br>`test_p3net.py::test_W7_cluster_distance_matches_eq1_on_hand_example`<br>`test_p3net.py::test_W7_build_clusters_recovers_trap_blocks` |  |
| W8 | `p3net.md` | `test_p3net.py::test_W8_useful_has_all_singletons_and_no_root` |  |
| W9 | `p3net.md` | `test_p3net.py::test_W9_clusters_with_zero_distance_removed` |  |
| W10 | `p3net.md` | `test_p3net.py::test_W10_clusters_ordered_smallest_first_ties_random` |  |
| W11 | `p3net.md` | `test_p3net.py::test_W11_donor_differs_on_cluster`<br>`test_p3net.py::test_W11_no_evaluation_when_no_donor_differs` |  |
| W12 | `p3net.md` | `test_p3net.py::test_W12_rejected_change_reverted_accepted_change_kept`<br>`test_p3net.py::test_W12_mogomea_accept_rule` |  |
| W13 | `p3net.md` | `test_p3net.py::test_W13_at_most_one_evaluation_per_cluster` |  |
| W14 | `p3net.md` | `test_p3net.py::test_W14_p3net_real_evaluations_per_iteration` |  |
| W15 | `p3net.md` | `test_p3net.py::test_W15_every_real_evaluation_in_history_and_no_duplicates`<br>`test_p3net.py::test_W15_eval_cache_is_the_history` |  |
| W16 | `p3net.md` | `test_p3net.py::test_W16_p3_finds_trap_optimum_in_8_of_10_runs` |  |
| W-K1 | `p3-canonical.md` | `test_p3_canonical.py::test_WK1_no_surrogate_object_and_no_surrogate_calls` |  |
| W-K2 | `p3-canonical.md` | `test_p3_canonical.py::test_WK2_each_changing_mixing_step_costs_one_real_evaluation` |  |
| W-K3 | `p3-canonical.md` | `test_p3_canonical.py::test_WK3_oracle_surrogate_reproduces_canonical_trajectory` |  |
| W-K4 | `p3-canonical.md` | `test_p3_canonical.py::test_WK4_budget_never_exceeded_and_stops_mid_iteration`<br>`test_p3_canonical.py::test_WK4_budget_object_rule` |  |
| W-K5 | `p3-canonical.md` | `test_p3_canonical.py::test_WK5_single_objective_mode_is_well_defined` | warunek wstępny; właściwy test zgodności z kodem autorów to poziom 2 (inna rola) |
| W-S1 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS1_predictions_never_consume_budget` |  |
| W-S2 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS2_predicts_both_objectives_f2_from_model`<br>`test_p3net_surrogate.py::test_WS2_p3net_has_no_access_to_f2_of_unevaluated` |  |
| W-S3 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS3_interaction_features_only_within_clusters`<br>`test_p3net_surrogate.py::test_WS3_nolink_variant_has_no_interactions` |  |
| W-S4 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS4_linkage_features_predict_better_on_traps` |  |
| W-S5 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS5_log_scale_predictions_are_scale_invariant`<br>`test_p3net_surrogate.py::test_WS5_nonpositive_objective_rejected`<br>`test_p3net_surrogate.py::test_WS5_acceptance_decisions_invariant_under_log` |  |
| W-S6 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS6_grouped_cv_no_solution_in_train_and_validation` |  |
| W-S7 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS7_chain_error_is_recorded` |  |
| W-S8 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS8_no_surrogate_before_first_completed_fihc` |  |
| W-S9 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS9_model_is_antisymmetric` |  |
| W-S10 | `p3net-surrogate.md` | `test_p3net_surrogate.py::test_WS10_same_surrogate_in_p3net_and_gate_variant` |  |
| W-B1 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB1_no_hill_climber_new_solution_goes_to_level_0` |  |
| W-B2 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB2_warmup_is_20_percent_all_real_before_first_training` |  |
| W-B3 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB3_climbs_all_levels_promotes_only_when_compare_prefers` |  |
| W-B4 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB4_donor_differs_on_F_when_one_exists` |  |
| W-B5 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB5_dsa_real_evaluation_iff_gate_passes` |  |
| W-B6 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB6_compare_uses_real_values_when_both_have_them` |  |
| W-B7 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB7_alpha_starts_at_one_decays_and_resets`<br>`test_bartnik.py::test_WB7_first_iteration_with_change_keeps_alpha_one` |  |
| W-B8 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB8_dominance_probability_hand_values`<br>`test_bartnik.py::test_WB8_dominance_probability_zero_sigma_is_a_step` |  |
| W-B9 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB9_psa_revert_iff_prevert_ge_tau_and_gt_pkeep`<br>`test_bartnik.py::test_WB9_psa_history_grows_by_max_probability` |  |
| W-B10 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB10_quantile_threshold_is_alpha_quantile`<br>`test_bartnik.py::test_WB10_quantile_threshold_is_numpy_linear` |  |
| W-B11 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB11_surrogate_refit_after_every_real_evaluation` |  |
| W-B12 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB12_stops_after_1000_iterations_without_new_evaluation` |  |
| W-B13 | `bartnik-mo-sa-p3-gomea.md` | `test_bartnik.py::test_WB13_two_independent_models_one_per_objective`<br>`test_bartnik.py::test_WB13_no_f2_access_and_budget` |  |
| W-E1 | `elympus.md` | `test_elympus.py::test_WE1_vig_empty_at_start` |  |
| W-E2 | `elympus.md` | `test_elympus.py::test_WE2_hit_costs_nothing_miss_costs_real_evaluations` |  |
| W-E3 | `elympus.md` | `test_elympus.py::test_WE3_full_true_vig_list_answers_always_correct` |  |
| W-E4 | `elympus.md` | `test_elympus.py::test_WE4_discovered_edges_are_true_dependencies` |  |
| W-E5 | `elympus.md` | `test_elympus.py::test_WE5_recursive_ll_finds_the_missing_dependency`<br>`test_elympus.py::test_WE5_recursive_ll_needs_at_most_log2_D_splits` |  |
| W-E6 | `elympus.md` | `test_elympus.py::test_WE6_pairs_stored_before_vig_update_stay_valid` |  |
| W-E7 | `elympus.md` | `test_elympus.py::test_WE7_always_verify_while_vig_empty`<br>`test_elympus.py::test_WE7_gap_grows_by_one_after_each_fruitless_verification`<br>`test_elympus.py::test_WE7_verify_right_after_a_discovery`<br>`test_elympus.py::test_WE7_repeated_optimum_resets_counter` |  |
| W-E7b | `elympus.md` | `test_elympus.py::test_WE7b_entry_orders_all_k_values_from_one_fihc_step` |  |
| W-E8 | `elympus.md` | `test_elympus.py::test_WE8_fihc_elympus_ends_in_local_optimum_with_full_vig` |  |
| W-E9 | `elympus.md` | `test_elympus.py::test_WE9_check_circuits_detects_cycle_and_runs_recursive_ll` |  |
| W-E10 | `elympus.md` | `test_elympus.py::test_WE10_separate_vig_per_objective`<br>`test_elympus.py::test_WE10_real_evaluation_when_one_objective_has_no_pair` |  |
| W-E11 | `elympus.md` | `test_elympus.py::test_WE11_every_solution_in_pyramid_and_history_has_real_values` |  |
| W-E12 | `elympus.md` | `test_elympus.py::test_WE12_always_verify_equals_plain_fihc` |  |
| W-E13 | `elympus.md` | `test_elympus.py::test_WE13_memory_lives_for_the_whole_run` |  |
| E-4 | `elympus.md` | `test_elympus.py::test_E4_unknown_pair_distance_plus_one`<br>`test_elympus.py::test_E4_empty_vig_no_cluster_dropped_by_zero_distance_rule`<br>`test_elympus.py::test_E4_known_if_in_either_objective_vig`<br>`test_elympus.py::test_E4_p3_elympus_pyramid_uses_vig_known` | E-4 / Z-E7 (2026-10-21, Q-45): bez numeru W w karcie |
| W-BB1 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB1_hv_contribution_remove_picks_smallest_contribution`<br>`test_bag_of_baselines.py::test_WBB1_steady_state_one_offspring_per_step`<br>`test_bag_of_baselines.py::test_WBB1_population_constant_and_removed_point_in_last_front` |  |
| W-BB2 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB2_get_budgets_matches_reference` |  |
| W-BB3 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB3_tournament_k3`<br>`test_bag_of_baselines.py::test_WBB3_uniform_crossover_half_from_each_parent`<br>`test_bag_of_baselines.py::test_WBB3_mutation_redraws_n_mut_variables`<br>`test_bag_of_baselines.py::test_WBB3_offspring_from_mutation_or_uniform_crossover` |  |
| W-BB4 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB4_motpe_configuration` | lib |
| W-BB5 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB5_ehvi_is_qnehvi_with_independent_gps_one_point_per_step` | lib |
| W-BB6 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB6_mobananas_selects_four_per_iteration`<br>`test_bag_of_baselines.py::test_WBB6_mobananas_ensemble_and_selection_settings` |  |
| W-BB7 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB7_initial_design_size_rule`<br>`test_bag_of_baselines.py::test_WBB7_mobohb_initial_design_at_max_fidelity`<br>`test_bag_of_baselines.py::test_WBB7_mobohb_num_initial_samples_default`<br>`test_bag_of_baselines.py::test_WBB7_first_batch_is_initial_design`<br>`test_bag_of_baselines.py::test_WBB7_budget_never_exceeded` |  |
| W-BB8 | `bag-of-baselines.md` | `test_bag_of_baselines.py::test_WBB8_no_access_to_f2_outside_evaluation` |  |
| W-N1 | `nsga-net.md` | `test_nsga_net.py::test_WN1_binary_tournament_dominance_then_crowding_then_random` |  |
| W-N2 | `nsga-net.md` | `test_nsga_net.py::test_WN2_two_point_crossover_structure_and_rate` |  |
| W-N3 | `nsga-net.md` | `test_nsga_net.py::test_WN3_integer_polynomial_mutation_in_range_local_and_rare` |  |
| W-N4 | `nsga-net.md` | `test_nsga_net.py::test_WN4_survival_is_rank_and_crowding_mu_plus_lambda` |  |
| W-N5 | `nsga-net.md` | `test_nsga_net.py::test_WN5_duplicates_eliminated_before_evaluation` |  |
| W-N6 | `nsga-net.md` | `test_nsga_net.py::test_WN6_population_20_offspring_20_budget_respected`<br>`test_nsga_net.py::test_WN6_start_is_random` |  |
| W-V1 | `nsganetv2.md` | `test_nsganetv2.py::test_WV1_start_then_iterations_of_eight` |  |
| W-V2 | `nsganetv2.md` | `test_nsganetv2.py::test_WV2_adaptive_switching_pool`<br>`test_nsganetv2.py::test_WV2_selection_criterion_and_fold_count`<br>`test_nsganetv2.py::test_WV2_too_few_points_cart_wins`<br>`test_nsganetv2.py::test_WV2_small_initial_design_propose_does_not_raise` |  |
| W-V3 | `nsganetv2.md` | `test_nsganetv2.py::test_WV3_inner_nsga2_on_predicted_objectives` |  |
| W-V4 | `nsganetv2.md` | `test_nsganetv2.py::test_WV4_candidates_in_archive_rejected` |  |
| W-V5 | `nsganetv2.md` | `test_nsganetv2.py::test_WV5_subset_selection_picks_K_minimising_gap_spread` |  |
| W-V6 | `nsganetv2.md` | `test_nsganetv2.py::test_WV6_no_f2_access_and_budget` |  |
| W-R1 | `reinforce.md` | `test_reinforce.py::test_WR1_one_sample_per_step`<br>`test_reinforce.py::test_WR1_factorised_policy_small_initial_logits` |  |
| W-R2 | `reinforce.md` | `test_reinforce.py::test_WR2_baseline_updated_before_advantage_adam_lr_05` |  |
| W-R3 | `reinforce.md` | `test_reinforce.py::test_WR3_mnasnet_soft_reward`<br>`test_reinforce.py::test_WR3_R4_online_minmax_normalisation`<br>`test_reinforce.py::test_WR3_online_minmax_degenerate_objective_maps_to_zero`<br>`test_reinforce.py::test_WR3_mnasnet_target_constant_during_run` |  |
| W-R4 | `reinforce.md` | `test_reinforce.py::test_WR4_monas_mixed_reward`<br>`test_reinforce.py::test_WR3_R4_online_minmax_normalisation` |  |
| W-R5 | `reinforce.md` | `test_reinforce.py::test_WR5_adc_reward_hand_examples` |  |
| W-R6 | `reinforce.md` | `test_reinforce.py::test_WR6_cosine_temperature_with_restarts` |  |
| W-R7 | `reinforce.md` | `test_reinforce.py::test_WR7_duplicates_free_and_budget`<br>`test_reinforce.py::test_WR7_policy_updated_on_duplicates` |  |
| W-R8 | `reinforce.md` | `test_reinforce.py::test_WR8_budget_never_exceeded` |  |
| W-RE1 | `regevo.md` | `test_regevo.py::test_WRE1_start_is_20_random_valid_evaluated` |  |
| W-RE2 | `regevo.md` | `test_regevo.py::test_WRE2_sample_of_five_with_replacement` |  |
| W-RE3 | `regevo.md` | `test_regevo.py::test_WRE3_rank_is_computed_on_the_population_not_the_sample`<br>`test_regevo.py::test_WRE3_crowding_tie_break_on_population_front` |  |
| W-RE4 | `regevo.md` | `test_regevo.py::test_WRE4_mutation_changes_exactly_one_variable`<br>`test_regevo.py::test_WRE4_cell_mutation_node_then_incoming_edge_nb201`<br>`test_regevo.py::test_WRE4_hp_variables_are_units_on_par_with_nodes_jahs`<br>`test_regevo.py::test_WRE4_uniform_variable_choice_without_cell` |  |
| W-RE5 | `regevo.md` | `test_regevo.py::test_WRE5_oldest_removed_population_constant` |  |
| W-RE6 | `regevo.md` | `test_regevo.py::test_WRE6_duplicate_child_enters_population_without_budget`<br>`test_regevo.py::test_WRE6_budget_never_exceeded` |  |
| W-L1 | `mo-ls.md` | `test_mo_ls.py::test_WL1_new_random_start_and_new_lambda_each_round` |  |
| W-L2 | `mo-ls.md` | `test_mo_ls.py::test_WL2_WL4_one_round_each_variable_once_all_values_then_restart` |  |
| W-L3 | `mo-ls.md` | `test_mo_ls.py::test_WL3_move_only_on_strict_improvement`<br>`test_mo_ls.py::test_WL3_ties_do_not_move` |  |
| W-L4 | `mo-ls.md` | `test_mo_ls.py::test_WL2_WL4_one_round_each_variable_once_all_values_then_restart` |  |
| W-L5 | `mo-ls.md` | `test_mo_ls.py::test_WL5_online_normalisation`<br>`test_mo_ls.py::test_WL5_duplicates_free_budget_exact` |  |
| W-A1 | `library-adapters.md` | `test_library_adapters.py::test_WA1_smac3_parego_configuration`<br>`test_library_adapters.py::test_WA1_moead_configuration`<br>`test_library_adapters.py::test_WA1_nsga3_motpe_vizier_rs_configuration`<br>`test_library_adapters.py::test_WA1_gp_arms_configuration` | lib |
| W-A2 | `library-adapters.md` | `test_library_adapters.py::test_WA2_smac3_initial_design_size` | lib |
| W-A3 | `library-adapters.md` | `test_library_adapters.py::test_WA3_moead_categorical_values_and_full_budget` | lib |
| W-A4 | `library-adapters.md` | `test_library_adapters.py::test_WA4_gp_initial_design`<br>`test_library_adapters.py::test_WA4_gp_pool_valid_unevaluated` | lib |
| W-A5 | `library-adapters.md` | `test_library_adapters.py::test_WA5_motpe_adapter_matches_native_optuna_loop`<br>`test_library_adapters.py::test_WA5_smac3_adapter_matches_native_smac_loop` | lib |
| W-A6 | `library-adapters.md` | `test_library_adapters.py::test_WA6_duplicates_free_budget_never_exceeded`<br>`test_library_adapters.py::test_WA6_random_search_exhausts_space_without_repeats` | lib |
| W-MF1 | `mf-track.md` | `test_mf_track.py::test_WMF1_cost_is_resume_fraction`<br>`test_mf_track.py::test_WMF1_total_cost_within_budget` |  |
| W-MF2 | `mf-track.md` | `test_mf_track.py::test_WMF2_front_only_from_full_fidelity` |  |
| W-MF3 | `mf-track.md` | `test_mf_track.py::test_WMF3_f2_at_low_fidelity_is_observed_not_full` |  |
| W-MF4 | `mf-track.md` | `test_mf_track.py::test_WMF4_hyperband_brackets_match_li_et_al` |  |
| W-MF5 | `mf-track.md` | `test_mf_track.py::test_WMF5_asha_promotes_from_highest_rung_when_enough_candidates` |  |
| W-MF6 | `mf-track.md` | `test_mf_track.py::test_WMF6_promotion_by_nds_and_crowding` |  |
| W-MF7 | `mf-track.md` | `test_mf_track.py::test_WMF7_hyperband_asha_ladders`<br>`test_mf_track.py::test_WMF7_bob_ladders_keep_source_ratio` |  |
| W-BM1 | `benchmarks.md` | `test_benchmarks.py::test_WBM1_no_method_code_reads_the_test_split`<br>`test_benchmarks.py::test_WBM1_nb201_f1_is_validation_error_mean_over_seeds` | dane |
| W-BM2 | `benchmarks.md` | `test_benchmarks.py::test_WBM2_nb201_f2_from_complete_energy_table` | dane |
| W-BM3 | `benchmarks.md` | `test_benchmarks.py::test_WBM3_energy_table_matches_hwnasbench_source`<br>`test_benchmarks.py::test_WBM3_wrong_sha256_rejected_before_unpickling` | dane |
| W-BM4 | `benchmarks.md` | `test_benchmarks.py::test_WBM4_jahs_f2_follows_bm3_check` | dane |
| W-BM5 | `benchmarks.md` | `test_benchmarks.py::test_WBM5_f1_validation_and_f2_low_fidelity`<br>`test_benchmarks.py::test_WBM5_fcnet_f2_scaled_by_epochs` | dane |
| W-BM6 | `benchmarks.md` | `test_benchmarks.py::test_WBM6_validity_rejects_cells_without_path`<br>`test_benchmarks.py::test_WBM6_validity_same_rule_on_all_cell_spaces` |  |
| W-BM7 | `benchmarks.md` | `test_benchmarks.py::test_WBM7_resource_fields_present_in_every_run_record`<br>`test_benchmarks.py::test_WBM7_zero_is_not_an_empty_resource_field`<br>`test_benchmarks.py::test_WBM7_run_peak_excludes_earlier_run_in_same_process` | Linux, dane |

Razem: 118 własności z 14 kart (117 W-* + E-4); każda ma ≥ 1 test.
