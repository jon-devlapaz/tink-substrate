# Start a change

Use this when a fresh person or agent starts a change from Substrate. The dashboard
is packaged here. Seed Me and tink-sdlc are external tools; this guide connects them.
An agent host is still required. This is not yet a one-command software factory.

## 1. Check the basics

The first path targets macOS with Codex Desktop and one existing Git repository.
Open the target project in Codex, and give the agent the absolute Substrate path.
The agent reads that project's instructions before choosing a separate checkout.
The complete Codex Desktop handoff is still to be tested. Host permissions may
require access to the selected checkouts, evidence directories and network; record
actual prompts rather than assuming the author's permissions. Other agent hosts and
Linux are outside the first user trial.

The public repository is `https://github.com/jon-devlapaz/tink-substrate`
under MIT. Obtain it with:

```sh
git clone https://github.com/jon-devlapaz/tink-substrate.git
cd tink-substrate
```

The public clone and initial GitHub checks have passed. The two workflow sources
below are also public.

For this first path, use macOS with Python 3.11+, Git, and Bash.
The underlying runtime also supports Linux, but that is outside this user trial. Git needs your commit identity.
For GitHub delivery, install `gh` and sign in to the intended account. A target
repository needs an initial commit for Git snapshots and verification, and a remote
before a PR can be created. Check the target remote rather than assuming it belongs to the intended account.

Check tool versions anywhere:

```sh
python3 --version
git --version
bash --version
```

From the **target repository**, inspect `git status --short`, `git remote -v`
and `git worktree list`. Confirm its Git identity with `git config user.name` and
`git config user.email`; configure your actual identity if absent. Inspect
Substrate's status separately if you plan to change Substrate itself.

Keep existing changes and active worktrees. Choose a separate checkout for the run.
Run the commands below from the Substrate checkout unless another directory is named.

## 2. Obtain the workflow tools

These commands download two repositories from GitHub into the ignored
`.substrate-tools/` directory. They use specific revisions inspected for this guide,
not the latest upstream versions. No global skill installation is required.
Run this once in a fresh directory; if it already exists, inspect it before reusing
it. Do not reset an existing checkout to make these commands work.

```sh
mkdir -p .substrate-tools
git clone --no-checkout https://github.com/jon-devlapaz/tink-skills.git .substrate-tools/tink-skills
git -C .substrate-tools/tink-skills checkout --detach 58878b5794ca04a5ec0ba62027faadabfe7ca925
git clone --no-checkout https://github.com/jon-devlapaz/tink-sdlc.git .substrate-tools/tink-sdlc
git -C .substrate-tools/tink-sdlc checkout --detach 328a2304b9af703dd846666757d6ffd1166df470
```

The selected sources provide Seed Me 1.17.1 and tink-sdlc scaffold 1.18.2. Both pins are on merged public history.
This SDLC version supplies text status; the dashboard displays it without
inventing structured verification or approval.
Their original licenses remain in those checkouts. Updating either revision is a
separate, reviewed dependency change. Network or authentication failures mean the
tool is unavailable; do not substitute remembered instructions.

## 3. Turn the hunch into a confirmed seed

Tell your agent:

> Read `.substrate-tools/tink-skills/skills/seed-me/SKILL.md` and follow it for this
> hunch: [your idea]. Resolve its helper paths from that skill directory. Keep my
> choices separate from your proposals.

Follow the skill’s triage first. An ordinary execution request can keep its
requested format without another interview; do not invent a confirmed seed for it.
In that case, give planning the actual request and labelled defaults, and omit
`--seed-contract` from the stage-1 command below.

The installed SDLC guide also describes installing Seed Me through Tink. This
basic path instead reads the same skill from its pinned clone; it does not require
a global installation. Read its triage first, then use an interview only when that
triage calls for one. The target's decision and verification rules still apply.

The skill owns the interview, session, viewer, and seed confirmation. Its helpers
are runnable with Python; its session records normally live under
`~/.local/share/seed-me/sessions/`. Keep the returned path. Do not create a confirmed
seed from an example or infer confirmation from a saved file's name.

