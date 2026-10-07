
$ ["python3", "-B", "-c", "import unittest; s=unittest.defaultTestLoader.discover('tests'); assert s.countTestCases() > 0, 'No tests discovered'; r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())"]
test_closure_requires_its_own_committed_record (test_archive.ArchiveTests.test_closure_requires_its_own_committed_record) ... ok
test_complete_snapshot_checksums_and_repeat_do_not_overwrite (test_archive.ArchiveTests.test_complete_snapshot_checksums_and_repeat_do_not_overwrite) ... ok
test_dirty_and_untracked_files_are_refused (test_archive.ArchiveTests.test_dirty_and_untracked_files_are_refused) ... ok
test_missing_retro_is_refused (test_archive.ArchiveTests.test_missing_retro_is_refused) ... ok
test_run_symlink_is_not_followed (test_archive.ArchiveTests.test_run_symlink_is_not_followed) ... ok
test_unsafe_destination_and_names_are_refused (test_archive.ArchiveTests.test_unsafe_destination_and_names_are_refused) ... ok
test_groups_existing_outputs_and_keeps_future_stages_empty (test_artifacts.ArtifactTests.test_groups_existing_outputs_and_keeps_future_stages_empty) ... ok
test_light_review_keeps_brief_and_checklist_together (test_artifacts.ArtifactTests.test_light_review_keeps_brief_and_checklist_together) ... ok
test_unsafe_large_and_missing_linked_documents_are_visible_errors (test_artifacts.ArtifactTests.test_unsafe_large_and_missing_linked_documents_are_visible_errors) ... ok
test_saved_selection_explains_restart_and_preserves_config_path (test_cli.SelectionTests.test_saved_selection_explains_restart_and_preserves_config_path) ... ok
test_existing_symlink_is_not_followed (test_install_skill.InstallSkillTests.test_existing_symlink_is_not_followed) ... ok
test_failed_copy_leaves_no_partial_installation (test_install_skill.InstallSkillTests.test_failed_copy_leaves_no_partial_installation) ... fatal: cannot change to '/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpudoec2u5/missing': No such file or directory
ok
test_independent_copy_and_repeat_preserves_destination (test_install_skill.InstallSkillTests.test_independent_copy_and_repeat_preserves_destination) ... ok
test_installed_agents_md_names_only_packaged_paths (test_install_skill.InstallSkillTests.test_installed_agents_md_names_only_packaged_paths) ... ok
test_package_instructions_drop_workspace_blocks (test_install_skill.InstallSkillTests.test_package_instructions_drop_workspace_blocks) ... ok
test_empty_or_failed_text_stays_unavailable (test_legacy_status.LegacyStatusTests.test_empty_or_failed_text_stays_unavailable) ... ok
test_explicit_unsupported_json_shows_text_without_inferred_approval (test_legacy_status.LegacyStatusTests.test_explicit_unsupported_json_shows_text_without_inferred_approval) ... ok
test_other_errors_and_bad_json_never_fall_back (test_legacy_status.LegacyStatusTests.test_other_errors_and_bad_json_never_fall_back) ... ok
test_untrusted_runtime_is_never_called (test_legacy_status.LegacyStatusTests.test_untrusted_runtime_is_never_called) ... ok
test_exact_head_success_for_each_fixed_source (test_prepare.EligibilityTests.test_exact_head_success_for_each_fixed_source) ... ok
test_newer_pending_attempt_does_not_accept_old_success (test_prepare.EligibilityTests.test_newer_pending_attempt_does_not_accept_old_success) ... ok
test_pending_failed_wrong_head_or_missing_ci_never_falls_back (test_prepare.EligibilityTests.test_pending_failed_wrong_head_or_missing_ci_never_falls_back) ... ok
test_dirty_new_target_and_existing_unrecorded_run_refused (test_prepare.PrepareTests.test_dirty_new_target_and_existing_unrecorded_run_refused) ... ok
test_failed_ci_and_smoke_leave_target_untouched (test_prepare.PrepareTests.test_failed_ci_and_smoke_leave_target_untouched) ... ok
test_integrity_failure_refuses_resume (test_prepare.PrepareTests.test_integrity_failure_refuses_resume) ... ok
test_main_moving_during_smoke_refuses_start (test_prepare.PrepareTests.test_main_moving_during_smoke_refuses_start) ... ok
test_new_run_records_exact_objects_and_resume_is_offline (test_prepare.PrepareTests.test_new_run_records_exact_objects_and_resume_is_offline) ... {"protocol": "tink-sdlc", "api_version": 1, "workspace": "/private/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmp4j14en2b/target", "run": {"slug": "trial", "meta": {"profile": "light", "kind": "feature"}, "gates": [{"stage": 3, "status": "pending", "blocked": false}], "verification_status": "blocked", "has_lock": false, "verification": null, "checklist": [], "checklist_state": "empty", "next_action": "revise/review stage 3; record the human decision.", "errors": [], "verification_config": {"require_tink": false, "checks": [{"argv": ["python3", "-B", "-c", "import unittest; s=unittest.defaultTestLoader.discover('tests'); assert s.countTestCases() > 0, 'No tests discovered'; r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())"], "timeout_seconds": 180}]}, "actions": {"verify": {"allowed": false, "reason": "revise/review stage 3; record the human decision.", "timeout_seconds": null}, "mark": {"allowed": false, "reason": "revise/review stage 3; record the human decision."}}, "artifacts": {"brief": "# Change brief\n\n## Problem and outcome\n\n## Acceptance criteria\n\n## Approach\n\nThe implementation checklist lives in `checklist.json` (definitions with id/description/verify) and is marked only with `sdlc.py mark`. Give an item a `check` (argv + timeout) whenever an automated proof exists; `verify` then runs it and no mark is needed.\n\n## Risks and verification\n"}, "decisions": [], "log": {"path": "runs/trial/04-test/output/test-log.md", "text": "", "truncated": false}, "cli_status": "Stage 3: pending\nNext: revise/review stage 3; record the human decision.\nAfter human review, fill in this command from the scaffold root (DECISION: approved or changes-requested):\n  python3 _system/scripts/sdlc.py decide trial 3 DECISION --reviewer 'REVIEWER' --source 'SOURCE' --reason 'REASON'\nChecklist: no items defined\nVerification: not run (implementation may be pending; a text log is not passing evidence)\nDeployment: not inferred from local review files; consult the deployment system."}}
ok
test_package_internal_symlink_is_refused_on_resume (test_prepare.PrepareTests.test_package_internal_symlink_is_refused_on_resume) ... ok
test_package_storage_inside_target_refused (test_prepare.PrepareTests.test_package_storage_inside_target_refused) ... ok
test_record_from_other_checkout_and_symlink_refused (test_prepare.PrepareTests.test_record_from_other_checkout_and_symlink_refused) ... ok
test_second_run_cannot_replace_first_runs_workflow (test_prepare.PrepareTests.test_second_run_cannot_replace_first_runs_workflow) ... ok
test_stage_launch_stays_in_checkout_and_carries_saved_tool_instructions (test_prepare.PrepareTests.test_stage_launch_stays_in_checkout_and_carries_saved_tool_instructions) ... skills: skipped (tink not installed); the agent will run without stage disciplines
warning: PR delivery may not be possible from this checkout: there is no `origin` remote. If this is still true at the end, hand the owner these commands instead of stopping silently: git push -u origin trial; gh pr create --fill
Checkout: /private/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpa8_pbwsl/target
Launch prompt (start a NEW session there):
Begin stage 3 (build) of SDLC run `trial`.
ok
test_target_customization_and_required_tink_refuse_start (test_prepare.PrepareTests.test_target_customization_and_required_tink_refuse_start) ... ok
test_target_runtime_changed_refuses_resume (test_prepare.PrepareTests.test_target_runtime_changed_refuses_resume) ... ok
test_unrecorded_extra_package_file_refuses_resume (test_prepare.PrepareTests.test_unrecorded_extra_package_file_refuses_resume) ... ok
test_workflow_cannot_mutate_a_different_run_or_use_global_tools (test_prepare.PrepareTests.test_workflow_cannot_mutate_a_different_run_or_use_global_tools) ... ok
test_workflow_keeps_project_tool_path_while_disabling_optional_discovery (test_prepare.PrepareTests.test_workflow_keeps_project_tool_path_while_disabling_optional_discovery) ... Configured checks passed for the recorded candidate. Human release review remains required.
ok
test_agent_status_reports_age_and_server_errors (test_server.ServerTests.test_agent_status_reports_age_and_server_errors) ... ok
test_failed_refresh_stays_visible_to_later_readers (test_server.ServerTests.test_failed_refresh_stays_visible_to_later_readers) ... ok
test_invalid_config_refresh_reports_error_not_old_success (test_server.ServerTests.test_invalid_config_refresh_reports_error_not_old_success) ... ok
test_no_arbitrary_files_or_cross_site_reads (test_server.ServerTests.test_no_arbitrary_files_or_cross_site_reads) ... ok
test_page_and_agents_share_snapshot_until_explicit_refresh (test_server.ServerTests.test_page_and_agents_share_snapshot_until_explicit_refresh) ... ok
test_record_edit_shows_after_refresh_without_restart (test_server.ServerTests.test_record_edit_shows_after_refresh_without_restart) ... ok
test_security_headers_and_no_inline_scripts (test_server.ServerTests.test_security_headers_and_no_inline_scripts) ... ok
test_current_pin_tells_agents_to_use_json (test_skill_read_guidance.BundledGuidanceTests.test_current_pin_tells_agents_to_use_json) ... ok
test_old_pin_has_the_bug (test_skill_read_guidance.BundledGuidanceTests.test_old_pin_has_the_bug) ... ok
test_accepts_json_payload_either_order (test_skill_read_guidance.ScannerTests.test_accepts_json_payload_either_order) ... ok
test_flags_payload_without_json (test_skill_read_guidance.ScannerTests.test_flags_payload_without_json) ... ok
test_ignores_plain_mount (test_skill_read_guidance.ScannerTests.test_ignores_plain_mount) ... ok
test_artifact_escape_and_symlink_rejected (test_sources.ContractTests.test_artifact_escape_and_symlink_rejected) ... ok
test_ci_empty_pending_skipped_and_unknown_never_pass (test_sources.ContractTests.test_ci_empty_pending_skipped_and_unknown_never_pass) ... ok
test_current_requires_passing_receipt_and_known_identity (test_sources.ContractTests.test_current_requires_passing_receipt_and_known_identity) ... ok
test_hunch_record_without_links_reads_as_not_linked (test_sources.ContractTests.test_hunch_record_without_links_reads_as_not_linked) ... ok
test_invalid_and_external_pr_urls_rejected (test_sources.ContractTests.test_invalid_and_external_pr_urls_rejected) ... ok
test_merged_pr_is_distinct_from_closed_and_preserves_other_warnings (test_sources.ContractTests.test_merged_pr_is_distinct_from_closed_and_preserves_other_warnings) ... ok
test_pr_head_mismatch_and_verification_staleness_surface (test_sources.ContractTests.test_pr_head_mismatch_and_verification_staleness_surface) ... ok
test_pr_review_state_is_specific (test_sources.ContractTests.test_pr_review_state_is_specific) ... ok
test_sdlc_errors_and_pending_human_decisions_surface (test_sources.ContractTests.test_sdlc_errors_and_pending_human_decisions_surface) ... ok
test_source_failure_does_not_hide_other_sources (test_sources.ContractTests.test_source_failure_does_not_hide_other_sources) ... ok
test_workflow_requires_explicit_trust_and_does_not_execute_by_discovery (test_sources.ContractTests.test_workflow_requires_explicit_trust_and_does_not_execute_by_discovery) ... ok
test_clean_dirty_and_other_worktrees (test_sources.GitTests.test_clean_dirty_and_other_worktrees) ... ok
test_detached_head_and_invalid_checkout (test_sources.GitTests.test_detached_head_and_invalid_checkout) ... ok
test_missing_worktree_is_unknown_not_clean (test_sources.GitTests.test_missing_worktree_is_unknown_not_clean) ... ok
test_rename_spaces_and_newline_paths (test_sources.GitTests.test_rename_spaces_and_newline_paths) ... ok
test_built_package_console_module_and_metadata_outside_source (test_version.VersionTests.test_built_package_console_module_and_metadata_outside_source) ... ok
test_help_and_missing_subcommand (test_version.VersionTests.test_help_and_missing_subcommand) ... ok
test_missing_malformed_and_selected_config_unchanged (test_version.VersionTests.test_missing_malformed_and_selected_config_unchanged) ... ok
test_source_ignores_other_distribution_version (test_version.VersionTests.test_source_ignores_other_distribution_version) ... ok
test_source_version_without_config_or_subcommand (test_version.VersionTests.test_source_version_without_config_or_subcommand) ... ok
test_version_exits_before_reading_config_or_running_commands (test_version.VersionTests.test_version_exits_before_reading_config_or_running_commands) ... ok
test_mount_hints_use_json (test_workspace_guidance.WorkspaceGuidanceTests.test_mount_hints_use_json) ... ok
test_workspace_files_present (test_workspace_guidance.WorkspaceGuidanceTests.test_workspace_files_present) ... ok

