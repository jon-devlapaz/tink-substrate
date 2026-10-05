# Entry skill trial

## Outcome

Added a repository-owned `tink-substrate` skill so the agent owns setup and delivery.
The README now starts with one installation and one request. Manual dashboard
configuration stays in the start guide. No runtime or SDLC changes were made.

## Evidence

- All 35 Substrate tests passed. Skill validation passed in a temporary environment.
- Tested the documented link installation twice: the second attempt preserves the
  existing destination instead of nesting a link. Resolved links reach both guides.
- A fresh agent used the skill on a disposable Python greeting repository. It
  obtained pinned tools, created an isolated checkout, installed SDLC, configured
  tests and opened planning without a human setup checklist.
- Runner probes passed good code, rejected broken code, and rejected zero tests.
- A separate planning agent produced a brief and checklist. The trial stopped at
  real human acceptance; no approval was invented and no feature was implemented.
- The dashboard status endpoint returned the selected trial and workflow state.
- Native Claude Opus 5.5 reviewed the skill and guides. Its findings led to the
  repeat-install guard, resume guidance, clearer host limits and external archive
  links that do not dirty the saved checkout.

## Obstacles and limits

The existing Tink integration supplied a nonexistent skill path and a mount command
missing its required JSON flag. The trial agent recovered using the installed
command's help and real approved library. No upstream or global settings changed.
This is a concrete remaining integration issue, not a reason to add another layer.

The trial used this machine's existing Tink library and permissions. It does not
prove a fresh machine, the reduced setup without Tink, full PR delivery, a real
Seed Me interview, or cross-session dashboard persistence. The independent planning
handoff had to carry the actual request and relevant file paths as the guide says.

## Decision

Keep the entry skill small and retain existing workflow ownership. The setup-to-
brief path worked. Next, use it for a real bounded change with actual human brief
acceptance and observe delivery and resume. Do not introduce more automation until
that use demonstrates a specific need.