Completion here means the human has confirmed the displayed seed and its file is
saved. That permits planning; it does not approve an unseen build brief. Continue
into planning under the user's instruction to carry out the change.

## 4. Prepare tink-sdlc in the target checkout

Select the actual target and an isolated worktree or clone. From Substrate, replace
`/absolute/path/to/isolated-target` below with that checkout's root. The initializer
previews changes, preserves project instructions, and refuses conflicting installs.

```sh
python3 .substrate-tools/tink-sdlc/scripts/init.py /absolute/path/to/isolated-target --check
python3 .substrate-tools/tink-sdlc/scripts/init.py /absolute/path/to/isolated-target
```

If the target already has tink-sdlc, first read its `_system/SDLC.md` and run its
status command. Do not reinstall or upgrade it during feature work. The installed
runtime and contracts govern that run.

Before the first implementation, configure `_system/verification.json` with the
repository's real checks. New installs deliberately start with no checks. Read the
installed `_system/SDLC.md` for its schema and preserve existing project policy.
For example, a repository whose full gate is `npm test` could use:

```json
{
  "require_tink": false,
  "checks": [{"argv": ["npm", "test"], "timeout_seconds": 120}]
}
```

This is a format example, not a recommendation for every repo. Use the actual test
command and sufficient timeout; confirm it discovers tests and fails for a known
incorrect result in a disposable test fixture or separate temporary checkout.
Do not deliberately break an active user's checkout. Run the chosen command
directly before approval; `sdlc.py verify` correctly refuses to run until its gate
is satisfied. The installer reporting “configured” is not proof that tests work.
Commands are argument arrays, not shell strings. The agent must
show the chosen checks in the brief before implementation. The installed runtime
validates them during verification; do not substitute a help command for tests.

Review the install diff in the isolated target checkout. Commit the intended
scaffold files, the router addition to `AGENTS.md`, and the configured checks as
an explicit setup commit on that branch. Include it in the eventual PR; it does
not approve the feature. Stage exact paths, preserving unrelated files. The
launcher is not a substitute for this commit. Runtime lock files such as
`runs/.<run>.lock` and `runs/<run>/.writer-lock` are not evidence: exclude those
exact runtime paths using the checkout's local Git exclude file
(`git rev-parse --git-path info/exclude`); untracked files also block archiving; do not ignore all run artifacts.

From the target checkout, read `_system/SDLC.md` and `stages/01-plan/CONTEXT.md`.
Inspect status before creating a run. A small change normally fits the light
profile; keep a bug fix classified as a bug because it needs a reviewed reproduction.
Use a run name chosen for the change:

```sh
python3 _system/scripts/sdlc.py status
python3 _system/scripts/sdlc.py new example-change --profile light --kind feature
python3 _system/scripts/sdlc.py stage example-change 1 --here --seed-contract /absolute/path/to/confirmed/seed-contract.md
```

The coordinator performs these launcher actions. Before starting the planning
session, save the actual user request, constraints and labelled defaults in
`runs/<run>/handoff.md`. Link any confirmed seed; omit the link when there is none.
Append the absolute handoff path to the launcher's short prompt, so a fresh session
can find the request without this conversation. Keep subsequent observations in
this same handoff.

Start the fresh planning session
with the prompt the launcher prints. It produces the concrete brief and checklist;
wait until that session has finished writing before presenting them for approval.
Keep one writer at a time. Record approval for the reviewed version, then open
the build. Follow the installed
guide for later stages, verification and independent review. Keep actual approval
sources; sample commands and test fixtures never supply approval.

For this basic setup, Seed Me is read from its cloned skill folder. The workflow
can open planning without Tink or tink-route installed. This path has fewer stage
skills than the earlier supervised trials; equivalent delivery quality is unproven.

Tink and tink-route are optional integrations in this scaffold. When absent, the
launcher reports that stage disciplines/routing were skipped. That is a reduced
setup, not a tested substitute for the skill-equipped trials. When present but
unconfigured, their failures may block launch: report the exact error and follow
the tool's setup instructions. Do not invent library approvals or hide failures.

## 5. Connect the work to the dashboard

