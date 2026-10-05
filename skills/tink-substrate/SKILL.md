---
name: tink-substrate
description: Take a requested change in a Git repository from idea to reviewed PR, using Seed Me, tink-sdlc, a shared dashboard, and a saved retrospective. Use when the user asks to use tink-substrate for a change or resume a Substrate run.
---

# Tink Substrate

Own the setup and delivery of one useful change. The human chooses the outcome,
resolves consequential tradeoffs, accepts the required brief, and authorizes merge.
Do not give them a configuration checklist to perform themselves.

## Find the package and target

This skill is distributed inside the Substrate repository. Resolve this SKILL.md's
real filesystem path (including symlinks); the package root is two directories
above its containing folder. Confirm it contains `tink_substrate/` and
`docs/start-a-change.md`. Read that root's `docs/start-a-change.md` for the
actual setup commands and contracts. Run Substrate commands from that root.
If the skill was copied without its repository, explain that the complete clone
is required; do not guess another installation.

Use the user's current project as the target unless they name another. Read its
instructions, Git status, worktrees and installed workflow before making changes.
Resume an existing matching run when present. Otherwise choose a separate checkout
and a short run name based on the requested change. Preserve existing work.

## Handle the wiring

Follow the start guide yourself. Select a Python 3.11+ interpreter and use it
consistently for setup and Substrate commands. Obtain its pinned tools only when missing; inspect
existing copies before reuse. Keep an installed target SDLC and follow its contracts.
Never upgrade it just to make setup match the guide. Use Seed Me's triage: a clear
execution request can proceed to planning without an interview or fabricated seed.
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
work pauses. Missing credentials or tools are specific obstacles to report, not
reasons to silently skip a required check or invent success.

## Deliver and learn

Follow the target's installed SDLC for implementation, verification and independent
review. Use the agent host's supported delegation when available; if required
review cannot run, report that unmet requirement. Never manufacture approval.

Build one useful slice, check its behavior, then decide whether to continue or fix
a demonstrated obstacle to future changes. Record that decision in the existing
handoff or retrospective; add no extra process for hypothetical problems.

Read the package's `docs/finish-a-change.md` before delivery. Save the retrospective
and independent archive as part of finishing, not as homework for the user. Report
the PR, dashboard, checks, retro, archive and any remaining decision. Merge only
with actual user authorization, then record closure using that same guide.
