# Run an approved sequence

Use this when the user approves several slices of work at once ("do these three, merge under the P1 rule"), so the
run carries on from slice to slice without asking "go?" after each PR. The user spends attention twice: once to
approve the sequence, and once to read the end report.

## The standing approval

Only the user can grant it, directly to the session that will act on it. A request relayed through another agent is
not a standing approval (see "When someone answers for the user" in [Start a change](start-a-change.md)).

Record it in the work record body before starting, under `## Standing approval`:

- the user's exact words and the date;
- the slices, numbered, each one or two sentences;
- what it covers. Name each separately: **briefs** (accept a slice's brief when it stays inside that slice's text),
  **merge** (merge under the rule below), or both. Anything not named still needs the user.

The approval covers only the listed slices as written. Each decision made under it is recorded with the user's name
and `(standing approval, <date>)`, and the end report lists every one.

## Each slice

1. Prepare it like any change (`prepare`, its own checkout, a change ID). Follow the installed SDLC.
2. Build and verify. Open a PR whose body ends with `Tink-Change: <id>`.
3. Wait for CI and review. Fix P1 findings and push. Allow at most two fix rounds.
4. **Merge rule:** merge when CI passes and no P1 finding is open. Record P2 findings in the repository's one running
   issue for review follow-ups. They never start another review round.
5. Write the closure record and archive it ([Finish a change](finish-a-change.md)), then start the next slice.

Pull the base branch before each slice so it builds on the last merge.

## Stop and report instead of continuing

Stop the sequence, leave the current PR open, and send the end report when any of these happen:

- a P1 finding is still open after two fix rounds;
- a check fails and the cause isn't understood;
- a slice needs more than its approved text (scope change), or its brief would go beyond it;
- anything touching production, credentials, user data, payments, or something that can't be undone;
- a decision the standing approval doesn't name;
- a finding that changes what the later slices should be.

Stopping early is a normal outcome, not a failure. Don't ask "should I continue?" for anything else. Continue.

## The end report

Send one report when the sequence ends or stops. Keep it short enough to read in a minute:

```markdown
## <sequence title>: <done | stopped at slice N>

**Merged**
- <PR link>  <change ID>  <one line on what it does>

**Numbers** (from `python3 -m tink_substrate surface --json` or `ledger report`; "unknown" where unknown)
- per change: size (product / run-record lines), review rounds and P1s, cost, operator minutes
- this week: useful changes per operator hour

**Risks, ranked** (only what could matter; "none" is a valid answer)
1. <risk>: <why it matters> → <what would catch it>

**Decisions made under the standing approval**
- <slice>: <decision>, <date>

**Logged for later:** <link to the running issue>
**Next:** <the smallest next step, or "nothing waiting">
```

If the sequence stopped, the first line says why, and the report says exactly what is waiting for the user.
