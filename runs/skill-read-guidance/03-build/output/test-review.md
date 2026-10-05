# Test review: skill-read-guidance reproduction test

Reviewer: independent Claude Code subagent (did not write the test). Date: 2026-10-04.
Checkout: branch `skill-read-guidance`, commit 6642f8b. Test reviewed: `tests/test_skill_read_guidance.py`.
Read: brief.md, checklist.json, handoff.md, 03-build/output/baseline.md, the test,
scripts/install_skill.py, .github/workflows/ci.yml, `_system/SDLC.md` "Bug reproduction baseline".

## Verdict: ACCEPT

The test fails at the current pin 328a230 for the documented reason (`tink mount ... --payload`
without `--json` at `assets/_system/SDLC.md:91` and `assets/_system/scripts/sdlc.py:1122`), and passes
at candidate 9172e2d. It fails, not skips, under CI when the clone is unavailable. It states that it does
not prove tink's generated rule line. No Important findings. The Minor gaps below do not block locking.

## Reproduction (re-run by reviewer, not copied from baseline.md)

Cache: `git clone --no-checkout ~/dev/active/factory/working-copies/tink-sdlc-patch-guidance $S/cache/tink-sdlc`
(`$S` = reviewer scratchpad). Both 328a230 and 9172e2d present (`git cat-file -t` -> commit).

At current pin 328a230, in the checkout:

```
$ TINK_SDLC_CACHE=$S/cache python3 -B -m unittest -v tests.test_skill_read_guidance
test_current_pin_tells_agents_to_use_json ... FAIL
test_old_pin_has_the_bug ... ok
(3 scanner tests) ... ok
AssertionError: Lists differ: [('assets/_system/SDLC.md', 91, 'tink moun[139 chars]")')] != []
FAILED (failures=1)   exit 1

$ env -u TINK_SDLC_CACHE -u CI python3 -B -m unittest -v tests.test_skill_read_guidance   # network clone
same single FAIL, same reason. Ran 5 tests in 1.359s; wall 1.7s
```

At candidate 9172e2d, in a throwaway `git archive HEAD` copy under `$S/copy` with the tink-sdlc pin
changed by sed (checkout not edited):

```
$ TINK_SDLC_CACHE=$S/cache python3 -B -m unittest -v tests.test_skill_read_guidance   -> Ran 5, OK
$ env -u TINK_SDLC_CACHE python3 -B -m unittest -v tests.test_skill_read_guidance     -> Ran 5, OK (1.32s)
$ env -u TINK_SDLC_CACHE python3 -B -m unittest discover -s tests                      -> OK, wall 11.5s
```

Coverage of the bundled text: `git grep -e --payload` over the whole tink-sdlc tree at 328a230 finds
exactly the two lines the test flags. Every `mount` mention under `assets/` at 328a230 is either one of those
two lines or prose without a command. So the two scanned files cover all current bug sites.

## Skip / vacuity checks

```
clone blocked (GIT_ALLOW_PROTOCOL=file), CI unset   -> OK (skipped=1)
clone blocked, CI=true                              -> AssertionError "tink-sdlc clone unavailable ...", FAILED (errors=1)
TINK_SDLC_CACHE=<missing dir>, CI=true              -> same AssertionError, FAILED (errors=1)
clone blocked, CI= (empty string)                   -> OK (skipped=1)
pin -> synthetic commit with both files deleted     -> CalledProcessError from git show (test errors)
pin -> synthetic commit with both files empty       -> OK  (vacuous pass, see Minor 1)
```

## CI behavior

- GitHub Actions sets `CI=true` on every runner, so the skip path becomes a failure there.
- Anonymous clone works: `HOME=$S GIT_TERMINAL_PROMPT=0 git -c credential.helper= clone --no-checkout
  https://github.com/jon-devlapaz/tink-sdlc.git` succeeded. 328a230 is on `origin/main`; 9172e2d is on
  `origin/fix/dogfood-workflow-guidance` only (the risk in the brief: deleting that branch breaks both the
  installer step and this test, so the candidate pin must be replaced before merge).
- Cost: one extra full clone of tink-sdlc, about 1.3 s locally; CI already clones it in the install step.
- No workflow change needed. Nothing in the test is newer than Python 3.11.

## Findings

Minor 1. Vacuous pass if the pinned files have no mount hint at all. An empty or rewritten SDLC.md/sdlc.py
passes `test_current_pin_tells_agents_to_use_json` (shown above with a synthetic commit). The test proves
"no bad hint", not "a working hint is printed". Low risk since pin moves are reviewed, but a positive check
(the current pin contains at least one `tink mount ... --json --payload`) would close it. The fix may add it
outside the locked test, or a reviewed replacement run may.

Minor 2. Scanner is line-based and literal. Missed variants (checked with `bad_mount_hints` directly):
- hint split across lines (`f"... tink mount {w} "` / `"--payload."`, or a wrapped Markdown line): not flagged.
- wrapper form `sdlc.py skills tink -- mount <skill> --payload`: not flagged.
- `tink  mount` (two spaces): not flagged.
- two hints on one line where only the second has `--json` (`tink mount a --payload; tink mount b --json`):
  not flagged, because `tink mount[^\n]*` is greedy to end of line.
None of these forms exist at 328a230 or 9172e2d, so the baseline is accurate. They matter only for a future
regression in a new shape.

Minor 3. Bookkeeping: baseline.md records "Checkout HEAD: ba6a510", i.e. it ran before the test was committed
as 6642f8b. The test file at 6642f8b is what this review ran, and the results match baseline.md.

Minor 4. The test depends on `scripts/install_skill.py` PINS, which the fix will change. Lock only the test
file; that is expected for this design and does not weaken the baseline.
