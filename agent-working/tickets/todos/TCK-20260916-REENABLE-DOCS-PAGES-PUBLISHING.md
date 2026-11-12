---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING
phase: open
date: 2026-09-16
tags: [documentation, process-improvement]
---

# TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING

## Title
Re-enable GitHub Pages docs publishing once the docs site is ready to publish a first version

## Status
BLOCKED

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Placeholder-by-design, filed at the user's request 2026-09-16 alongside
`TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW`, so that temporarily disabling the docs deploy
workflow does not quietly become permanently forgetting it.

**Why it is blocked:** the user's reasoning, verbatim in substance — *the main logic is still being
developed and is not yet ready to publish the first version*. Enabling GitHub Pages today would
publish a docs site that does not yet represent the project. This is a deliberate scheduling
decision, not an oversight or a defect.

**Current state:** `gh api repos/:owner/:repo/pages` returns **404** (Pages not enabled), and
`.github/workflows/deploy-docs.yml` has been narrowed so it no longer fires on push to `main` —
see the disable ticket for the full diagnosis, including that the failure was invisible for days
because no PR ever exercises that lane.

## Scope
When the docs are ready to publish:

- Enable GitHub Pages for the repository (a settings change, and the user's call — not an agent's).
- Restore `deploy-docs.yml`'s `push: branches: [main]` trigger, reverting the disable.
- Verify an actual published page renders, not merely that the workflow went green — a successful
  deploy step is not evidence the site is correct or reachable.
- Check whether anything in the repo already assumes a published site exists (README badges,
  cross-links) and reconcile it.

## Out of Scope
- Any work on the docs content itself. This ticket is only the publishing mechanism.
- Re-enabling early "because CI is red". The lane is disabled, not failing, so there is no CI
  pressure to act on — that was the point of disabling rather than deleting.

## Acceptance Criteria
- [ ] GitHub Pages is enabled and `gh api repos/:owner/:repo/pages` returns a real site, not 404.
- [ ] `deploy-docs.yml` fires on push to `main` again, and its in-file disable comment is removed.
- [ ] A published page is fetched and inspected — verified as rendering real content, not just a
      green check-run.
- [ ] `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` is cross-referenced as resolved-by-this.

## Related Tickets
- `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` — the temporary disable this reverses

## Related Docs
- None yet.

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.github/workflows/deploy-docs.yml`

## Assumptions / Open Questions
- **Unblock condition is a judgement call, not a measurable one**: "the docs are ready to publish a
  first version" is the user's decision. Do not self-authorise it from CI state or from the docs
  merely building successfully.
- Whether Pages should serve from a branch or from the Actions artifact is undecided; the existing
  workflow assumes the Actions path (`Configure Pages` / `Upload Pages artifact` /
  `Deploy to GitHub Pages`), so that is the default unless someone chooses otherwise.
- The first real run must also confirm actions/upload-pages-artifact@v5 (#588) and setup-node@v7 with Node 24 (TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24); neither has executed. deploy-docs.yml is platform-owned since 2026-10-18.

## Implementation Notes
Blocked. Do not pick this up without the user explicitly saying the docs are ready to publish.

Observed 2026-11-12 (platform-planner; this records progress, the ticket is not closed):
- After the repository moved to rpg-sim-lab (#715 6814855329), the owner re-enabled Pages with source GitHub Actions. `gh api repos/rpg-sim-lab/rpg-based-simulation/pages` gives `build_type: workflow` and html_url https://rpg-sim-lab.github.io/rpg-based-simulation/. AC 1 is met.
- The owner ran the first deploy by hand: Deploy Docs run 43203095497 (workflow_dispatch, at 0539145cb), success. It is the first execution of actions/upload-pages-artifact@v5 and actions/setup-node@v7 with Node 24 here, which answers the open question above.
- The published page was fetched: 200, title "RPG Simulation Wiki", canonical and og:url on the new host. That partly covers AC 3: the front page renders. No inner pages were inspected.
- Still open: AC 2 (restore `push: branches: [main]` and remove the in-file disable comment) and AC 4 (the cross-reference). Restoring the trigger is the owner's call, per Assumptions above.

## Test Summary
_Blocked._

## Files Changed
_Blocked._

## Completion Summary
_Blocked._
