# Version option retrospective

## Outcome

PR: https://github.com/jon-devlapaz/tink-substrate/pull/2

The accepted feature adds `--version` to both command forms. They print
`tink-substrate 0.1.0` without configuration or a subcommand. Package metadata and
runtime output share one value. The reviewed candidate is `b0d4a5e`; independent review found no remaining
Important findings. No merge occurred.

## Evidence and limits

The baseline had 35 passing tests. Current SDLC verification has 41 full-suite
and 6 focused passing tests. A separate installation-first full suite has 41
passing tests. See `04-test/output/test-log.md`, `verification.json`, and the
installation-first before/after logs. Tests run real source and temporary
installed commands, including execution outside the source checkout.

Local checks used macOS/Python 3.14.7. Packaging tests need pip and build
requirements from an index or cache; they are not offline or reproducible-build
proof. Local receipts and agent review do not authenticate human release approval.
Final remote CI and review results will be recorded below.

## Failure and repair

Initial candidate `cad755d` passed local checks but failed both remote CI
platforms after their `pip install .` step. Generated source `egg-info` took
precedence over the conflicting-version fixture, so its metadata probe returned
0.1.0 instead of 99.0.0. The independent reviewer reproduced the failure and
recorded an Important finding in `05-deploy/output/initial-review-findings.md`.

Repair `b0d4a5e` isolates the probe working directory and controls import paths.
It preserves the fake-version assertion and actual source-command assertion.
The installation-first reproduction changed from 5/6 focused tests passing to
41/41 full-suite tests passing. SDLC verification was renewed. Approved scope,
brief and checklist did not change.

## Obstacles and interventions

- Initial workflow setup added 22 files and 1,989 lines for this small feature,
  as required by the installed guide. Setup and product commits are separate.
- Main's guide predates the installed entry skill. Used the installed package's
  bundled tools and preserved the main and entry-skill checkouts.
- Port 7871 was occupied. Used 7872 with a dedicated config and LaunchAgent.
- Planner's documented `tink mount ... --payload` needed `--json`. Build and
  review agents also found missing `.tink/.active/` prose-skill paths. Supported
  mount commands returned verified library entrypoints, which agents read.
- Python lacked setuptools. Pip's standard temporary build isolation supplied
  build requirements without modifying the user's package installation.
- Attempting to resume the original builder failed with `agent thread limit
  reached`. A fresh repair agent started successfully with the recorded failure.
- Supervisor reported remote CI failure before the coordinator's next CI check.
  Agents then inspected logs, reproduced, and repaired it without human coaching.
- No setup permission prompts occurred. The sole product decision so far was
  actual user acceptance: “Approve brief and checklist”, relayed with source
  `request_user_input_async call_uOG7X4lUUgbfJQWEHG0MftsK` for artifacts at 98521de.
  A stage-3 receipt preserves that source. Acceptance is not merge authorization.

## What this taught us

A clean-checkout test pass missed the repository's installation-first CI setup.
The repaired fixture now works in both environments. No product redesign was
needed. The small argparse feature itself remained stable through review.

Decision: proceed with this bounded feature after independent review and final
CI. A separate workflow follow-up could correct the observed skill-path/mount
instructions; this run makes no workflow changes for that issue. Save delivery
and leave merge to the human. No customer outcome beyond command checks is claimed.

## Delivery result

Fresh independent review found no remaining Important findings. It independently
installed the package first in a disposable source copy, confirmed generated
metadata remained, and passed all 41 tests in 8.472 seconds. Both installed entry
points produced the exact expected output. See `05-deploy/output/REVIEW-findings.md`.

GitHub push and PR checks at 1126c66 passed on Ubuntu/Python 3.11 and macOS/Python
3.14 (four successful jobs). See `05-deploy/output/ci-before-delivery.json`.
Evidence-only delivery commits will receive a final head/check confirmation.

Supervisor also independently confirmed green CI and the source version output.
The coordinator recorded acceptance, opened stages, managed separate workers,
launched the dashboard, created the PR, checked CI, returned the failure for
repair, preserved both reviews, and prepared the archive. Recovery required one
fresh repair agent, another review checkout/agent, another verification pass and
another remote CI run. No human implementation coaching was supplied.

Remaining decision: human PR acceptance/merge. Delivery archiving is separate
from later closure; the coordinator will report the actual saved archive path
in the external work record and delivery response.
