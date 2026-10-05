# Lessons behind the workflow

These observations informed the current design. They are not extra approval rules.

- **Finish planning before asking for approval.** A planner changing the brief while
  a person reviews it can invalidate the accepted version. Keep one writer and
  hand over a stable artifact.
- **Preserve evidence during review.** Give independent checks their own output
  locations so a rerun does not overwrite what is being reviewed.
- **Test the real boundary.** Passing model or unit checks can miss interactive
  behavior. Use the actual interface when that is part of acceptance.
- **Check observation tools too.** A generated preview can introduce an apparent
  defect absent from the application. Compare it with the underlying evidence.
- **State what a supervised run needed.** Successful delivery with an experienced
  coordinator does not prove a new person can start from the README alone.
- **Distinguish source fixes from installed fixes.** An open PR or local patch is
  not an update to the target's installed tools.
- **Keep the next step small.** Fix a demonstrated obstacle, verify it, and stop.
  A successful run can justify no workflow change.

The public snapshot intentionally excludes personal trial records and historical
approvals. Tests use synthetic records. The original development history is
retained privately by the maintainer.
