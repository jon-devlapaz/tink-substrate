# Current tools for a new run

From the installed package, prepare a clean, isolated checkout before discovery:

```sh
python3 -B -m tink_substrate prepare --checkout /absolute/isolated-target --run useful-change
```

Use `--kind bug` for a bug fix. Use `--profile full` when the human selected the
full workflow. The command creates the SDLC run, so do not run `sdlc.py new` again.

Preparation checks current `main` in the fixed public Substrate, tink-skills and
tink-sdlc repositories. Each commit needs its designated CI workflow to have
completed successfully. It exports exact committed files, checks the copied
combination in a disposable project, checks main again, then installs or upgrades
SDLC in the selected target and creates the run. A moving main, pending or failed
CI, network failure or incompatible package stops preparation. There is no
fallback to an older success.

Read the returned JSON. It names the package directory and the versions, commits,
CI runs and compatibility checks. Use that directory as the package root for
Seed Me, dashboard and archive commands. Read its current `SKILL.md` and guides.
The global installed skill remains the bootstrap entry; preparation does not
replace it or other installations. `runs/<run>/tools.json` keeps the same record.
Commit that record and scaffold setup before implementation.

## Use and resume the saved tools

Use the workflow wrapper from the returned package for every SDLC command:

```sh
python3 -B -m tink_substrate workflow --checkout /absolute/isolated-target --run useful-change -- stage useful-change 1 --here
python3 -B -m tink_substrate workflow --checkout /absolute/isolated-target --run useful-change -- status useful-change --json
```

Add `--seed-contract /absolute/session/seed-contract.md` to stage 1 when Seed Me
returned an actually confirmed seed. Follow that version's Seed Me instructions
for the handoff location and ledger. Configure the target's real checks and obtain
its required human brief acceptance. Preparation creates no approval.

On resume, call prepare with the same checkout and run. It checks the existing
package and managed workflow files without network access, and returns the saved
record. The same rule applies to workflow commands. New upstream commits belong
to the next run. Project-owned verification settings remain editable under SDLC's
existing review rules. Changed managed files or package files refuse resume.
An old run without a tools record must continue under its existing contracts;
prepare refuses to update it. Do not manufacture a tools record for that run.

## Boundaries and recovery

- New-run preparation requires a clean target and package storage outside it.
  The target must be the explicitly selected isolated checkout. Its main checkout
  and existing runs are not upgraded. Customized managed files refuse the upgrade;
  project-owned configuration and pins are preserved.
- This slice updates the three bundled components. The workflow wrapper disables
  SDLC's discovery of global Tink and tink-route. Project check commands retain
  their normal PATH. A target requiring Tink refuses this bundled-only mode.
  Automatic provisioning of those optional tools is not implemented.
- `prepare` needs authenticated `gh` access to repository and Actions metadata,
  Git, Python 3.11+ and Bash. It checks the current main at the last preflight;
  an upstream commit landing after that check belongs to the next run.
- Compatibility checks exercise Seed Me's helper, SDLC API 1 and the dashboard's
  blocked state for an unapproved synthetic run. They do not prove interview
  quality or completed user work. Hashes are local integrity evidence, not signatures.
- A crash before `tools.json` is saved leaves an unprepared run. Preserve the
  checkout and package for inspection. A retry refuses that run rather than
  guessing its versions or replacing evidence. Preparation locks one checkout
  against concurrent preparation; it does not coordinate unrelated agent edits.
- Packages must remain available while their runs are active. The archive records
  their version receipt but does not include external package directories. Preserve
  a needed package separately before deleting its storage. Offline resume needs it.

The explicit pinned installer remains available for reproducible manual setups.
Its pins describe that installation, not the freshness of a new prepared run.
