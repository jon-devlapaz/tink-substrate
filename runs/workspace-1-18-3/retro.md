# Retrospective: workspace-1-18-3

Outcome: PR https://github.com/jon-devlapaz/tink-substrate/pull/4 (not merged). This repo's
own workspace moves from tink-sdlc 1.18.2 to 1.18.3 (3b175bb). Agents here now read
`tink mount <skill> --json --payload`, in SDLC.md, the launch prompt and the AGENTS.md rules.

## Human decisions
- Asked for an explanation first; after it, approved proceeding ("Yes").
- Approved the brief before the upgrade, and re-approved the same brief after the upgrade
  staled that approval. Merge not authorized yet.

## Evidence and its limits
- Automated: new locked test (failed on main at SDLC.md:91 and sdlc.py:1122, passes now);
  project gate 51 tests; `walk` 7/7 (W7 failed on main); `sdlc.py verify` current;
  checklist 8/8 (5 by check, 3 attested). Logs: `evidence/`, `04-test/output/`.
- Launch prompt: proven with a stub router in a disposable clone, plus the printed command
  run against real tink 1.0.50 (exit 0). The real router never routed, so a real stage open
  printed no pick line (`evidence/stage-5-open.txt`); the AGENTS.md rules compiled at that
  open do read `--json --payload`.
- Model reviews (repro and PR): ACCEPT. Advisory only; CI and the human merge decide release.
- The test checks text only. It does not prove an agent follows the hint.

## Failures and repairs
- Planner wrote `stage --check` for the launch-prompt check; `--check` never prints the pick.
  Fixed in the checklist before approval.
- First stub-router attempt failed: the pyenv shim puts its own `tink-route` before the stub on
  PATH. Calling the interpreter by absolute path fixed it.
- A misread of combined `git status` output briefly looked like the stage-5 open dirtied this
  checkout; it had only touched the review worktree.

## Manual interventions
- Approvals were typed by the human in chat and recorded by the coordinator with that source.

## What made this easier or harder
- Easier: `init.py --upgrade --check` gave an exact, honest preview, including the stale-run warning.
- Harder: approvals hash every stage contract, so a scaffold upgrade always costs a second
  human approval inside its own run. Expected by design; worth knowing up front.
- Harder: `tink-route --pick` fails with `no_api_key`, so stage-open picks never appear here.
  A hint on that path can only be tested with a stub.

## Smallest justified next step
- Merge #4 once CI is green and the human authorizes it.
- Optional, separate: configure the tink-route API key, or accept routing as off. No workflow
  change is justified by this run.
- Review nit noted for a future reviewed replacement of the locked test: assert all six stage
  contracts exist.
