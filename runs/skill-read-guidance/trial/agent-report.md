# Agent report: add-sub trial

## Skill-loading steps
1. Guidance followed (AGENTS.md rule block compiled by tink at stage-1 launch, and stage CONTEXT "Stage skills"):
   "- principle-build-the-lever: ... (read: tink mount principle-build-the-lever --json --payload)"
   Command: `tink mount principle-build-the-lever --json --payload`
   Exit code: 0. Full skill text returned: yes (JSON, payload.content, 2458 chars, whole SKILL.md). stderr empty.
2. Routed skill named in launch prompt: none. The launch prompt was only "Begin stage 1 (plan) of SDLC run `add-sub`." No stage-open pick file existed (runs/add-sub/skills/ not created). tink-route not needed or run.
3. Before the stage-1 launch, AGENTS.md had no discipline rules block (the init router only). The rule appeared after `stage add-sub 1 --here`.
4. Note: the target's AGENTS.md rules listed only principle-build-the-lever. The `unslop` rule appears only in the user's global/other repo instructions, not in the target, so it was not loaded.

## Other guidance problems
- docs/start-a-change.md says the launcher prints a "short prompt" to which the coordinator appends the handoff absolute path. The printed prompt gave no handoff path, which I had to append myself mentally. Minor. The handoff was written before launch, as the guide says.
- The `stage ... --here` launcher left the compiled rules in AGENTS.md as an uncommitted modification and `runs/add-sub/*` untracked, even though SDLC.md says the launcher "commits runs/<run>". I did not commit them (not asked; just reported).
- The `sdlc.py stage` output printed "exit=" blank in my pipe only because of my own PIPESTATUS use under zsh; not a tool issue.
- First check config attempt `unittest discover -s tests -t .` failed ("Start directory is not importable"): tests/ has no __init__.py. This is a target-repo quirk, not a guidance error; fixed by dropping `-t .`. Confirmed discovery finds 1 test, and a known-wrong calc.py in a temp copy gives exit 1.
- start-a-change.md assumes Codex Desktop; I ran from Claude Code. Not an obstacle.
- The guide's "Seed Me triage" was not run via the SKILL path because the request is a clear execution request (skill says proceed without interview); no seed, `--seed-contract` omitted.

## Setup done
init.py --check, init.py (exit 0), verification.json configured, router/scaffold committed as 80179fb, local git exclude for run lock files, run `add-sub` (light, feature) created, stage 1 opened with `--here`, handoff at runs/add-sub/handoff.md, brief.md and checklist.json written (2 items with checks). Status: stage 3 pending. No decide, no stage 3, no dashboard, no PR.

## Workarounds count: 0
(The `-t .` change was a fix to my own check command, not to guidance.)
