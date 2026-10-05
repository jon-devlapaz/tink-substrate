# tink-substrate

Take a hunch to a reviewed pull request with your agents, while keeping the work
understandable and the software easy to change.

**Features and Futures is the guiding practice:** build one useful change, check
its real behavior, and use what you learn to keep the next change easy. Add process
only when it solves an observed problem. Stop consolidating when that problem is
resolved.

Substrate gives you and your agents a shared local view of the work. Seed Me helps
clarify the idea. tink-sdlc holds the brief, decisions and verification evidence.
The agent performs the work; you choose the direction and make required decisions.

## Start here

Install from a reviewed clone with Python 3.11 or newer:

```sh
git clone https://github.com/jon-devlapaz/tink-substrate.git
cd tink-substrate
python3 scripts/install_skill.py
```

The installer exports committed HEAD (not uncommitted or untracked files),
copying the skill, guides, dashboard and archive code into your Codex
skills directory. It downloads the pinned Seed Me and tink-sdlc sources and includes
their licenses. It refuses to replace an existing installation. The resulting
package no longer needs this clone or your personal Tink setup.

Open a new Codex session in the project you want to change and ask:

> Use $tink-substrate to [describe one useful change].

For a different host, use `--destination /path/to/its/skills/tink-substrate`.
Only Codex is the current onboarding target. For updates, install to a review directory outside the host's skills directory.
After validation, move the old installation outside that skills directory for
backup and move the new copy to its original location. Keep only one discoverable
`tink-substrate` skill. Run records are separate and remain unchanged.

This entry point is being tested in supervised trials. It directs the agent to handle
tool setup, a separate checkout, the work record and dashboard,
then take the change through planning, implementation, checks and review. You
clarify the outcome, approve the brief and decide when to merge. The agent saves
a retrospective and archive before handing back the PR.

You need macOS, Python 3.11+, Git, Bash, Codex Desktop and your project's build tools.
PR delivery also needs authenticated GitHub CLI access. The agent reports any
missing prerequisite. Your host may ask for permission to access the checkouts,
local records or network. If it cannot keep the dashboard running, the agent gives
you one command to start the configured view. Existing project rules still apply.

## Check the version

From the source checkout, run:

```sh
python3 -m tink_substrate --version
```

After installing the package, you can also run:

```sh
tink-substrate --version
```

Both print `tink-substrate <package version>`, for example `tink-substrate 0.1.0`.
No configuration or subcommand is required.

## What works today

The dashboard and archive command work today. The entry skill delegates setup to
the agent using the existing guides. A complete new-user run from this entry point
to a reviewed PR is still being tested; this is a supervised workflow.
The dashboard does not dispatch agents or react to GitHub changes by itself.

For manual setup or troubleshooting, see [Start a change](docs/start-a-change.md).

## Follow the work

The agent gives you a local dashboard URL. It shows the selected work item,
checkout and worktrees, linked PR, workflow status and saved artifacts by stage.
It reads those sources when refreshed; it does not discover every project or
establish which agent owns a worktree. The pinned SDLC shows text status.

For manual dashboard commands, see [Start a change](docs/start-a-change.md#5-connect-the-work-to-the-dashboard).

## Keep what the run taught you

The agent writes `runs/<run>/retro.md` before delivering the PR and saves an
independent snapshot under `~/.local/share/tink-substrate/archive/<project>/<run>/`.
Later feedback or merge is recorded separately. This happens when the agent works
on the run, not automatically when GitHub changes state.

Archives contain committed run files and source. They exclude ignored files,
full agent conversations and costs, and are not an off-machine backup.
See [Finish a change](docs/finish-a-change.md) for details and manual commands.

## For contributors

Running from its checkout needs no package installation. To install a reviewed
copy without changing your system Python:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/tink-substrate --help
.venv/bin/python -B -m unittest discover -s tests
```

The package has no runtime Python dependencies or frontend build step. Installation
uses setuptools as a build dependency and needs network access to obtain it
unless it is already available in a configured package cache. Agent access, GitHub access and target build
tools remain external. Tink skill management and paid routing are optional setup
paths; see the start guide before enabling them.

## Design and evidence

- [System design](docs/system-design.md)
- [Lessons behind the workflow](docs/lessons.md)
- [Setup validation and remaining release work](docs/new-user-validation.md)
- [Guidance for agents](AGENTS.md)

The direction draws on Kent Beck's Features and Futures,
[ICM Architect](https://github.com/RinDig/icm-architect), and engineering accounts
from [Anthropic](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
and [OpenAI](https://openai.com/index/harness-engineering/). These inform the design;
observed runs determine what this package can claim.
