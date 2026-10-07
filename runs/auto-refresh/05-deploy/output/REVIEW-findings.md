# Independent review

Reviewer: fresh review_refresh subagent, read-only comparison against origin/main.
Initial reviewed candidate: 1630943. Three Important findings were reproduced:
- Default stage worktrees lost the recorded checkout identity.
- A second prepared run could replace the first run's shared workflow.
- Fresh stage prompts did not carry the saved package and wrapper instructions.

Rechecked candidate: da02d10. All three have behavioral regressions. The wrapper
keeps stages in the selected isolated checkout, refuses a second prepared run
there, and prints a final stage prompt with the saved package, tools receipt and
bundled-only boundary. No actionable findings remain in the bounded recheck.
Reviewer checks: 18 preparation tests and five installation tests passed.
Limits: review is advisory, not authenticated code-owner approval. The reviewer
did not repeat live-source or fresh-agent trials. The author separately ran the
live-source and real-dependency candidate probes; their limits remain explicit.
