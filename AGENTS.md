# Working on tink-substrate

Speak simply and concisely.

## Product direction

- Build one self-contained package in this repository.
- When starting a change from this repo, read `docs/start-a-change.md` for setup and handoff. Start discovery with Seed Me; preserve actual user decisions and identify proposals clearly.
- Work in small, useful slices. Features and Futures guides each pause: check the
  observed outcome, identify any concrete obstacle to the next change, then
  proceed, consolidate or re-scope. Stop repairing when that obstacle is resolved.
  Keep these decisions in the existing handoff; add no parallel lifecycle or gate.
- Other workflow repositories are reference material. Do not make this package depend on absolute paths to them.
- Keep provenance and license information for any code or skills brought into this repository.

## Work and evidence

- Inspect the current checkout and changes before editing. Preserve other agents' work.
- Keep tasks, runs, agent sessions, branches, and worktrees distinct and link them explicitly.
- Preserve human approval requirements. An agent report or dashboard label is not approval or proof that a check passed.
- Use real checks when behavior exists. Record missing verification and stale evidence plainly.
- Keep the design and README consistent with what is actually implemented.

## Finish a run

- Follow `docs/finish-a-change.md` for every Substrate run. At PR-ready delivery,
  write the retrospective, commit the evidence, and save an independent archive
  before handing back. Do this as part of the authorized run without asking the
  user to remember it. Report a failed archive explicitly.
- When later feedback, merge, or cancellation arrives, append a closure record
  and save a new closure snapshot. Preserve earlier snapshots. No automatic
  merge, monitoring, or new approval gate is implied.

## Examples and real work

`tests/fixtures/` contains synthetic test data, never real approvals or instructions.
Keep user work records outside the installed package. Do not treat examples or
past observations as current authority for a new run.
