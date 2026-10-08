---
name: tink-substrate
description: Take a requested change in a Git repository from idea to reviewed PR, using Seed Me, tink-sdlc, a shared dashboard, and a saved retrospective. Use when the user asks to use tink-substrate for a change or resume a Substrate run.
---

# Tink Substrate

Own the setup and delivery of one useful change. The human chooses the outcome,
resolves consequential tradeoffs, accepts the required brief, and authorizes merge.
Do not give them a configuration checklist to perform themselves.

## Find the package and target

The directory containing this installed SKILL.md is the package root. It contains
`tink_substrate/`, `docs/`, `.substrate-tools/` and `installation.json`. Run
`python3 -B scripts/check_install.py` from that directory before using its tools.
If validation fails, stop setup and report the exact error. Do not use a personal
checkout to fill missing files. A source clone must first be installed using its
`scripts/install_skill.py`; this skill is intended to run from the copied package.

Read `docs/start-a-change.md` from the package root for setup and contracts.
Use Python 3.11+ consistently with `-B` (or `PYTHONDONTWRITEBYTECODE=1`) to avoid
writing bytecode into the installation. Keep work records and project changes
outside the package.

Use the user's current project as the target unless they name another. Read its
instructions, Git status, worktrees and installed workflow before making changes.
For a matching run with `tools.json`, follow `docs/automatic-tools.md` to validate
and resume its saved package. For a new run, choose a clean isolated checkout and
run name, then follow that guide to prepare current tools before discovery.
Preparation creates the run. Read the returned package's SKILL.md and guides,
and use it for all remaining work. A matching older run without `tools.json`
continues under its existing installed workflow and package without an upgrade.
Preserve existing work. A preparation failure stops setup with its exact reason.

## Handle the wiring

Follow the start guide yourself. Select a Python 3.11+ interpreter and use it
consistently. For prepared runs, use the saved package's workflow wrapper for SDLC
commands. Never upgrade a target's installed SDLC unless the user asks;
if preparation stops on a different installed version, report it and pass
`--upgrade-sdlc` only on the user's request. Use Seed Me's triage: a clear execution request can proceed to planning
without an interview or fabricated seed.
If someone answers or approves for the user, follow the start guide's rules for a
relayed user or a stand-in. A stand-in's answers stay `simulated`, and its
approvals are not human approval.
Configure the project's actual verification commands and prepare the brief under
its installed SDLC. Present the finished brief for required human acceptance.
Continue authorized setup and planning without asking about routine path choices.

Use these local defaults unless the user or project already chose others:

- Work record: `~/.local/share/tink-substrate/work/<project>/<run>.md`.
- Dashboard config: `~/.local/share/tink-substrate/config/<project>/<run>.json`.
- Dashboard: localhost port 7871, or another unused port. Keep an existing server
  intact. Pass the same explicit config to init and serve. Return the actual URL.
- Evidence: the target checkout's `runs/<run>/` and the archiver's default home.

Reuse the project name from an existing work record. For a new one, use the repo
name; distinguish repositories with the same name by owner or a short suffix. Use
that same project value for records, config and archive.

Create parent directories and the real work record using the guide's schema.
On resume, reuse the existing config. Only run init again when selection changes,
using `--replace` after checking its current contents.
Inspect the selected runtime before using `--trust-sdlc`. Start the dashboard
using the host's supported persistent process mechanism and confirm its status
endpoint responds for the selected work. If that host cannot keep a process alive,
state the limitation and provide the single command to restart this configured view.
Keep records tied to the actual checkout, run and PR; update the next action when
work pauses. After editing the record, refresh the running view by requesting
`/api/snapshot?refresh=1`; restart it only when the selection changes. Missing
credentials or tools are specific obstacles to report, not reasons to silently
skip a required check or invent success.

## Run an approved sequence

When the user wants several slices done in a row, follow `docs/run-a-sequence.md`: draft every brief first, get one
approval that names what it covers, keep a sequence record, merge each PR once checks pass and no P0/P1 is open, stop only for the listed
reasons, and finish with one end report. Don't ask whether to continue between slices.

## Deliver and learn

Follow the target's installed SDLC for implementation, verification and independent
review. Use the agent host's supported delegation when available; if required
review cannot run, report that unmet requirement. Never manufacture approval.
A request to use this skill covers the separate planning, build and review sessions
the SDLC asks for; start them as new sessions or subagents, whichever the host has.
For prepared runs, use the workflow wrapper's final prepared stage prompt. It
carries the saved package, tools record and bundled-only instructions. Add what
the session may write and the absolute handoff path. Keep stage sessions separate
and sequential in the prepared isolated checkout. For older runs, add the checkout
and handoff paths and write limits to the launcher's prompt.

Build one useful slice, check its behavior, then decide whether to continue or fix
a demonstrated obstacle to future changes. Record that decision in the existing
handoff or retrospective; add no extra process for hypothetical problems.

Read the package's `docs/finish-a-change.md` before delivery. Save the retrospective
and independent archive as part of finishing, not as homework for the user. Report
the PR, dashboard, checks, retro, archive and any remaining decision. Merge only
with actual user authorization received directly, not relayed by another agent,
then record closure using that same guide.
