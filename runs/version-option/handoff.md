# Version option handoff

## Actual request
Use $tink-substrate to add a --version option to tink-substrate so I can identify the version I am running.

## Constraints and defaults
- Preserve existing work. Work only in this isolated checkout on feat/version-option.
- Do not merge without actual human authorization. Brief acceptance is still required.
- Seed Me triage: ordinary execution request; no interview or confirmed seed.
- Proposed default: light feature run. Print the package name and current package version, exit successfully without configuration or a subcommand. Support the console command and python -m entry point.
- Keep commands and dashboard behavior intact; no dependency upgrade or release-version bump requested.
- Coordinator: /root/user_experience_trial; fresh stage agents must follow their stage contract.

## Setup evidence
Installed skill validated against source fdb13d577a06af25d764bef7a12fab86c21101eb. Main source is 985ac59. Existing entry-skill worktree was preserved.
Bundled SDLC 1.18.2 newly installed and committed at c5ca8b6; no prior target workflow existed.
Python 3.14.7. Existing 35 tests passed in 4.388 seconds. Verification runner additionally rejects a deliberate 1 != 2 test and empty discovery in a disposable temporary directory. Checks configured in _system/verification.json.
Features and Futures: smallest slice is version output; inspect module and installed console behavior. No broader cleanup proposed.

## Obstacles and interventions
No approval prompts or tool failures so far. Main checkout documentation predates installed entry skill; followed the installed package for bundled-tool setup rather than fetching replacement tools.

## Planning complete
Fresh planning agent /root/user_experience_trial/plan_version wrote brief.md and checklist.json. It reported no consequential open product choice. Stage 3 remains pending; no implementation or approval occurred.
Planner reported a tool syntax mismatch: documented `tink mount ... --payload` required `--json`; retry succeeded. Preserve this in the final retrospective.
Dashboard uses dedicated LaunchAgent dev.tink-substrate.version-option at http://127.0.0.1:7872; /api/snapshot confirmed this checkout and run. Port 7871 was already in use and left intact.
Next owner: human, to accept or revise the concrete brief and checklist. Supervisor will relay actual human decision.

## Build and verification complete

Build agent `/root/user_experience_trial/build_version` read the stage 3 and 4
contracts and confirmed the stage 3 approval was current before editing.
Implemented the accepted slice in candidate `cad755d83af539333c82524a65cfd9ec49747427`.
The package initializer holds version `0.1.0`; setuptools reads that value for
metadata, and argparse prints it through the global version action. README lines
39-54 document the source module and installed console forms. The approved brief
and checklist definitions were unchanged.

`python3 _system/scripts/sdlc.py verify version-option` passed. The configured
suite ran 41 tests in 8.658 seconds. The checklist separately ran all 6 version
tests in 4.062 seconds. Full output and the generated receipt are in
`04-test/output/`. The README review was recorded with `sdlc.py mark` before
verification. Both checklist items passed; the behavior item is proven by tests,
and the documentation item is an agent attestation.

The new repeatable test builds and installs a temporary copy of the package,
removes that source copy, and runs the generated console command and installed
module outside the checkout. Both print exactly `tink-substrate 0.1.0` with a
newline, exit 0, and no stderr. Installed metadata agrees. Other tests cover a
conflicting external version, missing and malformed config without writes,
help, the missing-subcommand error, and early exit before reading config or
running command handlers.

### Build observations for the retrospective

- No permission prompt or product decision blocked implementation.
- The generated AGENTS skill paths under `.tink/.active/` did not exist for the
  prose-only skills. `tink mount <skill> --json` through the SDLC wrapper supplied
  verified library entrypoints, which were read directly. No files or dependencies
  were upgraded to resolve this.
- Python 3.14.7 had pip but no setuptools. Standard pip build isolation successfully
  supplied build requirements in the temporary environment. No user installation
  was changed. Repeating the package test needs pip and access to its build
  requirements through the configured package index or cache. Missing tools or a
  failed build fail the test; they are not skipped.
