# Handoff: workspace-1-18-3

## User request (verbatim summary of the goal)

> Upgrade this repo's own tink-sdlc workspace (_system/, stages/, _shared/,
> .tink/skillsets/) from 1.18.2 to 1.18.3. 1.18.3 is tink-sdlc commit 3b175bb,
> the merge of jon-devlapaz/tink-sdlc#43. Agents working inside this repo still
> see the old hint `tink mount <skill> --payload`, which tink rejects without
> --json. The fixed scaffold is already bundled in the installed skill at
> ~/.codex/skills/tink-substrate/.substrate-tools/tink-sdlc.
>
> ... follow the substrate workflow: run, brief for my approval, isolated
> worktree, implement, verify, independent review, PR, retro and archive. Do not
> merge without my authorization. Preserve the existing runs/ evidence, Seed Me,
> and other agents' worktrees.
>
> Real check: open a stage in this repo afterwards and confirm the launch prompt
> and SDLC.md print `--json --payload`.

## User decisions

- 2026-10-05, coordinating Claude Code session: after the explanation, the user
  answered "Yes" to proceeding with the plan as explained, including the
  coordinator's recommendation to keep the AGENTS.md tink:rules refresh in scope
  (no objection raised).
- Merge only with explicit user authorization.

## Coordinator defaults (proposals, not user decisions)

- Run kind `bug` (a reviewed reproduction of the stale hint), profile `light`.
- Isolated worktree
  `/Users/jondev/dev/active/factory/working-copies/tink-substrate-workspace-1-18-3`
  on branch `workspace-1-18-3` from `origin/main` 0fd38d7.
- Seed Me triage: a clear execution request. No interview, no seed contract.
- Upgrade source: the installed, validated bundle
  (`check_install.py`: installation matches 0fd38d7; tink-sdlc revision
  3b175bbc8924a52512e7c12b29a4770e4f579267). The installed skill stays unchanged.
- Apply with `init.py <worktree> --upgrade --check`, then `--upgrade`.
  Expected: Update `_system/SDLC.md`, `_system/scripts/sdlc.py`,
  `stages/04-test/CONTEXT.md` and the receipt `_system/scaffold.json`; AGENTS.md
  router unchanged; project-owned files kept.
- Refresh the tink-generated rules block with installed tink 1.0.50
  (`tink use build-skillset`, also run by the stage-3 launcher). Pre-existing:
  `sdlc.py walk` W7 fails on main 0fd38d7.
- Add one offline test that scans this repo's own workspace files for
  `tink mount ... --payload` without `--json`.
- Historical runs `version-option` and `skill-read-guidance` will read "stale"
  after the stage-4 contract changes. Expected; they are not re-approved.
- This run's own stage-3 approval will go stale when the upgrade lands; the
  human re-approves the same brief afterwards.
- Dashboard: dedicated config, port 7872 (7871 and 7873 servers left intact).
- Not touched: main checkout, worktree
  `working-copies/tink-substrate-skill-read-guidance`
  (branch `docs/skill-read-guidance-closure`, local commit 395006e).

## Observations

- Baseline (main 0fd38d7): all managed scaffold hashes match the 1.18.2 receipt;
  only project-owned `_system/verification.json` differs.
- tink 1.0.50: `tink mount unslop --payload` exits 2; `--json --payload` returns
  the skill.
- Past stage-open picks in this repo: 2 router errors, 2 abstentions, 0 routed.
  A plain stage open will likely print no mount line, so the launch-prompt check
  also uses a stub router in a disposable clone, and the printed command is run
  against real tink.
