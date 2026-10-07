# Finish a change

The agent owns these steps as part of each authorized Substrate run. Do them when
delivering a ready PR, without another reminder. These are completion instructions,
not a background service or a replacement for the target repo's SDLC contracts.

## At PR-ready delivery

1. Confirm the reviewed candidate, current verification, PR head and checks. Fix
   failures within scope. State missing evidence or pending decisions plainly.
2. Write `runs/<run>/retro.md`. Keep it proportional: outcome and PR link; evidence
   and its limits; failures and repairs; manual interventions; what made the next
   change harder or easier; and the smallest justified next step. Separate human
   feedback from automated checks. Reuse links to existing logs instead of copying
   them. A successful run can justify no workflow change.
3. Commit the run evidence in its isolated checkout. Push the requested PR changes
   and check the final head. Do not include unrelated work to satisfy the archiver.
4. From Substrate, save the committed run:

   ```sh
   python3 -m tink_substrate archive --checkout /absolute/path/to/checkout --project repo-name --run run-name --phase delivery
   ```

5. Confirm the command succeeds; link its returned path and the retro in the external work
   record, so the archived checkout remains clean. Update the dashboard's next action. Report delivery separately
   from human acceptance or merge. If archiving fails, retain the files and report
   the failure; do not claim the run was saved independently.

## After feedback, merge or cancellation

Record the actual feedback and outcome in `runs/<run>/closure.md`: PR URL, merge
revision or cancellation, observed checks, remaining limits, and any follow-up.
Do not revise the original delivery archive to make it look complete earlier.

Commit the closure record in an appropriate documentation branch or local evidence
checkout; do not push directly to a protected main branch or reopen product code
just to store it. If the run branch was kept after merge, its checkout works: commit
there and push that branch, so the record survives removing the worktree. That
commit stays off `main`; say so in the report. No extra documentation PR is
required unless the repo requires one. Then run the same archive command with
`--phase closure`. Update the shared work record to show completion or the real
remaining action. Cleanup of worktrees requires a separate inventory and proof
that their work is preserved.

Before removing the checkout the dashboard reads, stop that dashboard, or select a
checkout that remains with `init --replace` and restart it. Otherwise it keeps
showing its last snapshot, and a refresh reports Git as unavailable.

Leave the user's main checkout as it is after merge; it may hold other work. Report
that it is behind the merge and pull only when the user asks.

## What the archive proves

Default home: `~/.local/share/tink-substrate/archive/<project>/<run>/`.
Override with `--root /path/to/archive`. Keep it outside the target checkout.
Each invocation makes a new timestamped directory with:

- `runs/<run>/`: readable committed run files, including the retro or closure.
- `source.tar`: Git's archive of the recorded commit; Git export attributes apply.
- `metadata.json`: source revision, checkout, phase, time and capture limits.
- `SHA256SUMS`: verified file hashes.

The command refuses dirty checkouts, missing or empty required records, and links
inside the run. It reads Git objects and does not run project scripts. It does not
capture ignored files, agent conversations, costs, or live forge state. Save needed
observations in the committed run first. Hashes establish snapshot integrity,
not correctness, approval or a backup on another machine.

An idle agent will not notice a later merge automatically. Resume the run with the
merge or feedback request; the agent then performs closure. A GitHub event hook can
be considered later if this manual handoff becomes a demonstrated problem.
