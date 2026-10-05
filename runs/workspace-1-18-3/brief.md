# Change brief

## Problem and outcome

Agents working inside this repo read hints that say `tink mount <skill> --payload`. Tink rejects that command (exit 2) unless it also gets `--json`. The repo's own workspace files (`_system/SDLC.md`, `_system/scripts/sdlc.py`) still carry the 1.18.2 text. tink-sdlc 1.18.3 (commit 3b175bb, merge of jon-devlapaz/tink-sdlc#43) fixes the hint.

Outcome: this repo's workspace is on 1.18.3, and every hint in it reads `tink mount <skill> --json --payload`.

Reproduction of the stale hint (on main 0fd38d7, today):
- `grep -n 'tink mount .*--payload' _system/SDLC.md _system/scripts/sdlc.py` shows line 91 of SDLC.md and line 1122 of sdlc.py with no `--json`.
- `tink mount unslop --payload` exits 2; `tink mount unslop --json --payload` returns the skill.
- The new offline test (below) fails on these files and passes after the upgrade.

## Acceptance criteria

1. `_system/SDLC.md`, `_system/scripts/sdlc.py`, `stages/04-test/CONTEXT.md` and the receipt `_system/scaffold.json` are updated from 1.18.2 to 1.18.3, using the installed package (`~/.codex/skills/tink-substrate/.substrate-tools/tink-sdlc`, revision 3b175bb) with `init.py --upgrade --check`, then `--upgrade`. The router block in AGENTS.md is unchanged; project-owned files are kept.
2. The `tink:rules` block in AGENTS.md is refreshed with installed tink (`tink use build-skillset`). It already reads `--json --payload` in this worktree (the stage-1 launcher refreshed it); that edit ships in the PR. `sdlc.py walk` W7 (stale rules block) passes.
3. A new offline test, `tests/test_workspace_guidance.py`, scans this repo's own `_system/SDLC.md`, `_system/scripts/sdlc.py`, `stages/*/CONTEXT.md` and `AGENTS.md` for `tink mount ... --payload` without `--json`. It reuses `bad_mount_hints` from `tests/test_skill_read_guidance.py`. It fails on today's files and passes after the upgrade.
4. `_system/verification.json` is not changed. Existing runs under `runs/` are not changed.
5. Real check, after the upgrade: open a stage and confirm the launch prompt and SDLC.md print `--json --payload` (see Verification).

## Approach

1. Build the test first and show it failing on the unfixed files. Lock it with `sdlc.py lock-tests` once a reviewer accepts the reproduction (bug runs cannot verify without a lock).
2. Run the upgrade preview, then apply it. Expected changes are exactly the four files in criterion 1.
3. Run `tink use build-skillset` to refresh the rules block (AGENTS.md).
4. Run the test, `sdlc.py walk`, and `sdlc.py verify`.
5. Add no new dependency and no new gate.

Approval and history:
- The upgrade changes `stages/04-test/CONTEXT.md` and SDLC.md, so this run's own stage-3 approval goes stale when the upgrade lands. The human re-approves the same brief after the upgrade lands.
- Historical runs `version-option` and `skill-read-guidance` will read stale. That is expected. They are not re-approved.

## Risks and verification

- Risk: a managed file is customized and blocks the upgrade. Baseline shows every managed hash matches the 1.18.2 receipt, so none is expected.
- Risk: the stage-open pick rarely routes (past opens: 0 routed), so the launch prompt may print no mount line. The launch-prompt check therefore uses a stub `tink-route` on PATH in a disposable clone (never in this checkout), then runs the printed command with real tink.
- Risk: the new test only checks text in files. It does not prove an agent follows the hint; the real-tink run of the printed command covers that.
- Verification: the repo gate `_system/verification.json` (unittest discovery over `tests/`) is unchanged and runs through `sdlc.py verify`. Checklist items carry automated checks where a real proof exists; three items are attested (see checklist).
