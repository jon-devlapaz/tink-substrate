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

Clone this repository once, then link its entry skill into Codex:

```sh
git clone https://github.com/jon-devlapaz/tink-substrate.git
cd tink-substrate
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
skill_dest="${CODEX_HOME:-$HOME/.codex}/skills/tink-substrate"
if [ -e "$skill_dest" ] || [ -L "$skill_dest" ]; then
  echo "Already exists; inspect before changing: $skill_dest"
else
  ln -s "$PWD/skills/tink-substrate" "$skill_dest"
fi
```

Keep this clone: the skill reads the guides and runs the dashboard from it.
If the destination already exists, inspect it instead of replacing it.
Open a new Codex session in the project you want to change and ask:

> Use $tink-substrate to [describe one useful change].

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
