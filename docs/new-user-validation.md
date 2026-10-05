# Validation and release limits

## What has been checked

The setup instructions were exercised in temporary directories on macOS with
Python 3.13 and 3.14. A fresh native Claude session independently followed a draft
using a restricted PATH and scratch configuration. These checks shared an existing
OS and installed interpreters; they were not a fresh-machine test.

- Public clones reached Seed Me `58878b5794ca04a5ec0ba62027faadabfe7ca925`
  (1.17.1) and SDLC `328a2304b9af703dd846666757d6ffd1166df470` (1.18.2),
  both on merged public history.
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

## What is not established

The basic path has not delivered a complete user change through PR review and
closure. A Seed Me interview and the full Codex Desktop handoff still require a
real user trial. The historical skill-equipped trials do not prove equivalent
outcomes with optional skills absent.

The first GitHub clone and remote CI are pending publication. CI is configured for
Python 3.11 on Linux and 3.14 on macOS; configured jobs are not passing results.
Host permissions may require access to chosen paths and the network. No claim is
made for unattended operation, all repositories or all agent hosts.

## Publication preparation

The owner selected public `jon-devlapaz/tink-substrate` and MIT. This clean snapshot
contains the runtime, tests, CI and user-facing documentation. Personal work records,
private-project references, historical approvals and the original Git ancestry are
excluded. Original history and review evidence are retained privately.

A native Claude publication review covered the original candidate and reachable
history. This cleaned candidate requires its own content check before pushing.
The package license applies to this repository. Workflow dependencies are obtained
separately from their public repositories and retain their own source and terms.

## Next proof

After publication, follow the actual GitHub README in a fresh session, complete a
bounded change with real approvals, resume once after interruption, and save its
reviewed PR and retrospective. Record each intervention. Change the system only
where that run demonstrates a need.
