# Independent review: version-option

## Result

No remaining Important findings. No nits reported. The earlier installation-first test failure is resolved by the test-only repair.

## Revisions and scope

- Verified code candidate: `b0d4a5ecf323c1251d49066d386c85683aff9d0e`.
- Reviewed checkout HEAD: `1126c6615fa9d7afb09f1e1db3067d6bfbdda43b`.
- Comparison base, local `origin/main`: `985ac59e68b77fcbc2ec90570ec7c9feab0ef17a`.
- HEAD differs from the verified candidate only in five run-evidence files. The launcher also supplied the uncommitted deployment rules in AGENTS.md and stage-5 skill snapshot.

Inspected the complete feature diff: runtime version, packaging, tests, README, workflow setup, stage contracts, skill pins, and saved run evidence. One combined pass covered logic, security boundaries and the accepted brief/checklist; this small feature did not justify separate review agents. The installed scaffold files match their saved installation hashes except `_system/verification.json`, which contains the configured test runner. This checks installation consistency, not independent authenticity of the scaffold.

## Prior Important finding: resolved

The saved before evidence shows `pip install .` succeeding, followed by the conflicting-metadata probe returning `0.1.0` instead of its fixture's `99.0.0`. Source egg-info took precedence because the probe ran from the source directory.

The repair changes only the test's working directory and PYTHONPATH ordering, and adds an exit-code assertion. Both original version assertions remain. The fixture directory now comes first and the source directory second; source code remains importable while fake distribution metadata takes precedence.

Independently repeated the installation-first sequence in a disposable copy with a fresh venv: install the copied package, confirm `tink_substrate.egg-info` exists in that source, then run `python3 -B -m unittest discover -s tests -v` from it. All **41 tests passed in 8.472 seconds**, including the conflicting-metadata test. Temporary files were removed after the check; the review checkout's code and saved evidence were not changed.

## Version contract

- Independently executed the generated installed console command and installed module outside the source directory. Each returned exit 0, stdout exactly `tink-substrate 0.1.0\n`, and empty stderr.
- The suite additionally builds an isolated package, removes its build source, exercises both installed entry points, and checks distribution metadata against the package version.
- The source module prints its own `0.1.0`; the repaired test first confirms external metadata is `99.0.0`, then asserts source output remains `0.1.0`.
- The initializer supplies the single version value to setuptools and argparse. The version action exits before config loading, server startup or selected-work processing.
- Tests cover missing/malformed config without writes, help visibility, the existing missing-subcommand error, and existing command/dashboard behavior. README examples agree with observed output.
- Read-only `sdlc.py status version-option` reports stage 3 approved, checklist 2/2 passed, and verification current. Saved verification covers 41 suite tests plus all six focused version tests. The earlier README attestation remains applicable because the repair changes only test setup.

The required `principle-prove-it-works` skill led to the independent installation-first run and direct command checks instead of relying solely on the saved passing receipt.

## Limits and handoff

Local execution used macOS and Python 3.14.7. This review does not establish results on other platforms or Python versions. Package tests require pip and access to build requirements through the configured index or cache. The workflow setup was inspected but its complete upstream test suite was not rerun. `git diff --check` reports Markdown hard-break whitespace in imported templates and whitespace in the retained failure output; these are not functional findings.

The coordinator must check the final PR head and required CI. No remote PR action, approval, merge or deployment was performed. This report is advisory and does not authorize release.