Create a Markdown work record with TOML metadata and a short description.
A useful default is `~/.local/share/tink-substrate/work/<project>/<run>.md`.
Create the parent directories first. You can instead keep records in a directory
you version yourself; store the chosen absolute path only in the local config. Start
with the real title, project, owner and next action; link the run after creation.
Add a PR only when one exists. Test fixtures are synthetic, not reusable
decisions or live state for your new change.

```toml
+++
schema = 1
title = "Describe the change"
project = "target-project"
owner = "Planning agent"
next_action = "Prepare the brief and checklist for human review."
run = "example-change"
handoff = "runs/example-change/handoff.md"
+++
```

If a confirmed seed exists, copy it for the dashboard from its external session
into `runs/<run>/seed-contract.md` in the target checkout, without rewriting its
content or confirmation details. Keep the original session. Dashboard artifact
paths are relative to the target checkout and cannot point outside it.

Add `seed = "runs/example-change/seed-contract.md"` only when that file actually
exists and represents the confirmed seed. Never copy a historical decision into a
new work record.

From Substrate, select that file with `python3 -m tink_substrate init --work PATH
--checkout TARGET --trust-sdlc`. Use a separate `--config PATH` before `init` or
`serve` for a trial; this avoids replacing an existing selection. Inspect the
selected SDLC runtime before trusting it. Start `serve --port PORT` on an unused
port. Selection is read at server startup, so restart the owned server after a
selection change. Refresh does not switch projects.

## 6. Deliver and close

Follow [Finish a change](finish-a-change.md): verify and review the PR, save the
retrospective and independent archive at delivery, then record later feedback and
merge separately. The agent owns these steps during the run. The dashboard does
not watch GitHub or trigger them in the background.

## Use it without the entry skill

Give your agent the absolute path to this checkout and this request:

> Read /path/to/tink-substrate/AGENTS.md and
> /path/to/tink-substrate/docs/start-a-change.md. Use this workflow
> for [repo path] to accomplish [outcome]. Inspect existing instructions, worktrees
> and installed SDLC first. Preserve active work. Take the change through the
> required decisions, implementation, verification and PR review. Follow
> /path/to/tink-substrate/docs/finish-a-change.md before handing back. Merge only when I authorize it.

Pick one useful change in one repo for the first run. Keep a separate dashboard
configuration for each selected work item. No bulk installation or upgrade across
your repos is needed. Record the post-verification decision in the existing handoff or retro:
what worked, any demonstrated obstacle to the next change, and whether to proceed,
consolidate or re-scope. “No change needed” is a valid outcome. If installed tooling disagrees with its instructions, record
the exact conflict; do not silently upgrade it during feature work.

## What remains unproven

Earlier supervised changes used the author's skill-equipped setup. This
pinned basic path has not yet delivered a change or proved unattended delivery
or setup on a fresh machine. Seed Me, tink-sdlc, the agent host,
GitHub authentication and project build tools remain external requirements.

## Recover without starting over

- **Interrupted agent:** read the saved work record, target instructions, brief,
  handoff and current `sdlc.py status <run>`. Check the checkout and PR revisions.
  Resume the existing run; never recreate approval from remembered conversation.
- **Pinned SDLC:** text status is expected on 1.18.2. The dashboard labels it; use
  the installed status command for its decisions. Do not upgrade just for a badge.
- **Tink present but empty:** planning stops with `Skill ... not found in library`
  and `stage not opened`. Review the installed stage's skillset pin and use the
  documented Tink setup before retrying. Do not grant blanket trust, silently
  uninstall tools, or treat a blocked stage as opened.
- **Optional routing:** tink-route needs Tink and a TypeSafe API key. It is not
  required for this basic setup. Do not purchase or provision routing to begin.
- **Wrong dashboard selection:** use an explicit per-work `--config` and restart
  the server with that same config. Refresh does not select another work record.
- **Dirty checkout during archive:** preserve unrelated work. Commit only the
  intended evidence in its isolated checkout; do not clean or stash someone
  else's work to make the command succeed.

See [validation and limits](new-user-validation.md) for what was actually exercised.
