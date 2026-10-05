# Review findings: skill-read-guidance (stage 5)

Reviewer: independent Claude Code subagent. I did not write this change.
Checkout: detached review checkout at 126bc32 (stage-5 open commit on top of PR head 3693e72).
Diff reviewed: `origin/main...HEAD` (PR jon-devlapaz/tink-substrate#3, draft).
This is a model review, not human approval. It approves and merges nothing.

## Result

ACCEPT. No Important findings. Five Minor findings, all about the precision of the evidence and wording. None of them blocks the draft PR.

## What I checked and what held

- **Pin change.** `scripts/install_skill.py` changes only the tink-sdlc revision, from 328a230 to 9172e2dce2fd2c32e69bf9b60e2c03c3bf779ebb. The new comment says: "Unmerged candidate (tink-sdlc PR #43). Replace with the merged/released revision before merging this change." The Seed Me pin stays at 58878b5. The diff has no other code change.
- **Locked test.** The sha256 of `tests/test_skill_read_guidance.py` matches `test-lock.json` (6c8268dd…). The file has not changed since 6642f8b (zero diff from 0f07a96 to HEAD), so it was locked before the pin commit 6da9737. The docstring says it does not prove tink's rule line or agent behaviour, which matches the brief.
- **Fails at 328a230, passes at the pin.** I re-ran this with a fresh `--no-checkout` cache and with a network clone (commands below). In both, the pin test failed at 328a230 on SDLC.md:91 and sdlc.py:1122, and all 5 tests passed at 9172e2d. A `git grep` over every `assets/` file at 9172e2d finds no `tink mount … --payload` without `--json`, so the scan is not missing another file.
- **Docs.** `docs/start-a-change.md:65` calls the tink-sdlc pin an unmerged candidate (#43) that will be replaced. `docs/new-user-validation.md:10-13` says the earlier validation used 328a230, which is no longer the pin. Nothing calls the pin merged or released. Outside `runs/`, nothing presents 328a230 as current: the only other mention is `OLD_PIN` in the test. Line 257 (1.18.2) is still true because `_system/scaffold.json` reports 1.18.2.
- **Install of HEAD.** I cloned HEAD into a temp directory and installed it twice, once over the network and once with `--tool-cache`. Both times `check_install.py` reported "Installation matches source 126bc32…", `installation.json` recorded tink-sdlc 9172e2d, and the installed SDLC.md:91 and sdlc.py:1122 contained `--json --payload`.
- **Trial evidence.** I checked the committed log against the raw trial files left in the coordinator's scratchpad:
  - The raw wrapper log `trial/tink-calls.log` is byte-identical to the committed `trial/commands.log` once `$TRIAL` is substituted back.
  - `last.out` holds the output of the final logged call, `tink mount principle-build-the-lever --json --payload`: valid JSON with 2458 chars in `payload.content`.
  - The `tink-real` sha256 (d1169981…) matches `tools.json`. It reports `tink 1.0.49`, and `tink-src` HEAD is ab8d7e9.
  - The sha256 of the trial install's `installation.json` matches `tools.json` (5b9d9aef…), and its `check_install.py` reports source 6da9737.
  - The trial target's AGENTS.md rule line reads `(read: tink mount principle-build-the-lever --json --payload)`. The target has no `.tink/.active`, which fits the absence of any plain mount.
  - Within the stated limits, this supports "0 workarounds" for the one required skill load.
- **Remote CI.** All 4 jobs passed at PR head 3693e72 (ubuntu 3.11 and macOS 3.14, two runs each). GitHub sets `CI`, so the repro test could not have been skipped there. Local HEAD 126bc32 adds only stage-5 run records and has not been pushed.

## Findings

1. **Minor. The PR body says "5/5" without saying 2 items are attested.** It says "SDLC verification is current with 5/5 checklist items". `sdlc.py status` says "5/5 passed (3 proven by check, 2 attested)", and the attested items are `docs-pin-wording` and `fresh-agent-trial`. Suggest copying the status wording.
2. **Minor. The PR body's "0 workarounds" needs its basis stated.** The wrapper logs only `tink` calls. The brief's other pass conditions ("no `ls`/`find` for paths, no edits to the installed copy") rest on `agent-report.md`, which is self-report, plus indirect signs such as the missing `.tink/.active` in the target. `result.json` and the handoff state the limits, but the PR body does not. Suggest: "0 workarounds (tink calls from the wrapper log; other actions from the agent's report)".
3. **Minor. `commands.log` does not follow the format the brief specifies.** Brief step 6 asks for "command, exit, first line of output", and step 1 asks for the binary path. The log has no output column. `tools.json` names the wrapper but not the path of the real binary. The proof of non-empty `payload.content` exists only in the uncommitted scratchpad `last.out`, which I inspected, and not in the committed evidence. Brief step 2 also asks for `check_install.py` on the trial install, which `tools.json` does not record. I ran it myself and it passed.
4. **Minor. The stage-4 `local-ci.md` install ran from a dirty tree.** It records "Installation matches source 0642556" together with tink-sdlc 9172e2d. 0642556 predates the pin commit, so the install came from uncommitted edits. The note in the file admits this. My clean install of HEAD replaces that evidence.
5. **Minor, follow-up and out of scope.** This repository's own SDLC workspace (`_system/SDLC.md:91`, `_system/scripts/sdlc.py:1122`, scaffold 1.18.2 at 328a230) still prints `tink mount <skill> --payload`. Runs in this repo keep the broken routed-skill hint until the workspace is refreshed from the fixed tink-sdlc. The shipped package is not affected. Also, stage-5 `skills/stage-5-pick.json` has `status: error`, so no routed skill was named. Neither the trial nor this review exercised the routed-skill hint with an agent, as `result.json` already states.

## Skill loading in this review (the run's subject)

- The AGENTS.md rule line in this checkout comes from the installed tink 1.0.48, which still uses the old form: `(full: .tink/.active/principle-prove-it-works/SKILL.md; run: tink mount principle-prove-it-works)`.
- `ls .tink/.active/` failed with "No such file or directory", and `cat .tink/.active/principle-prove-it-works/SKILL.md` also failed. The `full:` path did not exist before a mount, so the old failure still shows wherever tink#94 is not installed.
- `tink mount principle-prove-it-works` (the `run:` form as printed) exited 0 and printed "Mounted … Created .tink/.gitignore". After that the `full:` path was readable, and I read the whole skill. Both paths are git-ignored or excluded and do not appear in `git status`.
- I did not try the `--payload` or `--json --payload` forms. I did not use `tink-route`.
- How the skill changed the review: I checked the raw trial artifacts (wrapper log, `last.out`, binary hash, installation.json hash) rather than relying on `agent-report.md`, and I re-ran the fail and pass checks myself.

## Commands run (short outputs)

```
python3 -B _system/scripts/sdlc.py status skill-read-guidance
  -> Stage 3: approved; Checklist: 5/5 passed (3 proven by check, 2 attested); Verification: current
shasum -a 256 tests/test_skill_read_guidance.py      -> 6c8268dd… (matches test-lock.json)
git clone --no-checkout ~/dev/active/factory/working-copies/tink-sdlc-patch-guidance $TMP/cache/tink-sdlc
  (both 9172e2d and 328a230 present)
TINK_SDLC_CACHE=$TMP/cache python3 -B -m unittest tests.test_skill_read_guidance   -> Ran 5, OK
TINK_SDLC_CACHE=$TMP/cache python3 -B $TMP/oldpin.py  (PINS patched in memory to 328a230)
  -> FAIL test_current_pin_tells_agents_to_use_json [('assets/_system/SDLC.md', 91, ...)]; FAILED (failures=1)
python3 -B -m unittest tests.test_skill_read_guidance  (network clone)              -> Ran 5, OK
python3 -B $TMP/oldpin.py  (network clone)                                          -> FAILED (failures=1), same test
python3 -B -m unittest discover -s tests  (network)                                 -> Ran 49, OK
CI=1 TINK_SDLC_CACHE=$TMP/cache python3 -B -m unittest discover -s tests            -> Ran 49, OK
git clone <checkout> $TMP/src; checkout 126bc32
python3 scripts/install_skill.py --destination $TMP/skill                            -> Installed, exit 0
python3 $TMP/skill/scripts/check_install.py      -> Installation matches source 126bc32…; tink-sdlc 9172e2d
python3 scripts/install_skill.py --destination $TMP/skill2 --tool-cache $TMP/tc + check_install.py -> matches 126bc32
python3 -m tink_substrate --help -> exit 0;  init.py $TMP/target --check -> preview, exit 0
gh pr view 3 … statusCheckRollup -> 4/4 SUCCESS at 3693e72
diff (trial/tink-calls.log with $TRIAL substituted) runs/.../trial/commands.log -> identical
shasum trial/bin/tink-real -> d1169981… ; tink-real --version -> tink 1.0.49 ; tink-src HEAD ab8d7e9
last.out -> JSON, payload.content 2458 chars (principle-build-the-lever)
```

## Limits

- I did not re-run the fresh-agent trial. I inspected its raw artifacts.
- I did not rebuild tink from ab8d7e9. The binary hash is consistent with `tools.json` but does not prove what the binary was built from.
- I did not run `pip install .` or `tink-substrate --help`.
- The 9172e2d network fetch works today. Whether it is still fetchable after #43 merges is the open risk the brief already records, which is why the PR stays draft.
- The uncommitted AGENTS.md change in this checkout is stage-open launcher output (`deployment-skillset`), not part of the change. I left it alone.
- This review is not code-owner approval and not a deployment result.
