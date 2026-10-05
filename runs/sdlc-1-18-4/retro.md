# Retrospective: sdlc-1-18-4

Outcome: https://github.com/jon-devlapaz/tink-substrate/pull/5 (open, not merged). Substrate pins
tink-sdlc 1.18.4 (f730e13, merge of tink-sdlc#44, authorized by the user) and this repo's
workspace runs it. Companion upgrades, same source, separate PRs (user approved "yes"):
repo-root-tracker#27, tink#95, tink-skills#126.

## Human decisions
- "merge #44 and upgrade to 1.18.4 and upgrade everything that needs updating" -> #44 merged
  on green CI; one brief approval covering this run and the three companion PRs.
- Merges of #5, #27, #95 and #126 not yet authorized.

## Evidence and its limits
- Automated: checklist 8/8 (6 by check), verify current, walk 7/7, 51 tests. Independent
  review ACCEPT (05-deploy/output/REVIEW-findings.md).
- Real checks (real-checks.txt): with the key unset, a real stage open prints
  `router exited 2: no_api_key` and records the reason; a trial install from the branch
  validates and bundles f730e13.
- `sdlc-py-matches-pin` uses a local clone path; not reproducible on another machine.
- Companion repos: walk 7/7 each; tink-skills 310 tests locally. repo-root-tracker (pytest
  after `pip install -e .`) and tink (cargo) were left to CI to avoid changing the global
  Python environment and a long Rust build; their diffs touch no product code.

## Failures and repairs
- Two shell slips (zsh `$b:a` path modifier; unsplit file list) caught before any commit.

## What made this easier or harder
- Easier: approval did not go stale, because only sdlc.py changed. The inventory found every
  workspace on disk in one pass.
- Harder: 12 product checkouts run 1.19.0 from unmerged tink-sdlc#42 and lack #43/#44.
  `init.py` refuses 1.19.0 -> 1.18.4. They stay stale until #42 is rebased onto main.

## Smallest justified next step
- Merge #5, then reinstall `~/.codex/skills/tink-substrate` from main.
- Merge #27, #95, #126 after CI.
- Rebase tink-sdlc#42 onto main (picks up #43 and #44), then upgrade the 1.19.0 checkouts.
- Left alone on purpose: feature-branch worktrees (pick up the fix when they merge) and the
  1.0.1 line (groveboard, tink-skills-viewer-fix).
