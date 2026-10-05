# Handoff: sdlc-1-18-4

## User request (verbatim)

> merge #44 and upgrade to 1.18.4 and upgrade everything that needs updating please

## User decisions

- 2026-10-05: "merge #44" -> merged jon-devlapaz/tink-sdlc#44 as f730e131557d8e3ba8a1e83b656855f7feaec585 (CI 3.9/3.11/3.14 green, head 40c1579). tink-sdlc main is now 1.18.4.
- Merge of any tink-substrate PR still needs explicit authorization.

## Coordinator defaults (proposals, not user decisions)

- Run kind `feature`, profile `light`, worktree
  `/Users/jondev/dev/active/factory/working-copies/tink-substrate-sdlc-1-18-4`, branch `sdlc-1-18-4` from origin/main bebbeec.
- Seed Me triage: clear execution request; no interview, no seed.
- Scope in this repo:
  1. Move the Substrate pin `scripts/install_skill.py` PINS['tink-sdlc'] from 3b175bb (1.18.3) to f730e13 (1.18.4); update docs that name the pin (`docs/start-a-change.md:65,257`, `docs/new-user-validation.md:12`).
  2. Upgrade this repo's own workspace 1.18.3 -> 1.18.4 with `init.py --upgrade` from a package built at f730e13. Only `_system/scripts/sdlc.py` and the receipt change; no stage CONTEXT.md changes, so approvals do not go stale.
  3. After the PR merges (with user authorization): reinstall `~/.codex/skills/tink-substrate` from merged main using `scripts/install_skill.py` per the start guide (install to a review dir, validate, back up the old copy outside the skills dir, swap).
- Upgrade source for step 2: the installed skill still bundles 3b175bb, so use a clean export of tink-sdlc at f730e13 (git archive from the local clone into the scratchpad), not a mutable working copy.

## Inventory of other tink-sdlc workspaces (2026-10-05)

Not upgraded by this run; reported to the user for a decision.
- 1.19.0 (from unmerged tink-sdlc#42 `feat/runtime-api-1`): product/neon-tetris*, product/tink-arcade-* (12 checkouts). Lacks #43 and #44; init.py refuses 1.19.0 -> 1.18.4 as a downgrade. Needs #42 rebased onto main.
- 1.18.2 main checkouts, clean: boards/repo-root-tracker, factory/tink, factory/tink-skills (each has runs).
- Feature branches / other agents' worktrees (no upgrade during feature work): repo-root-tracker-commit-title-pipes, sdlc-cockpit (1.18.0, feat/tink-cockpit), working-copies/tink-patch-guidance (dirty), tink-skills-remove-engram, tink-substrate-skill-read-guidance.
- boards/groveboard and tink-skills-viewer-fix: version 1.0.1 (older package line).
