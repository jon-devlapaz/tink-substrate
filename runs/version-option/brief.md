# Change brief

## Problem and outcome

Request: add `--version` to tink-substrate so the user can identify the version
they are running. Today the parser requires a subcommand and has no version
option. `pyproject.toml` declares version `0.1.0`.

Proposed scope: a light feature run for one global option, tests, and a short
README example. Work in this checkout on `feat/version-option`. This brief is a
proposal awaiting human acceptance; it is not an approval.

## Acceptance criteria

1. `tink-substrate --version` and `python3 -m tink_substrate --version` print
   exactly `tink-substrate <package version>` followed by a newline, exit 0,
   and produce no stderr. The current version remains `0.1.0`.
2. The option works from the source checkout and from an installed package.
   Installed output agrees with that package's distribution metadata. Source
   output identifies the source package, even if another version is installed.
3. No subcommand or configuration is required. Missing or malformed config
   files do not prevent version output; the command does not create or modify
   configuration, start a server, or read a selected work item.
4. Top-level `--help` lists the option. Invocations without a subcommand and
   without `--version` retain the existing error behavior. Existing commands
   and dashboard behavior continue to pass their tests.
5. The README shows the console and module forms and their output shape.

## Approach

Add argparse's built-in version action to the top-level parser in
`tink_substrate/__main__.py`, before subcommand parsing.

Use one version value for both runtime output and package metadata. Proposed
implementation: define `__version__ = '0.1.0'` in `tink_substrate/__init__.py`
and have setuptools read that attribute through its dynamic version setting in
`pyproject.toml`. This avoids duplicate literals and does not require an
installed distribution or a source-tree `pyproject.toml` at runtime. Keep the
package initializer free of side effects.

Add focused tests in `tests/test_version.py`. Exercise actual subprocesses for
the module and installed console command, including an installed invocation
outside the source checkout. Use temporary installation/configuration paths;
do not alter the user's installation or saved selection. Include assertions
that output matches installed metadata and that source output uses its own
version when distribution metadata differs.

No dependency upgrades, release-version bump, dashboard changes, or workflow
factory changes are part of this feature.

The implementation checklist lives in `checklist.json` (definitions with id/description/verify) and is marked only with `sdlc.py mark`. Give an item a `check` (argv + timeout) whenever an automated proof exists; `verify` then runs it and no mark is needed.

## Risks and verification

- Changing version metadata could break packaging. The focused test must build
  and install the local package into a temporary environment, run its generated
  console command outside the repository, and compare output with installed
  metadata. Use existing build tools and no dependency upgrades. Missing build
  tools are a reported failure, not a skipped passing test.
- A source checkout could accidentally report an unrelated installed version.
  Test source execution with differing metadata and assert the local version.
- An early-exit option could still touch config or run normal command handling.
  Test absent and malformed config and check that files remain unchanged.

The checklist runs focused unittest discovery for `tests/test_version.py`,
rejects zero discovered tests, and uses a 180-second timeout. The new file must contain real tests, including the
installation check; this command is planned verification, not passing evidence.

The configured full-suite check in `_system/verification.json` runs unittest
discovery, rejects an empty suite, and exits nonzero for failures (180-second
timeout). After implementation, commit the candidate, record the README review,
then run `python3 _system/scripts/sdlc.py verify version-option`. Preserve the
actual output. The handoff reports 35 baseline tests passed; this planning stage
has not rerun them or verified the proposed behavior.

`principle-build-the-lever` informed the choice to require a saved, repeatable
installation test rather than rely on a manual console check. Planning only
defines that test; implementation follows human acceptance of this brief and
checklist. No further product choice needs an interview. The light profile,
output format, and single-version approach remain proposed defaults for that
review. Merge requires separate actual human authorization.
