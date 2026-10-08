# Run an approved sequence

Use this when the user wants several slices of work done in a row without being asked "go?" after each PR. The user
spends attention twice: once to approve the sequence with its finished briefs, and once to read the end report.

## 1. Draft every brief, then ask once

Agree the slices with the user. Then, for each slice, prepare its run in its own isolated checkout (with its change ID)
and write its brief under the installed SDLC, as for any change. Present all the finished briefs together. The user
approves the sequence by accepting those briefs and saying what they authorize.

Only the user can grant this, directly to the session that will act on it. A request relayed through another agent is
not a standing approval (see "When someone answers for the user" in [Start a change](start-a-change.md)).

## 2. Keep one sequence record

Write `~/.local/share/tink-substrate/work/<project>/sequence-<name>.md`, next to the slices' work records:

- the user's exact words and the date;
- the slices, in order, each with its run, checkout, change ID, and (later) PR;
- what the approval covers. Name each part: **briefs** (the briefs as presented), **merge** (merge each PR under the
  rule below). Anything not named still needs the user.

Each slice's handoff names the sequence record's path and quotes the approval line it relies on. Record each decision
made under it with the user's name and `(standing approval, <date>, <sequence record>)`.

tink-sdlc 1.23.0 and later let a human authorize a merge this way. With an older installed tink-sdlc ("only a human
merges it"), the approval can't cover merging: stop at each merge and ask. The release gate still applies: the user's
authorization, current required CI and verification, and whatever the forge requires (branch protection, required
reviews). If the forge refuses the merge, that is a stop.

## 3. Each slice

1. Bring the slice up to date before building. Fetch the remote and rebase the slice's branch (which so far holds
   only its planning records) onto the updated remote base, so it includes every earlier slice's merge. The user's own
   checkout is never pulled or changed. If the rebase conflicts, stop.
2. Build and verify under the installed SDLC. Open a PR whose body ends with `Tink-Change: <id>`.
3. Wait for CI and review. Fix P0 and P1 findings, verify again under the installed SDLC, and push. Allow at most two
   fix rounds.
4. Before merging, write the retro, commit the evidence and save the delivery archive, as
   [Finish a change](finish-a-change.md) describes.
5. **Merge rule:** merge when every required check passes, the SDLC verification is current for the PR head, and no P0
   or P1 finding is open. Write P2 findings into the slice's handoff for the end report. If the repository already
   keeps a running issue for review follow-ups, add them there too. P2s never start another review round.
6. After the merge, write the closure record and save the closure archive. Inside a sequence, the delivery and merge
   reports go into the records and the end report instead of separate messages.

## 4. Stop and report instead of continuing

Stop the sequence, leave the current PR open, and send the end report when any of these happen:

- a P0 or P1 finding is still open after two fix rounds;
- a required check fails and can't be cleared within the slice, whatever the cause (a known outage counts);
- a slice needs more than its approved brief (scope change);
- anything touching production, credentials, user data, payments, or something that can't be undone;
- a decision the approval doesn't name, or the forge refuses the merge;
- a finding that changes what the later slices should be.

Stopping early is a normal outcome, not a failure. Don't ask "should I continue?" for anything else. Continue.

## 5. The end report

Send one report when the sequence ends or stops. Keep it short enough to read in a minute. Fill the per-change numbers
from `python3 -m tink_substrate --config <slice config> surface --json` for each slice, and the weekly number from
`ledger report`. Write "unknown" where a number is unknown.

```markdown
## <sequence title>: <done | stopped at slice N because …>

**Merged**
- <PR link>  <change ID>  <one line on what it does>

**Numbers**
- <change ID>: <product / run-record lines>, <review rounds, P1s>, <cost>, <operator minutes>
- this week: <useful changes per operator hour>

**Risks, ranked** (only what could matter; "none" is a valid answer)
1. <risk>: <why it matters> → <what would catch it>

**Decisions made under the standing approval**
- <slice>: <decision>, <date>

**Logged for later:** <P2 findings, or a link to the running issue>
**Waiting for you:** <exactly what, or "nothing">
**Next:** <the smallest next step>
```
