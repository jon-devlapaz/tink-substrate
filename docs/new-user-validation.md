# Validation and release limits

## What has been checked

The setup instructions were exercised in temporary directories on macOS with
Python 3.13 and 3.14. A fresh native Claude session independently followed a draft
using a restricted PATH and scratch configuration. These checks shared an existing
OS and installed interpreters; they were not a fresh-machine test.

- Public clones reached Seed Me `58878b5794ca04a5ec0ba62027faadabfe7ca925`
  (1.17.1) and SDLC `328a2304b9af703dd846666757d6ffd1166df470` (1.18.2).
  Both were on merged public history. The current SDLC pin is 1.20.0 (`3440e17`),
  which adds the structured status API, a status next-action fix, and an early
  delivery warning, on top of the 1.18.3/1.18.4 skill-reading and router-reason fixes;
  this validation predates all of them.
- Installer preview was non-mutating; install preserved project instructions.
- Planning opened without optional Tink tools and reported skipped stage skills.
  An installed Tink with an empty library explicitly refused stage opening.
- Real fixture tests passed correct code and rejected incorrect code. Workflow
  verification correctly refused to proceed without human approval.
- Virtual-environment package installation, CLI use outside the source directory,
  and all 35 unit tests passed before publication preparation.
- The dashboard and CLI supplied expected status. Older SDLC text remained text,
  without inferred approval or verification. Separate rendered-page checks covered
  that compatibility behavior.
- Archive success was checked on committed runs; dirty-run refusal was also checked.

The new-user instructions were corrected where fresh-session use exposed missing
scaffold commits, missing request handoffs, work-record placement and ambiguous
paths. Those changes used existing artifacts rather than adding a lifecycle.

## Entry skill trial

A fresh agent followed the entry skill on a disposable Python project through tool
setup, an isolated checkout, real test configuration, planning and a working
dashboard endpoint. A separate planner wrote the brief and checklist. The trial
stopped at human acceptance, without implementing the proposed change. It used
this machine's existing Tink library and permissions. Two Tink instruction mismatches
required agent recovery. See [the retrospective](../runs/entry-skill/retro.md).

## Copied package trial

The installer now copies the runtime, guides and skill and exports the pinned
Seed Me and SDLC sources with their licenses. Fresh GitHub downloads and an offline
Git cache were both exercised. Tests cover independent copies, repeat-install
refusal, existing symlinks, committed dependency exports and failed installation.

On macOS, a sandbox denied access to the author's development directory, personal
skills and Tink/Seed Me data. With an empty HOME, a limited PATH without Tink or
routing, and network denied, the installed package opened planning, recovered the
run in a fresh process and refused verification before human approval. A separate
localhost-enabled check served the selected dashboard and archived synthetic run
evidence. This was not feature delivery; no acceptance was invented. The initial
dashboard probe used the wrong endpoint; correcting the probe to `/api/snapshot`
passed without a product change.

## Claude Code dogfood run

The package was installed with `--destination ~/.claude/skills/tink-substrate`
and used from Claude Code on a small CLI project. Planning, build and review ran
as Agent-tool subagents. The run reached an open PR with current verification and
an advisory review. A coordinator agent stood in for the user: Seed Me recorded
its answers as `simulated`, no seed was confirmed, and no human approved the brief.
The run's retro and dogfood log stay with that project's run evidence.

## What is not established

The basic path has not delivered a complete user change through PR review and
closure. A human-answered Seed Me interview and the full Codex Desktop handoff
still require a real user trial. The historical skill-equipped trials do not prove equivalent
outcomes with optional skills absent.

The public GitHub clone succeeded after publication. The initial GitHub CI run
passed on Python 3.11 on Linux and 3.14 on macOS.
Host permissions may require access to chosen paths and the network. No claim is
made for unattended operation, all repositories or all agent hosts.

## Publication preparation

The owner selected public `jon-devlapaz/tink-substrate` and MIT. This clean snapshot
contains the runtime, tests, CI and user-facing documentation. Personal work records,
private-project references, historical approvals and the original Git ancestry are
excluded. Original history and review evidence are retained privately.

A native Claude publication review covered the original candidate and reachable
history. A separate native Claude Opus 5.5 review of the cleaned candidate found no
publication blockers before the initial push.
The package license applies to this repository. Workflow dependencies are obtained
separately from their public repositories and retain their own source and terms.

## Next proof

Follow the actual GitHub README in a fresh session, complete a
bounded change with real approvals, resume once after interruption, and save its
reviewed PR and retrospective. Record each intervention. Change the system only
where that run demonstrates a need.

## Automatic preparation

New runs now select current main with exact-commit CI, export separate packages,
and retain a tools receipt. Offline resume and failure cases are checked using
real temporary Git repositories and synthetic CI responses. The compatibility
probe executes copied Seed Me, SDLC and dashboard code on a synthetic unapproved
run. These checks do not establish a human interview or complete feature delivery.
See `runs/auto-refresh/retro.md` for the final candidate's live-source evidence and
remaining limits. Optional Tink/routing provisioning is outside this slice.
