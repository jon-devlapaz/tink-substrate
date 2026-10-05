# Handoff: skill-read-guidance

## User request (verbatim)

> Use $tink-substrate to fix the repeated skill-loading failures
> documented in runs/version-option/retro.md.
>
> Reproduce the missing skill paths and incorrect tink mount
> instructions. Identify which repository owns the problem,
> then make the smallest fix in its source—not my installed copy.
>
> Handle setup and the dashboard. Present the brief for approval,
> then implement, test with a fresh agent, obtain independent
> review, open a PR, and save the retrospective and archive.
>
> The fresh agent should need no path or command workarounds.
> Preserve tink-sdlc and Seed Me. Merge only when I authorize it.

## User decisions

- 2026-10-04, in the coordinating Claude Code session: "Adopt existing PRs
  (Recommended)". Do not duplicate jon-devlapaz/tink#94 or
  jon-devlapaz/tink-sdlc#43. Test them together with a fresh agent, attach the
  evidence to both PRs, and keep a small draft substrate PR that moves the
  pin once the user merges or releases them.
- Merge only with explicit user authorization. This includes #94, #43, #42 and
  any substrate PR.

## Coordinator defaults (proposals, not user decisions)

- Run kind `bug`, profile `light`, in isolated worktree
  `~/dev/active/factory/working-copies/tink-substrate-skill-read-guidance`
  on branch `skill-read-guidance` from `origin/main` 1acb6b3.
- Seed Me triage: a clear execution request. No interview, no seed contract.
- Installed copy `~/.codex/skills/tink-substrate`, the installed `tink` 1.0.48
  binary and `~/.tink-library` stay unchanged. Candidate tools are built or
  installed into temporary trial directories only.
- Dashboard: dedicated config and port 7873; the 7871 and 7872 servers stay
  intact.

## Reproduction (coordinator, 2026-10-04, installed tink 1.0.48)

- `tink mount unslop --payload` exits 2: `the following required arguments were
  not provided: --json`. The hint comes from tink-sdlc
  `assets/_system/scripts/sdlc.py:1122` (stage-open launch prompt) and
  `assets/_system/SDLC.md:91`, bundled here at tink-sdlc 328a230.
- `tink use` writes `(full: .tink/.active/NAME/SKILL.md; run: tink mount NAME)`
  (tink `src/use_skillset.rs`). The path does not exist until a plain mount
  runs; `--json` never links prose-only skills (`mounted: false`). Both build and
  review agents in version-option hit this.
- `tink mount NAME --json --payload` already works on 1.0.48 and returns the
  full skill in `payload.content`. Only the guidance is wrong.
- tink-substrate owns neither text. It pins tink-sdlc in
  `scripts/install_skill.py`; tink is an external optional tool.

## Existing source fixes (not authored in this session)

- jon-devlapaz/tink#94, branch `fix/mount-payload-guidance`, head ab8d7e9:
  generated line becomes `(read: tink mount NAME --json --payload)`; help names
  the `--json` requirement. CI green; independent review recorded no findings.
- jon-devlapaz/tink-sdlc#43, draft, branch `fix/dogfood-workflow-guidance`,
  head 9172e2d: launch prompt and SDLC.md add `--json`; stage 4 keeps
  verification in the build session. Manifest still names 1.18.2; waiting on
  release coordination with #42.

## Planning (stage 1 session)

Wrote brief.md and checklist.json (5 items). No approval, `decide`, commit or push.
Inspected tink#94 (ab8d7e9) and tink-sdlc#43 (9172e2d) read-only; both match the
handoff. 9172e2d is fetchable from GitHub as a branch head and PR ref today.

Skills loaded:
- `principle-build-the-lever`: ran `ls .tink/.active/principle-build-the-lever/SKILL.md`
  from the AGENTS rule line: failed, path absent (exit 1). Then `tink mount
  principle-build-the-lever` (the line's `run:` form): worked, created the path
  and `.tink/.gitignore` (untracked). Changed decision: the repro test and trial are
  built as rerunnable scripts, not manual checks.
- `unslop`: its rule line was not in AGENTS.md (planning rules block lists only the
  first skill, though the task prompt showed both). `tink mount unslop --payload`
  as printed in the earlier hint form exits 2 (needs `--json`). Used `tink mount
  unslop --json --payload` (the known-good form) and read `payload.content`. That
  is a workaround of the printed guidance, recorded here. It shaped the brief's wording.

Guidance failures hit: (1) `full:` path missing before a mount; (2) `--payload`
without `--json` rejected; (3) AGENTS.md was already modified (uncommitted) by the
stage-open recompile to planning-skillset, dropping the unslop line.
Not verified: remote CI with the new pin, the fresh-agent trial, the tink#94 build.
