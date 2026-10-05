# Baseline: repro test for skill-read-guidance

Date: 2026-10-05T04:04Z. Checkout HEAD: ba6a510. Installer unchanged: PINS['tink-sdlc'] = 328a230.

tink-sdlc source: local clone (--no-checkout) of the patch-guidance worktree at `$TINK_SDLC_CACHE/tink-sdlc`; both 328a230 and 9172e2d are present.

## 1. At the current pin (328a230): expected FAIL
```
$ TINK_SDLC_CACHE=<tmp>/cache python3 -B -m unittest -v tests.test_skill_read_guidance
test_current_pin_tells_agents_to_use_json (tests.test_skill_read_guidance.BundledGuidanceTests.test_current_pin_tells_agents_to_use_json) ... FAIL
test_old_pin_has_the_bug (tests.test_skill_read_guidance.BundledGuidanceTests.test_old_pin_has_the_bug) ... ok
test_accepts_json_payload_either_order (tests.test_skill_read_guidance.ScannerTests.test_accepts_json_payload_either_order) ... ok
test_flags_payload_without_json (tests.test_skill_read_guidance.ScannerTests.test_flags_payload_without_json) ... ok
test_ignores_plain_mount (tests.test_skill_read_guidance.ScannerTests.test_ignores_plain_mount) ... ok

======================================================================
FAIL: test_current_pin_tells_agents_to_use_json (tests.test_skill_read_guidance.BundledGuidanceTests.test_current_pin_tells_agents_to_use_json)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "<wc>/tink-substrate-skill-read-guidance/tests/test_skill_read_guidance.py", line 91, in test_current_pin_tells_agents_to_use_json
    self.assertEqual(found, [], f'tink-sdlc at {self.pin} prints `tink mount ... --payload` without '
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                '--json; `tink mount` exits 2 on it: ' + repr(found))
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [('assets/_system/SDLC.md', 91, 'tink moun[139 chars]")')] != []

First list contains 2 additional elements.
First extra element 0:
('assets/_system/SDLC.md', 91, 'tink mount <skill> --payload` before relying on it). Abstent')

+ []
- [('assets/_system/SDLC.md',
-   91,
-   'tink mount <skill> --payload` before relying on it). Abstent'),
-  ('assets/_system/scripts/sdlc.py',
-   1122,
-   'tink mount {picked[\'winner\']} --payload.")')] : tink-sdlc at 328a2304b9af703dd846666757d6ffd1166df470 prints `tink mount ... --payload` without --json; `tink mount` exits 2 on it: [('assets/_system/SDLC.md', 91, 'tink mount <skill> --payload` before relying on it). Abstent'), ('assets/_system/scripts/sdlc.py', 1122, 'tink mount {picked[\'winner\']} --payload.")')]

----------------------------------------------------------------------
Ran 5 tests in 0.074s

FAILED (failures=1)
exit: 1
```

## 2. Same test, PINS patched in memory to candidate 9172e2d (installer not edited): expected PASS
Throwaway runner (outside the checkout) wraps `unittest.mock.patch.dict(install_skill.PINS, ...)`.
```
$ TINK_SDLC_CACHE=<tmp>/cache python3 -B <scratchpad>/run_at_candidate.py
test_current_pin_tells_agents_to_use_json (tests.test_skill_read_guidance.BundledGuidanceTests.test_current_pin_tells_agents_to_use_json) ... ok
test_old_pin_has_the_bug (tests.test_skill_read_guidance.BundledGuidanceTests.test_old_pin_has_the_bug) ... ok
test_accepts_json_payload_either_order (tests.test_skill_read_guidance.ScannerTests.test_accepts_json_payload_either_order) ... ok
test_flags_payload_without_json (tests.test_skill_read_guidance.ScannerTests.test_flags_payload_without_json) ... ok
test_ignores_plain_mount (tests.test_skill_read_guidance.ScannerTests.test_ignores_plain_mount) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.073s

OK
exit: 0
```

## 3. Network path (no TINK_SDLC_CACHE): clones the PINS url, current pin
```
$ python3 -B -m unittest -v tests.test_skill_read_guidance
----------------------------------------------------------------------
Ran 5 tests in 1.231s

FAILED (failures=1)
exit: 1
```

## 4. Full existing suite (current pin, no cache set)
```
$ python3 -B -m unittest discover -s tests
First extra element 0:
('assets/_system/SDLC.md', 91, 'tink mount <skill> --payload` before relying on it). Abstent')

+ []
- [('assets/_system/SDLC.md',
-   91,
-   'tink mount <skill> --payload` before relying on it). Abstent'),
-  ('assets/_system/scripts/sdlc.py',
-   1122,
-   'tink mount {picked[\'winner\']} --payload.")')] : tink-sdlc at 328a2304b9af703dd846666757d6ffd1166df470 prints `tink mount ... --payload` without --json; `tink mount` exits 2 on it: [('assets/_sy

----------------------------------------------------------------------
Ran 49 tests in 11.191s

FAILED (failures=1)
exit: 1
```

## 5. Full suite with the new test excluded vs included
Only `test_current_pin_tells_agents_to_use_json` fails at the current pin (section 4: 49 tests, failures=1). Other 48 pass.
Full suite with PINS patched to the candidate (throwaway runner):
```
$ TINK_SDLC_CACHE=<tmp>/cache python3 -B <scratchpad>/suite_at_candidate.py
...........fatal: cannot change to '/var/folders/sk/r2ns7lvn2ygcsj7bhd0mvnyw0000gn/T/tmpwqqt_ppo/missing': No such file or directory
......................................
----------------------------------------------------------------------
Ran 49 tests in 9.879s

OK
exit: 0
```
