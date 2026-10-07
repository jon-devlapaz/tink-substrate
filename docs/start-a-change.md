# Start a change

Use this when a fresh person or agent starts a change from Substrate. The dashboard
is packaged here. The installed skill includes pinned Seed Me and tink-sdlc sources.
An agent host is still required. This is not yet a one-command software factory.

## 1. Check the basics

The first path targets macOS, one existing Git repository, and an agent host that
loads skills from a directory, such as Codex or Claude Code. Open the target
project in that host and ask the agent to use the installed tink-substrate skill.
The agent reads that project's instructions before choosing a separate checkout.
One Claude Code run has reached an open PR this way; the Codex Desktop handoff is
still to be tested. Host permissions may require access to the selected checkouts,
evidence directories and network; record actual prompts rather than assuming the
author's permissions. Linux is outside the first user trial.

The public repository is `https://github.com/jon-devlapaz/tink-substrate`
under MIT. Obtain it with:

```sh
git clone https://github.com/jon-devlapaz/tink-substrate.git
cd tink-substrate
python3 scripts/install_skill.py
```

The default destination is Codex's skills directory (`$CODEX_HOME/skills`, else
`~/.codex/skills`). For another host, pass its skills directory, for example
`--destination ~/.claude/skills/tink-substrate` for Claude Code.

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
Run the commands below from the installed skill directory (the package root) unless
another directory is named. Source development must first install committed HEAD to a separate trial directory.

## 2. Prepare current tools, or resume the existing run

For a new run, follow [Current tools for a new run](automatic-tools.md) before
starting Seed Me. It refreshes checked sources, prepares the isolated target and
creates the run. Read the returned package's instructions and use its workflow
wrapper. For a matching prepared run, that same command validates and returns
its saved versions without an update.

An older run without `tools.json` keeps its installed workflow and the package it
started with. The remaining manual setup commands below describe that older
pinned path; do not use them to replace a prepared run's tools or create it again.
The pinned installer and `--tool-cache` remain available for reproducible source
installation. They export committed Git objects and retain licenses.

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
`~/.local/share/seed-me/sessions/`. Follow the bundled Seed Me version's save rules and keep its returned handoff path. Seed Me 2.0 saves the seed and
ledger together in the session folder outside the checkout. Do not create a confirmed
seed from an example or infer confirmation from a saved file's name.

Completion here means the human has confirmed the displayed seed and its file is
saved. That permits planning; it does not approve an unseen build brief. Continue
into planning under the user's instruction to carry out the change.

### When someone answers for the user

Seed Me's decisions and the brief approval belong to the user. Two cases occur:

- **Relayed user.** The user answers through another agent or person. Pass each
  question and the user's words through unchanged. The session stays a human
  session; record only what the user actually said.
- **Stand-in.** An agent or person decides in the user's place. Only the user can
  appoint one; record that appointment in the handoff. Run Seed Me in its agent
  mode: it records every answer as `simulated` and saves
  a simulated seed under that version's save rules, which cannot become a confirmed seed. Keep that
  file outside the checkout, label it as proposals in the handoff, and omit
  `--seed-contract` at stage 1. Record each later decision under the stand-in's
  name, for example `coordinator stand-in for <user>`, never as the user. These
  decisions let a trial continue; they are not human approval. The delivery report
  and retro say which decisions came from the stand-in. Merge still needs the user.

Later approvals follow the same rule. If feedback extends the scope after review,
amend the brief and checklist, show the changed text to the user, and record
approval of that text. A request such as "fix them" asks for the change; it does
not approve wording the user has not seen. Merge only on authorization that the
merging session received from the user directly. If it arrived through another
agent, hand the merge back to the session that talks with the user.

## 4. Prepare planning in the target checkout

For a prepared run, the current scaffold and run already exist. Configure the
actual project checks, commit the setup and `tools.json`, and open stage 1 through
the workflow wrapper in [Current tools for a new run](automatic-tools.md). Then
follow the handoff and human review steps below. Skip manual initialization and
`sdlc.py new` in this section. Use the wrapper for later SDLC commands too.

### Manual pinned setup

Select the actual target and an isolated worktree or clone. From Substrate, replace
`/absolute/path/to/isolated-target` below with that checkout's root. The initializer
previews changes, preserves project instructions, and refuses conflicting installs.

