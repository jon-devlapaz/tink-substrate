# `surface --json`

One read-only JSON for the selected change. It's what a human surface (Tinkery) renders, and what an agent can read
to answer "what happened?". It writes nothing, and it exits 0 for every expected absence.

```bash
python3 -m tink_substrate surface --json [--ledger PATH]
```

It uses the selection saved by `init` (`--config` picks another one). The schema is `tink-surface/1`:

| Key | Contents |
| --- | --- |
| `selection` | `status`: `ok`, `missing` or `unavailable`, with an `error`, and a `fix` command when it isn't `ok` |
| `change` | `title`, `project`, `next_action`, `run`, `pr`, `change_id` (from `runs/<run>/tools.json`), `ledger_key` (`owner/repo#N`), and `link`: `change_id`, `pr` or `none` |
| `brief` | The seed contract, else the run's `brief.md`, else the work-record body: `{status, label, relative_path, text}` |
| `workflow` | The tink-sdlc state: `{status, error, data: {format, verification_status, next_action, gates, decisions, checklist: {total, passed}}}` |
| `pr` | `{status, error, data: {number, state, draft, ci, review_decision, merged_at, head_matches_checkout}}` |
| `needs_you` | Consequential items only, each `{kind, text}`. `kind` is one of: `source` (unavailable), `gate` (a pending, stale or changes-requested gate, or failed verification, while the PR isn't finished), `ci` (failed on an open PR), `review` (changes requested), `p1` (open PR with P1 findings) |
| `notes` | Everything else that's worth knowing but needs no decision |
| `ledger` | `{status: ok, missing or unavailable, as_of, row, week}`. `row` holds the change's `outcome`, `times`, `size`, `review`, `operator`, `cost` and `config`. `null` means unknown, never zero. `week` holds this ISO week's `merged`, `useful`, `covered`, `operator_hours_c5` and `useful_per_hour` per cap. `useful_per_hour` is `null` and `suppressed` gives the reason when fewer than 5 changes have operator data. |

The ledger row is found by the run's change ID first, then by the record's PR. If both exist and point at different
changes, the ledger is `unavailable` rather than guessed. A half-written last ledger line is ignored, because the
daily update may be appending; any other bad line makes the ledger `unavailable`.
