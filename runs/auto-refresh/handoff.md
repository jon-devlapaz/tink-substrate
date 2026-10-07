Outcome: New dogfood runs use checked current bundled tools; resumes keep exact saved versions.
Authority: The user reviewed the proposal in this chat and explicitly asked to branch, commit its implementation and deliver a clean PR. Stage 03 permits explicit execution of a reviewed proposal. No merge authorization.
Scope clarification: The three bundled components update automatically. Ambient optional Tink and tink-route are disabled by the run wrapper so they cannot change a run silently. Provisioning those tools is not included.
Evidence: Baseline and final results will be linked here.
Learning: Existing installer pins and installation hashes answer different questions; preserve explicit pinned installs while adding freshness at the run boundary.
Futures: Keep package assembly in one owner so dependency changes do not require two export implementations.
Decision: Proceed with the approved pre-run refresh behavior.
Next: Implement, verify, independently review, commit evidence, push PR and archive.
Skills: Features and Futures bounded the slice; principle-build-the-lever requires rerunnable checks; unslop guides user-facing text.
