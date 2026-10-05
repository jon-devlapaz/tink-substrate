# Version option independent review

## Result

One Important finding blocks completion: the conflicting-metadata test fails after installing the package from the checkout. No functional defect was found in the version option itself. This review does not approve the candidate for release.

## Important finding

**[P1] Make the conflicting-metadata fixture independent of source build metadata — `tests/test_version.py:76–81`.**

After `pip install .`, setuptools leaves the source checkout's `tink_substrate.egg-info`. The metadata probe runs with that checkout as its working directory, so its current-directory entry precedes the temporary `PYTHONPATH` fixture. `importlib.metadata.version` returns the source package's `0.1.0`, and line 81 fails before the version-command assertion. This breaks the installation-first CI setup and leaves the conflicting-version criterion unverified there. Isolate metadata discovery from generated source metadata while preserving the real source-command assertion, then rerun verification and CI.

The coordinator reported the same failure on both CI platforms in https://github.com/jon-devlapaz/tink-substrate/actions/runs/37259478228 . I independently reproduced it without changing this checkout: copied the package, tests, pyproject and license to a temporary directory; created a temporary venv; installed the copied source with `pip install --no-deps`; then ran `python -B -m unittest discover -s tests -p test_version.py -v` from the copied source. Installation exited 0. Five tests passed and the conflicting-metadata test failed in 4.203 seconds; test process exited 1:

```text
AssertionError: '0.1.0\n' != '99.0.0\n'
```

The earlier 41-test pass below remains accurate for the clean review checkout. It does not cover this installation-first condition. The coordinator has returned the failure to the builder; updated code requires renewed verification and review.

## Reviewed revisions and scope

- Product candidate: `cad755d83af539333c82524a65cfd9ec49747427`.
- Saved build/test evidence: `3302664`.
- Review checkout HEAD: `6b77d0e8638b5128dd4e2cb591fd752330453b45` (stage-opening evidence commit).
- Comparison base, local `origin/main`: `985ac59e68b77fcbc2ec90570ec7c9feab0ef17a`.
- Product files at review HEAD match the candidate: `README.md`, `pyproject.toml`, `tink_substrate/`, and `tests/` have no intervening diff.
- PR supplied by coordinator: https://github.com/jon-devlapaz/tink-substrate/pull/2 . The coordinator owns final PR head, CI, and delivery checks.

One combined review pass covered logic, side effects, packaging, security boundaries, documentation, tests, and acceptance criteria. This small argparse change did not warrant separate specialist passes. Workflow scaffolding and run records in the broader branch diff were read as review context; this review does not certify the entire workflow engine.

## Evidence checked

Read `AGENTS.md`, stage 5's contract, `_shared/REVIEW.md`, the brief, checklist, approval receipt, documentation mark through current status, saved test log, and verification receipt. `python3 -B _system/scripts/sdlc.py status version-option` reported stage 3 approved, checklist 2/2 passed, and verification current. The verification receipt names the exact product candidate above. Local receipts do not authenticate human identity or release authority.

Ran the configured full-suite command independently in this checkout:

```sh
python3 -B -c "import unittest; s=unittest.defaultTestLoader.discover('tests'); assert s.countTestCases() > 0, 'No tests discovered'; r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(not r.wasSuccessful())"
```

Result: exit 0; **41 tests passed in 9.303 seconds**, including all six version tests. No test was skipped. The saved stage-4 results were also inspected: 41 tests passed in 8.658 seconds and the separate six-test checklist run passed in 4.062 seconds. Those saved results were not rewritten.

The independent run exercised:

- Source module output with no configuration or subcommand: exact name/version/newline, exit 0, empty stderr, no files created in the temporary home.
- Missing, malformed, and selected configuration: version succeeds and file contents remain unchanged. Separate patched read/config/server handlers fail if called, confirming the early exit.
- Conflicting distribution metadata (`99.0.0`): source output still uses its own `0.1.0`.
- A real temporary package build and installation, followed by deletion of the copied build source. Both installed module and generated console command run outside the checkout, print the expected version, and agree with installed distribution metadata.
- Help visibility, the existing missing-subcommand error, and the existing CLI, source, archive, and dashboard regression tests.

A separate source subprocess observation returned exit `0`, stdout `b'tink-substrate 0.1.0\n'`, and stderr `b''`. README lines 39–54 describe that behavior and both entry points accurately.

The initializer contains only its docstring and version constant. Setuptools reads that same constant for package metadata. The argparse version action exits during parsing, before normal configuration reads and command handling. No new dependency, server path, or file-write path was introduced.

## Limits and workflow observations

- Environment: macOS 27.0.1 arm64, Python 3.14.7. This reviewer did not independently verify other Python/platform combinations, remote CI, forge approval, deployment, or rollback state.
- Installation testing uses pip build isolation and the configured build requirements (`setuptools>=68`). It needs the package index or cached build requirements; it passed here. This is not an offline or reproducible-build claim.
- The generated required skill path `.tink/.active/principle-prove-it-works/SKILL.md` was absent. The supported command `python3 -B _system/scripts/sdlc.py skills tink -- mount principle-prove-it-works --json` returned `/Users/jondev/.tink-library/skills/principle-prove-it-works/SKILL.md`, `mounted: false`, and the digest matching the stage lock. Read that file in full. Its requirement to check actual artifacts was applied through diff inspection, installed command execution in the tests, and direct source output inspection. No skill files were copied or repaired.
- The stage-5 skill pick recorded `status: none`; no additional routed skill was required.
- No code or prior run evidence was changed. The only review output is this file; pre-existing generated AGENTS and stage-open files were preserved.

Repair the test fixture and refresh verification before review completion. Final forge checks and human release authorization remain with the coordinator and owner.
