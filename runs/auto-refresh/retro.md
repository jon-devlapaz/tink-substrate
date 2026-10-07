# Retrospective: automatic dogfood tool refresh

Outcome: [PR #17](https://github.com/jon-devlapaz/tink-substrate/pull/17), awaiting human review and merge. New prepared runs refresh Substrate, Seed Me and SDLC at the run boundary; resumes retain a checked package. Version 0.2.0. No existing installation was replaced.

## Human decisions
The user reviewed the pre-run-refresh proposal, then explicitly asked for a branch, implementation, commit and clean PR using Features and Futures. That instruction was recorded under Stage 03's execution-of-reviewed-proposal rule. No merge authorization was supplied.

## Evidence and limits
- 72 project tests passed. SDLC verify is current; both automated checklist checks passed. Generated log: `04-test/output/test-log.md`.
- `evidence/live-source.json`: current successful-CI exports of public Substrate, Seed Me 2.0.0 and SDLC 1.21.0 passed simulated-session, API, dashboard and unapproved-verification checks. Re-run with `python3 -B tests/check_current_tools.py --out /tmp/current-tools.json`.
- `evidence/candidate-run.json`: the committed candidate with real checked Seed Me and SDLC exports prepared a synthetic target, resumed from the copied package without GitHub on PATH, opened stage 1 with saved-tool instructions, and retained a blocked human gate. The test explicitly selected candidate Substrate code; production never bypasses CI. Re-run with `python3 -B tests/check_candidate_run.py --out /tmp/candidate-run.json`.
- Independent fresh review found three concrete defects. Tests and a bounded recheck resolved all three. See `05-deploy/output/REVIEW-findings.md`. Model review is advisory, not code-owner approval.
- No real human interview or completed customer change was performed. Optional Tink/router provisioning is outside this slice. External packages must remain available for offline resume; the archive preserves their version record, not those external directories.

## Failures and repairs
- Initial PATH isolation hid a project check executable. Reproduced with a temporary project tool, then limited suppression to SDLC's optional tool discovery. Project checks retain PATH.
- Workflow digest initially included project-owned verification settings. Kept managed files fixed while allowing SDLC's normal reviewed check configuration.
- Independent review reproduced default stage worktrees losing identity, a second run replacing an earlier scaffold, and fresh stage prompts losing package instructions. The wrapper stays in the prepared checkout, refuses a second prepared run there and carries the complete saved-tool prompt.
- Live main advanced while CI was pending. Preparation correctly refused; no old-head fallback was used. Later checked sources passed.
- Concurrent upstream documentation changes required a rebase. Preserved the newer package instruction trimming and onboarding changes.

## Features and Futures
Learning: freshness belongs at preparation; stability belongs to each run. The next change became safer because one package builder owns export and hashing for both fixed installs and automatically resolved sources.
Decision: stop consolidating. The demonstrated run-boundary defects are resolved. No background updater or global-tool installer was added.
Next: human review and merge. Then observe one actual human-answered dogfood run from the installed entry skill, including interruption and resume. Record interventions before choosing another slice.
