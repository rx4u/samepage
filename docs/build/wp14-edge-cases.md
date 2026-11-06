# WP-14 edge cases ledger

Every edge case named in the architecture, with the test that proves it or the recorded manual check. Run date 2026-11-06.

| Edge case | Source | Proof |
|---|---|---|
| Concurrent write conflict from Code (pull conflict) | B9 | `test_pull_conflict_stops_and_writes_nothing` |
| Remote has newer entries before a write | B9 | `test_pull_brings_remote_entries_first` |
| Push fails (offline) after a local commit | contract | `test_push_failure_keeps_commit` |
| Invalid entry never lands; store unchanged | ADR-0007 | `test_check_failure_rolls_back`, `test_invalid_entry_is_not_written` |
| Dry run writes nothing; confirmed write matches the preview | ADR-0007 | `test_dry_run_writes_nothing_and_pins_reproduce_it`; manual: real Claude Code `/sp log` showed dry run id 57e9454a, store unchanged until "yes", written file had the same id, commit reached the remote |
| Two surfaces editing the same project file from chat (sha mismatch) | consistency table | Skill `references/github-backend.md` (re-read, re-apply once, then ask). Not executable in tests; chat connector writes are blocked on the owner's account until A2 is resolved |
| uuid prefix collision | B12 | `test_collision_regenerates_id` |
| Duplicate ids across files | B12 | `test_broken_cases_fail_on_named_field` (duplicate-id) |
| Slug equal to a tag slug | test-data | fixtures/small project `ai` and tag `ai`; `test_small_store_passes`; perf fixture has 3 such slugs |
| Archive instead of delete | US-14 | `test_project_show_and_archive` |
| Supersede chains and wrong supersede targets | US-12 | `test_decision_and_supersede`, `test_supersede_failures` |
| Handoff to design rejected | B7 | `test_rejects_design_and_unknown`, broken case handoff-to-design |
| Stale index at boot | monitoring | `test_stale_index_warning` |
| Store pull hangs at boot | targets | Manual: hung upload-pack, boot returned cached context in 2.01 s on Python 3.13 and 3.11, no leftover processes |
| No config, Notion config, missing index | US-03 | `test_no_config`, `test_notion_backend_points_to_skill`, `test_missing_index` |
| Boot budget with maximum-length content | targets | `test_perf_fixture_targets` (largest boot 7,909 of 8,000) |
| More than 20 rules for one surface, more than 50 active | B3 | `sp check` warning and error paths; perf fixture triggers the 20-rule warning case for code |
| Secrets and card numbers, without false positives on uuids | ADR-0007 | `test_patterns`, broken cases secret-in-body and card-number; perf fixture passes with 8,290 uuids |
| Store Action: invalid store never commits an index | guardrails | Manual on rx4u/samepage-demo: invalid edit 518dd9da failed the run, no index commit; revert rebuilt in 13 s |
| Store Action skips its own commits | ADR-0004 | `test_skips_its_own_commits`; manual: index commits started no runs |
| Stop nudge reaches the user | WP-08 | `test_hook_script_prints_one_line_or_nothing` (systemMessage JSON, per the Claude Code hooks reference) |
| Project with shipped work but no public proof | US-07 | `test_proof_excludes_general_and_marks_missing_proof` (vault-cli) |
