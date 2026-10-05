
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
test_failed_copy_leaves_no_partial_installation (test_install_skill.InstallSkillTests.test_failed_copy_leaves_no_partial_installation) ... fatal: cannot change to '/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmp9_h0lg15/missing': No such file or directory
ok
test_independent_copy_and_repeat_preserves_destination (test_install_skill.InstallSkillTests.test_independent_copy_and_repeat_preserves_destination) ... ok
test_empty_or_failed_text_stays_unavailable (test_legacy_status.LegacyStatusTests.test_empty_or_failed_text_stays_unavailable) ... ok
test_explicit_unsupported_json_shows_text_without_inferred_approval (test_legacy_status.LegacyStatusTests.test_explicit_unsupported_json_shows_text_without_inferred_approval) ... ok
test_other_errors_and_bad_json_never_fall_back (test_legacy_status.LegacyStatusTests.test_other_errors_and_bad_json_never_fall_back) ... ok
test_untrusted_runtime_is_never_called (test_legacy_status.LegacyStatusTests.test_untrusted_runtime_is_never_called) ... ok
test_agent_status_reports_age_and_server_errors (test_server.ServerTests.test_agent_status_reports_age_and_server_errors) ... ok
test_failed_refresh_stays_visible_to_later_readers (test_server.ServerTests.test_failed_refresh_stays_visible_to_later_readers) ... ok
test_invalid_config_refresh_reports_error_not_old_success (test_server.ServerTests.test_invalid_config_refresh_reports_error_not_old_success) ... ok
test_no_arbitrary_files_or_cross_site_reads (test_server.ServerTests.test_no_arbitrary_files_or_cross_site_reads) ... ok
test_page_and_agents_share_snapshot_until_explicit_refresh (test_server.ServerTests.test_page_and_agents_share_snapshot_until_explicit_refresh) ... ok
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
Ran 51 tests in 9.282s

OK

# checklist item workspace-guidance-test
$ ["python3", "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_workspace_guidance.py", "-v"]
test_mount_hints_use_json (test_workspace_guidance.WorkspaceGuidanceTests.test_mount_hints_use_json) ... ok
test_workspace_files_present (test_workspace_guidance.WorkspaceGuidanceTests.test_workspace_files_present) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK

# checklist item receipt-1-18-3
$ ["python3", "-B", "-c", "import json,sys; v=json.load(open('_system/scaffold.json'))['version']; sys.exit(0 if v=='1.18.3' else 'version is '+v)"]

# checklist item walk-passes
$ ["python3", "-B", "_system/scripts/sdlc.py", "walk"]
PASS W1 entry-file: AGENTS.md is a router (51 lines outside generated blocks; generated block 534 bytes (cap 8192))
PASS W2 pointers-resolve: 35 pointers resolve
PASS W3 stage-contracts: 6 stage contracts name inputs, output, and gate
PASS W4 token-budget: largest stage context ~1667 tokens
PASS W5 skillsets-consistent: 6 pins, all named and present
PASS W6 status-derivable: status derivable for 3 run(s)
PASS W7 rules-block-current: rules block current for build-skillset
  tokens 01-plan: ~1601
  tokens 02-design: ~1471
  tokens 03-build: ~1528
  tokens 04-test: ~1505
  tokens 05-deploy: ~1667
  tokens 06-maintain: ~1403
Walk: 7 passed, 0 warned, 0 failed

# checklist item verification-config-unchanged
$ ["git", "diff", "--exit-code", "--quiet", "origin/main", "--", "_system/verification.json"]

# checklist item history-preserved
$ ["git", "diff", "--exit-code", "--quiet", "origin/main", "--", "runs/skill-read-guidance", "runs/version-option"]
