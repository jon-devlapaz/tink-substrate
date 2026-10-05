# Brief: skill-read-guidance

Proposal for human review. Not an approval.

## Problem

Fresh agents fail to load skills by following printed guidance
(runs/version-option/retro.md, lines 46-48). Reproduced 2026-10-04 with tink 1.0.48
and again in this planning session:

1. tink-sdlc tells agents `tink mount <skill> --payload`. That exits 2 and asks for
   `--json`. Source: tink-sdlc `assets/_system/scripts/sdlc.py:1122`,
   `assets/_system/SDLC.md:91`, bundled here at the pin 328a230.
2. `tink use` writes `(full: .tink/.active/NAME/SKILL.md; run: tink mount NAME)`.
   The path is absent in a fresh checkout (`ls` exits 1) until a plain mount runs.
   Source: tink `src/use_skillset.rs`.
   The working form is already `tink mount NAME --json --payload`.

Owners: tink (1) and tink-sdlc (2). tink-substrate owns neither text; it only
pins tink-sdlc in `scripts/install_skill.py`, so installed copies inherit the bug.

## Scope (user chose: adopt existing PRs)

Not duplicated here: jon-devlapaz/tink#94 (head ab8d7e9, rule line becomes
`(read: tink mount NAME --json --payload)`) and jon-devlapaz/tink-sdlc#43
(draft, head 9172e2d; `--json` in launch prompt and SDLC.md; stage 4 stays in the
build session). Read-only inspection of both worktrees confirmed the diffs match the
handoff. #43 changes the bundled `sdlc.py`, `SDLC.md`, `stages/04-test/CONTEXT.md`,
and manifest hashes; scaffold version stays 1.18.2.

This run changes tink-substrate only:

- Move the tink-sdlc pin to 9172e2d, marked as a candidate.
- Add one reproduction test.
- Fix docs that name the pin or say it is on merged history.
- Seed Me pin (58878b5) and content unchanged. No edits to tink-sdlc source.
- Installed skill, tink 1.0.48 and ~/.tink-library untouched.

## Acceptance criteria

1. `PINS['tink-sdlc']` in `scripts/install_skill.py` is 9172e2d, with a comment saying
   it is an unmerged candidate to replace with the merged/released revision
   before merge. Seed Me pin unchanged.
2. A new test fails at the old pin 328a230 because the bundled SDLC.md and sdlc.py
   tell agents `tink mount ... --payload` without `--json`. It passes at the current
   pin. It does not claim to prove tink's generated rule text.
3. Docs that cite the pin (`docs/start-a-change.md:65,257`,
   `docs/new-user-validation.md:10-11`) say the pin is a candidate (or the old
   validation was at 328a230), not "merged public history". The scaffold version is
   unchanged, so "1.18.2" stays true.
4. Existing tests and CI pass. The CI install step works with the new pin.
5. Fresh-agent trial (below) passes with zero workarounds, evidence saved.

## Approach

- Edit the pin and comment. `installation.json` records the pin, so no other code agrees with it.
- Test `tests/test_skill_read_guidance.py` (stdlib unittest):
  - A pure function finds `tink mount ... --payload` hints that lack `--json` on
    the same line. Offline unit cases cover it.
  - Pin test: fetch `assets/_system/SDLC.md` and `assets/_system/scripts/sdlc.py`
    from the tink-sdlc clone (`git show REV:path`). Assert the old pin
    328a230 yields bad hints (documents the bug) and `PINS['tink-sdlc']` yields none.
  - Source of the clone: env `TINK_SDLC_CACHE` (offline, same layout as `--tool-cache`),
    else a `--no-checkout` clone of the PINS url into a temp dir, as the installer does.
    If neither works, skip locally; fail when `CI` is set.
- CI already installs from the pins over the network, so no workflow change is
  needed. Stage 4 text is not tested.

## Risks

- Candidate pin is a PR branch head. If #43 is squash-merged and the branch is
  deleted, 9172e2d may become unfetchable and CI breaks. Replace it with the
  merged/released revision before merge. This PR stays draft until then.
- #43 is a draft and its manifest still says 1.18.2; the coordination with #42 may
  change the version. Re-check docs when repinning.
- The test needs network or a cache. It proves the bundled SDLC text, not the
  tink binary's rule line (external, optional) and not that agents obey guidance.
- The planning rule block in AGENTS.md was recompiled to `planning-skillset` by the
  stage open (one skill, not two); that is uncommitted launcher output, not part
  of this change. Do not commit it.
- Possible missed scope (proposal only): stage CONTEXT files for stages 1-3 still say
  "`tink use` ... start a NEW session"; no failure seen, so not included.

## Verification

Checklist ids: `pin-candidate`, `repro-test`, `docs-pin-wording`, `full-suite`, `fresh-agent-trial`.

Fresh-agent trial (human-visible evidence, run by the coordinator in stage 4/5):

1. In a temp dir: build tink from jon-devlapaz/tink at ab8d7e9
   (`cargo build --release`, clone to temp, not the patch worktree). Put that binary
   first on PATH only for the trial. Record `tink --version`, source SHA, binary path and sha256.
2. Install the substrate branch HEAD to a temp destination with
   `scripts/install_skill.py --destination TMP/skill --tool-cache TMP/cache`. The
   cache holds local clones of Seed Me and tink-sdlc at the pinned commits. Run
   `scripts/check_install.py`.
3. Create a disposable git repo as target (temp). Start a new agent session with only the
   installed copy and that target. It follows the README/SKILL text, opens stage 1 with
   `sdlc.py stage`, then loads each required skill and the routed skill (if any) by
   running the printed command exactly as written. For the routed skill, if the pick
   abstains, use `tink-route` once for a gap, as guidance directs.
4. Pass means all of: every load command is copied from printed guidance (AGENTS rule
   line or stage launch prompt), exits 0, and returns non-empty `payload.content`
   (or SKILL text); no `ls`/`find` for paths, no added or removed flags, no edits
   to the installed copy, no global tink binary. Skills come from a temporary copy of
   ~/.tink-library selected with `TINK_HOME`; the real library is not fetched, approved
   or edited. Any deviation, extra probe, or guidance failure is a fail and is recorded.
5. Control: same steps with installed tink 1.0.48 and the old pin reproduce the failure
   (kept as the "before" record, not the pass condition).
6. Evidence under `runs/skill-read-guidance/trial/`: `commands.log` (command, exit,
   first line of output), `agent-report.md` (agent's own account of any deviation),
   `tools.json` (tink version, SHAs, binary hash, installed `installation.json`
   hash), `result.json` (`pass` or `fail`, workaround count). The agent report
   is not proof; the commands log is.
