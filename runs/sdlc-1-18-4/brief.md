# Change brief

## Problem and outcome

tink-sdlc 1.18.4 is merged (jon-devlapaz/tink-sdlc#44, `f730e131557d8e3ba8a1e83b656855f7feaec585`). Its only code change from 1.18.3 is `assets/_system/scripts/sdlc.py`: the stage-open skill pick keeps the router's `reason`, and non-object router output is treated as unreadable.

Outcome: Substrate bundles and uses 1.18.4. Its installer pin, its docs and its own workspace all say 1.18.4, and nothing else changes.

## Acceptance criteria

1. `scripts/install_skill.py` `PINS['tink-sdlc']` revision is `f730e131557d8e3ba8a1e83b656855f7feaec585`. The `tink-skills` pin is unchanged.
2. `docs/start-a-change.md` (lines 65 and 257) and `docs/new-user-validation.md` (line 12) name 1.18.4 / `f730e13` where they describe the current pin. The validation doc still says plainly what was validated at which pin (1.18.2); it is not rewritten to claim 1.18.4 was validated.
3. This repo's workspace is upgraded with `init.py --upgrade` from a clean `git archive` export of tink-sdlc at `f730e13`. `_system/scaffold.json` reports 1.18.4 and `_system/scripts/sdlc.py` matches the pin. No stage `CONTEXT.md` changes, so this run's approval stays current.
4. Nothing else differs from origin/main except this run's own files: `_system/verification.json`, other runs and tests are untouched.
5. `sdlc.py walk` stays 7/7; the project gate (unittest discovery, including `tests/test_skill_read_guidance.py` at the new pin) passes.

## Approach

- Edit the pin string and the three doc lines. No test needs editing: `tests/test_install_skill.py` patches `PINS`, and `tests/test_skill_read_guidance.py` reads the pin from `PINS`.
- Export tink-sdlc at `f730e13` into the coordinator's scratchpad, run `init.py <worktree> --upgrade --check`, confirm the plan is `Update: _system/scripts/sdlc.py` plus the receipt only, then `--upgrade`.
- Run the project gate and walk.

Out of scope, follow-ups only: (a) reinstalling `~/.codex/skills/tink-substrate` from merged main, which needs the user to authorize the merge; (b) upgrading other tink-sdlc workspaces (the 1.19.0 product checkouts, 1.18.2 main checkouts, 1.0.1 boards), which was inventoried in the handoff and needs the user's decision.

## Risks and verification

- Pin typo or wrong commit: the check compares the exact string, and the sdlc.py check compares bytes against `git show f730e13:...` in the local tink-sdlc clone.
- Upgrade touches more than expected: preview with `--check` first; a diff-name check limits changes to the allowed file set.
- Docs overclaim: wording kept to what was actually validated.
- `AGENTS.md` shows a modified `tink:rules` block from stage open; it is generated, excluded from the candidate fingerprint, and not part of this change.
- Attested (not auto-checkable here): a real stage open with `TYPESAFE_API_KEY` unset in a disposable clone prints `skill pick: skipped (router exited 2: no_api_key)` and the pick receipt has `reason`; and `install_skill.py` into a temp dir with `--tool-cache`, then its `scripts/check_install.py`, passes.

The implementation checklist lives in `checklist.json` (definitions with id/description/verify) and is marked only with `sdlc.py mark`. Give an item a `check` (argv + timeout) whenever an automated proof exists; `verify` then runs it and no mark is needed.