If you create the worktree with `git worktree add -b <run> PATH origin/main`, Git
sets `origin/main` as the new branch's upstream. With `push.default=upstream`, a
plain `git push` then updates `main`. Remove it at once with
`git -C PATH branch --unset-upstream`, and push the run branch later with
`git push -u origin <run>`.

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
In a linked worktree that command names the repository's shared exclude file, so
the entries also apply to the main checkout and every other worktree.

From the target checkout, read `_system/SDLC.md` and `stages/01-plan/CONTEXT.md`.
Inspect status before creating a run. A small change normally fits the light
profile; keep a bug fix classified as a bug because it needs a reviewed reproduction.
Use a run name chosen for the change:

```sh
python3 _system/scripts/sdlc.py status
python3 _system/scripts/sdlc.py new example-change --profile light --kind feature
python3 _system/scripts/sdlc.py stage example-change 1 --here --seed-contract /absolute/path/to/confirmed/seed-contract.md
```

With `--seed-contract`, the launcher copies the seed to `runs/<run>/seed-contract.md`
and binds that copy's hash to later approvals and verification. Do not copy or
edit it by hand.

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

If a confirmed seed exists, stage 1 has already copied it to
`runs/<run>/seed-contract.md` in the target checkout. Keep the original session.
Dashboard artifact paths are relative to the target checkout and cannot point
outside it.

Add `seed = "runs/example-change/seed-contract.md"` only when that file actually
exists and represents the confirmed seed. Never copy a historical decision into a
new work record.

From Substrate, select that file with `python3 -m tink_substrate init --work PATH
--checkout TARGET --trust-sdlc`. Use a separate `--config PATH` before `init` or
`serve` for a trial; this avoids replacing an existing selection. Inspect the
selected SDLC runtime before trusting it. Start `serve --port PORT` on an unused
port. Selection is read at server startup, so restart the owned server after a
selection change. Refresh does not switch projects.

Edits to the selected work record, checkout or run need no restart. The page and
`status --url` show the last snapshot until someone presses **Refresh sources**;
reloading the page does not re-read. An agent that edits the record can refresh
the view itself by requesting `/api/snapshot?refresh=1` from the server.

## 6. Deliver and close

Follow [Finish a change](finish-a-change.md): verify and review the PR, save the
retrospective and independent archive at delivery, then record later feedback and
merge separately. The agent owns these steps during the run. The dashboard does
not watch GitHub or trigger them in the background.

## Use it without the entry skill

Run the installer first. Give your agent the absolute path to the installed
skill directory and this request (replace `/path/to/tink-substrate` with that path):

> Read /path/to/tink-substrate/SKILL.md and
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
or setup on a fresh machine. The agent host, interpreter, GitHub authentication
and project build tools remain external requirements.

## Recover without starting over

- **Interrupted agent:** read the saved work record, target instructions, brief,
  handoff and current `sdlc.py status <run>`. Check the checkout and PR revisions.
  Resume the existing run; never recreate approval from remembered conversation.
- **Pinned SDLC:** a workspace installed from this pin has 1.20.0 and structured status; an older workspace gives text status only. The dashboard labels which one it read; use
  the installed status command for its decisions. Do not upgrade just for a badge.
- **Tink present but empty:** planning stops with `Skill ... not found in library`
  and `stage not opened`. Review the installed stage's skillset pin and use the
  documented Tink setup before retrying. Do not grant blanket trust, silently
  uninstall tools, or treat a blocked stage as opened.
- **Optional routing:** tink-route needs Tink and a TypeSafe API key. It is not
  required for this basic setup. Do not purchase or provision routing to begin.
- **Wrong dashboard selection:** use an explicit per-work `--config` and restart
  the server with that same config. Refresh does not select another work record.
- **Dashboard shows old record contents:** press **Refresh sources** or request
  `/api/snapshot?refresh=1`. Do not restart the server for this.
- **Dirty checkout during archive:** preserve unrelated work. Commit only the
  intended evidence in its isolated checkout; do not clean or stash someone
  else's work to make the command succeed.

See [validation and limits](new-user-validation.md) for what was actually exercised.
