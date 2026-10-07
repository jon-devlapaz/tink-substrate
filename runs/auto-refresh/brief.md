# Refresh tools before a dogfood run

## Problem and outcome
Substrate hardcodes dependency commits. Installation integrity does not establish freshness, and an existing target scaffold can override bundled tools. The user asked to implement the reviewed pre-run refresh proposal, commit it, and deliver a verified PR using Features and Futures.

## Acceptance criteria
- Before a new run, resolve current main for Substrate, Seed Me and SDLC from their fixed public repositories. Require the designated CI workflow to have succeeded on that exact commit. Pending, failed, missing, malformed or unavailable evidence refuses startup without falling back.
- Export committed objects into a separate per-run package, retain licenses and hashes, and exercise Seed Me, SDLC and the dashboard together before changing the target.
- Prepare current SDLC in a clean isolated target before creating the run. Preserve verification settings and project-owned pins. Customized managed files refuse the upgrade. Do not change an existing run or global installation.
- Save versions, exact commits, checks, package path and checkout identity with the run. Resume validates that package and target scaffold without network or resolving newer versions.
- Supply a workflow command that uses the run package and suppresses ambient optional Tink/routing integrations. This first slice automatically updates the three bundled components; optional global tools are not silently installed, updated or used.
- Keep the existing manual pinned installer available for reproducible installation and source tests. No background updater, global tool replacement, automatic approval, merge or deployment.

## Approach
Add prepare and workflow commands. A single package builder supports explicit pins and resolved pre-run commits. The installed entry skill calls prepare before discovery and uses the returned package's instructions and workflow command. New runs refresh; matching runs resume. The target must be a clean, explicitly selected isolated checkout for initial preparation.

## Risks and verification
A moving main or incomplete CI must stop rather than choose older code. Compatibility smoke checks cannot prove interview quality or finished-work improvement. Checks use real temporary Git repositories, independently advancing upstream commits, CI failure cases, interruption/tampering, immutable resume and a real copied-package smoke test. Run the project suite, installed CLI checks and an independent review. Keep all required human planning and release gates.

## Features and Futures
Smallest useful slice: current bundled tools before a new run, frozen tools on resume. Uncertainty: whether current component sources work together outside personal checkouts. Resolve it with the copied-package checks and a recorded live upstream probe. Preserve the existing pinned install API, work records, dashboard API and active runs. Stop after this boundary works; optional-tool provisioning remains a separately testable next change.