----------------------------------------------------------------------
Ran 72 tests in 19.744s

OK

# checklist item refresh-boundaries
$ ["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_prepare*.py", "-v"]
test_exact_head_success_for_each_fixed_source (test_prepare.EligibilityTests.test_exact_head_success_for_each_fixed_source) ... ok
test_newer_pending_attempt_does_not_accept_old_success (test_prepare.EligibilityTests.test_newer_pending_attempt_does_not_accept_old_success) ... ok
test_pending_failed_wrong_head_or_missing_ci_never_falls_back (test_prepare.EligibilityTests.test_pending_failed_wrong_head_or_missing_ci_never_falls_back) ... ok
test_dirty_new_target_and_existing_unrecorded_run_refused (test_prepare.PrepareTests.test_dirty_new_target_and_existing_unrecorded_run_refused) ... ok
test_failed_ci_and_smoke_leave_target_untouched (test_prepare.PrepareTests.test_failed_ci_and_smoke_leave_target_untouched) ... ok
test_integrity_failure_refuses_resume (test_prepare.PrepareTests.test_integrity_failure_refuses_resume) ... ok
test_main_moving_during_smoke_refuses_start (test_prepare.PrepareTests.test_main_moving_during_smoke_refuses_start) ... ok
test_new_run_records_exact_objects_and_resume_is_offline (test_prepare.PrepareTests.test_new_run_records_exact_objects_and_resume_is_offline) ... {"protocol": "tink-sdlc", "api_version": 1, "workspace": "/private/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpfs1mh_q5/target", "run": {"slug": "trial", "meta": {"profile": "light", "kind": "feature"}, "gates": [{"stage": 3, "status": "pending", "blocked": false}], "verification_status": "blocked", "has_lock": false, "verification": null, "checklist": [], "checklist_state": "empty", "next_action": "revise/review stage 3; record the human decision.", "errors": [], "verification_config": {"require_tink": false, "checks": [{"argv": ["python3", "-B", "-c", "import unittest; s=unittest.defaultTestLoader.discover('tests'); assert s.countTestCases() > 0, 'No tests discovered'; r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())"], "timeout_seconds": 180}]}, "actions": {"verify": {"allowed": false, "reason": "revise/review stage 3; record the human decision.", "timeout_seconds": null}, "mark": {"allowed": false, "reason": "revise/review stage 3; record the human decision."}}, "artifacts": {"brief": "# Change brief\n\n## Problem and outcome\n\n## Acceptance criteria\n\n## Approach\n\nThe implementation checklist lives in `checklist.json` (definitions with id/description/verify) and is marked only with `sdlc.py mark`. Give an item a `check` (argv + timeout) whenever an automated proof exists; `verify` then runs it and no mark is needed.\n\n## Risks and verification\n"}, "decisions": [], "log": {"path": "runs/trial/04-test/output/test-log.md", "text": "", "truncated": false}, "cli_status": "Stage 3: pending\nNext: revise/review stage 3; record the human decision.\nAfter human review, fill in this command from the scaffold root (DECISION: approved or changes-requested):\n  python3 _system/scripts/sdlc.py decide trial 3 DECISION --reviewer 'REVIEWER' --source 'SOURCE' --reason 'REASON'\nChecklist: no items defined\nVerification: not run (implementation may be pending; a text log is not passing evidence)\nDeployment: not inferred from local review files; consult the deployment system."}}
ok
test_package_internal_symlink_is_refused_on_resume (test_prepare.PrepareTests.test_package_internal_symlink_is_refused_on_resume) ... ok
test_package_storage_inside_target_refused (test_prepare.PrepareTests.test_package_storage_inside_target_refused) ... ok
test_record_from_other_checkout_and_symlink_refused (test_prepare.PrepareTests.test_record_from_other_checkout_and_symlink_refused) ... ok
test_second_run_cannot_replace_first_runs_workflow (test_prepare.PrepareTests.test_second_run_cannot_replace_first_runs_workflow) ... ok
test_stage_launch_stays_in_checkout_and_carries_saved_tool_instructions (test_prepare.PrepareTests.test_stage_launch_stays_in_checkout_and_carries_saved_tool_instructions) ... skills: skipped (tink not installed); the agent will run without stage disciplines
warning: PR delivery may not be possible from this checkout: there is no `origin` remote. If this is still true at the end, hand the owner these commands instead of stopping silently: git push -u origin trial; gh pr create --fill
Checkout: /private/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpj5emz4k7/target
Launch prompt (start a NEW session there):
Begin stage 3 (build) of SDLC run `trial`.
ok
test_target_customization_and_required_tink_refuse_start (test_prepare.PrepareTests.test_target_customization_and_required_tink_refuse_start) ... ok
test_target_runtime_changed_refuses_resume (test_prepare.PrepareTests.test_target_runtime_changed_refuses_resume) ... ok
test_unrecorded_extra_package_file_refuses_resume (test_prepare.PrepareTests.test_unrecorded_extra_package_file_refuses_resume) ... ok
test_workflow_cannot_mutate_a_different_run_or_use_global_tools (test_prepare.PrepareTests.test_workflow_cannot_mutate_a_different_run_or_use_global_tools) ... ok
test_workflow_keeps_project_tool_path_while_disabling_optional_discovery (test_prepare.PrepareTests.test_workflow_keeps_project_tool_path_while_disabling_optional_discovery) ... Configured checks passed for the recorded candidate. Human release review remains required.
ok

----------------------------------------------------------------------
Ran 18 tests in 10.103s

OK

# checklist item package-regressions
$ ["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_install_skill.py", "-v"]
test_existing_symlink_is_not_followed (test_install_skill.InstallSkillTests.test_existing_symlink_is_not_followed) ... ok
test_failed_copy_leaves_no_partial_installation (test_install_skill.InstallSkillTests.test_failed_copy_leaves_no_partial_installation) ... fatal: cannot change to '/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpo31f9q9h/missing': No such file or directory
ok
test_independent_copy_and_repeat_preserves_destination (test_install_skill.InstallSkillTests.test_independent_copy_and_repeat_preserves_destination) ... ok
test_installed_agents_md_names_only_packaged_paths (test_install_skill.InstallSkillTests.test_installed_agents_md_names_only_packaged_paths) ... ok
test_package_instructions_drop_workspace_blocks (test_install_skill.InstallSkillTests.test_package_instructions_drop_workspace_blocks) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.125s

OK