- `principle-build-the-lever` led to the committed installation test rather than
  an unsaved manual installation. `principle-prove-it-works` led to executing both
  installed entry points after deleting their build source. `unslop` guided the
  short README and handoff text.
- Features and Futures decision: proceed to independent review. The accepted
  behavior works and there is no demonstrated product obstacle requiring more
  code or workflow changes in this slice.

Independent review, PR creation, release approval, and the delivery retrospective
and archive remain with the coordinator. This build session did not create a PR,
merge, or record any approval. Verification is local on macOS/Python 3.14.7; it
is not remote CI or proof of other Python/platform combinations.


## Installation-first CI repair

Repair agent `/root/user_experience_trial/repair_version` resumed stages 3 and 4
from `6b77d0e`. The coordinator could not resume the original builder because the
agent tool returned `agent thread limit reached`; this replacement session was
the orchestration workaround. No product decision or new approval was requested.
The existing stage 3 approval was current. The brief, checklist and approval
receipt remain byte-for-byte unchanged from that starting revision.

PR 2 CI run https://github.com/jon-devlapaz/tink-substrate/actions/runs/37259478228
failed the conflicting-metadata test. `gh run view 37259478228 --log-failed`
showed the Ubuntu 3.11 failure. The coordinator reported the same macOS 3.14
failure. The independent review reproduced it and identified the cause in
`/Users/jondev/dev/active/factory/working-copies/tink-substrate-version-review/runs/version-option/05-deploy/output/REVIEW-findings.md`.
That review checkout was read only throughout this repair.

The repair reproduced the failure in a temporary source copy and venv on local
macOS/Python 3.14.7. Copy `pyproject.toml`, `LICENSE`, `tests/` and
`tink_substrate/` into a temporary directory, create a venv, then run its Python
with `-m pip install --disable-pip-version-check --no-deps .` from that copied
source. Next run `-B -m unittest discover -s tests -p test_version.py -v` there.
Installation succeeded. Five tests passed and one failed in 4.134 seconds.
The probe returned `0.1.0` where the fixture required `99.0.0`. Full output is
`04-test/output/installation-first-before.txt`.

Setuptools leaves `tink_substrate.egg-info` in the build source. The original
probe ran with that source as its current directory, which Python searches before
PYTHONPATH, so the generated metadata hid the fake external version. This was a
test setup failure; no runtime version change was needed.

Candidate `b0d4a5ecf323c1251d49066d386c85683aff9d0e` changes only
`tests/test_version.py`. The metadata probe and source module command now run
from the temporary fixture directory. PYTHONPATH contains that directory first
and the actual source checkout second. This keeps conflicting metadata ahead of
build metadata while still importing the source package. Both original output
assertions remain, and the probe now also checks exit code zero.

After copying the repaired test into the same installed temporary source, its
full suite (`-B -m unittest discover -s tests -v`) passed all 41 tests in
8.432 seconds. The generated source metadata was still present. Output is
`04-test/output/installation-first-after.txt`.

After committing the repair, `python3 _system/scripts/sdlc.py verify
version-option` passed: 41 tests in 8.415 seconds plus the six-test checklist
in 4.063 seconds. The generated receipt and log are in `04-test/output/`.
Status reports verification current and the checklist 2/2 passed. The existing
README attestation predates this repair, which changes neither documentation nor
command behavior, so it was retained. No assertions, approved checks or
configuration were weakened.

`principle-build-the-lever` informed the saved test repair and repeatable
installation-first check. `principle-prove-it-works` required rerunning the actual
installed and source commands through the tests. `unslop` guided this handoff.
Features and Futures decision: proceed to independent review of the repair.
The demonstrated local obstacle is resolved; no broader workflow change is
justified by this test defect.

This session did not push, edit the PR, or merge. Updated independent review,
remote CI, the delivery retrospective and the independent archive remain with
the coordinator. Local results do not establish remote platform success.
