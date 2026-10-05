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

## Current status

Intended for a first supervised trial on macOS with Codex Desktop; that
complete handoff is not yet tested.
**Publication target:** [jon-devlapaz/tink-substrate](https://github.com/jon-devlapaz/tink-substrate), under the [MIT license](LICENSE).
This is a publication candidate. The GitHub clone path, remote CI and complete
new-user workflow still need validation after the first push. See [validation](docs/new-user-validation.md).

The dashboard and archive command work today. They do not dispatch agents, watch
GitHub in the background, approve work or merge changes. Earlier supervised deliveries
used the author's existing tools and coordinator help.

## Obtain the package

After publication, clone the public repository:

```sh
git clone https://github.com/jon-devlapaz/tink-substrate.git
cd tink-substrate
```

This clone path is not yet independently verified; publication and CI are pending.
For a pre-publication evaluation, clone a reviewed local repository with its history.

## Start one change

You need Python 3.11+, Git, Bash, an agent host and the target repo's build tools.
For PR delivery, you also need the GitHub CLI (`gh`) authenticated to the intended
account. Project permissions and approval rules still apply.

Follow [Start a change](docs/start-a-change.md). It covers public tool revisions,
setup, real verification commands, human decisions and recovery. It keeps existing
repo instructions and installed workflows intact.

Give your agent this request, replacing the two paths and outcome:

> Read /path/to/tink-substrate/AGENTS.md and
> /path/to/tink-substrate/docs/start-a-change.md. Use that
> workflow for /path/to/my-repo to accomplish [one outcome]. Preserve active work.
> Carry it through the required decisions, implementation, verification and a
> reviewed PR. Follow /path/to/tink-substrate/docs/finish-a-change.md to save
> the retro and archive.
> Use Features and Futures to decide whether to proceed or consolidate after
> verified work. Merge only when I authorize it.

Seed Me's triage determines whether an interview is useful. A concrete execution
request does not need a fabricated seed or another interview. A required build
brief still needs actual human acceptance.

## See the same work as your agent

From the Substrate checkout, select a saved work record and its target checkout.
The start guide explains where to create the record. Test fixtures are synthetic
and must not be selected as real work.

```sh
python3 -m tink_substrate --config /path/to/my-selection.json init --work /path/to/work.md --checkout /path/to/target-checkout --trust-sdlc
python3 -m tink_substrate --config /path/to/my-selection.json serve --port 7871
```

Open **http://127.0.0.1:7871**. Keep the terminal running. Use an unused port when
another view is running. To change an existing selection, pass `init --replace`,
then restart its server with the same config. Refresh only updates the sources.

`--trust-sdlc` permits running the selected checkout's SDLC status command. Inspect
that runtime first. Without this flag, Git and GitHub work but workflow status is
unavailable. API 1 supplies structured status; an older runtime that explicitly
rejects `--json` supplies labelled text. Failures remain visible.

The view shows one work item, its checkout and worktrees, one linked PR, workflow
status and saved artifacts grouped by stage. It does not discover every project
or establish which agent owns a worktree. Sources have timestamps and are read
separately; an old snapshot is not proof of current state.

Agents can read the same cached snapshot, or collect a fresh one:

```sh
python3 -m tink_substrate status --url http://127.0.0.1:7871
python3 -m tink_substrate --config /path/to/my-selection.json status
```

## Keep what the run taught you

The agent follows [Finish a change](docs/finish-a-change.md) before handing back a
ready PR. It writes `runs/<run>/retro.md`, commits the evidence, and archives it:

```sh
python3 -m tink_substrate archive --checkout /path/to/target-checkout --project my-repo --run my-change --phase delivery
```

Later feedback or merge belongs in `runs/<run>/closure.md`, saved with
`--phase closure`. This happens when the agent works on the run, not automatically
when GitHub changes state.

Archives live under `~/.local/share/tink-substrate/archive/<project>/<run>/`.
Each new snapshot holds readable committed run files, source, revision metadata
and checked hashes. Earlier snapshots stay intact. Ignored files, full agent
conversations and costs are excluded. Copy needed seed evidence into the run
before committing; its external session is not captured automatically. A local
archive is not an off-machine backup or approval.

## Install and test this package

Running from its checkout needs no package installation. To install a reviewed
copy without changing your system Python:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/tink-substrate --help
python3 -B -m unittest discover -s tests
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
