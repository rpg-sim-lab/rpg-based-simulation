---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261111-DEPENDABOT-WATCHES-WEBSITE
phase: done
date: 2026-11-11
tags: [platform]
---

# TCK-20261111-DEPENDABOT-WATCHES-WEBSITE

## Title
Dependabot watches website/, so a website advisory gets an update PR

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Issue #845 (reopened by lead-planner, 2026-11-11, comment 6791502076): `.github/dependabot.yml` has an npm entry for
`/frontend` only. No entry covers `/website` (the Docusaurus wiki, lead-owned), so website advisories such as #143 (uuid)
and #249 (deepmerge) got no update PR. The wiki rebuild landed in #867 and the uuid alert was cleared by hand in #849.
The remaining scope is the Dependabot entry. This is option 1 in the issue.

## Scope
- `.github/dependabot.yml`: add an `npm` entry for `directory: /website` in the same shape as the `/frontend` entry:
  - `schedule.interval: monthly`, `open-pull-requests-limit: 5`;
  - groups `npm-major` (`[major]`) and `npm-minor-patch` (`[minor, patch]`). Group names are scoped to their update
    entry, and the PR title names the directory ("in /website");
  - `labels: [dependencies, platform]`. No lead label exists, and Dependabot reports an error for a label it can't find.
    Platform triages website PRs and forwards them to lead (see the open question).
- Header comment: add `website/** -> lead (platform triages)` to the review-routing line.
- Close #845 by the PR (`Closes #845` comes from pr_render, through this ticket ID in a commit subject).

## Out of Scope
- Any version bump in `website/package.json` or `website/package-lock.json` (lead's).
- Dismissing the deepmerge alert #249 (lead's scoping already dismisses it with a reason).
- Creating a new GitHub label.
- Merging or closing Dependabot PRs (user).

## Acceptance Criteria
- `dependabot.yml` parses and has 6 entries. The `/website` entry matches the `/frontend` entry's schedule, limit and
  group shape (validated: schema/parse check).
- `website/package.json` and `website/package-lock.json` both exist at the branch head, which is what Dependabot's npm
  ecosystem reads (validated).
- After merge: GitHub's Dependabot config check shows no error, and the next monthly run (2026-12-01) opens at most 2
  grouped PRs "in /website" (observed after merge; record it on this ticket then). Until then the ticket says:
  Known gap: the first /website run is not yet observed.

## Related Tickets
- TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY and TCK-20261015-DEPENDABOT-DOCKER-IGNORE-PYTHON-MINOR-AND-UV: same
  file. Both close in this batch on the 2026-11-01 run evidence (see Implementation Notes).
- TCK-20261108-WEBSITE-DEV-SERVER-PULLS-A-UUID-WITH-AN-OPEN-SECURITY-ALERT and TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA
  (done; lead's website work).

## Related Docs
`docs/architecture/devops_plan_amendment_proposal.md` (step 1)

## Related Stored Artifacts
None.

## Related Code Areas
.github/dependabot.yml
website/package.json

## Assumptions / Open Questions
- Resolved by lead-planner (owner of website/**), 2026-11-11: labels stay `[dependencies, platform]`. Platform triages
  website Dependabot PRs and forwards them to lead. No `lead` label, because the owner would have to create it first.
- Security updates are not governed by the version-update schedule. Once website is a watched directory, GitHub can
  raise a security PR for it at any time.

## Implementation Notes
**Batch close-outs that ride in this PR (the ride-along rule, #715 6793205403).** The 2026-11-01 Dependabot run
satisfies the observed acceptance criteria of both earlier tickets. Record it there and close them:
- GROUPED-MAJORS: the run opened 7 PRs, all grouped (#809 docker-minor-patch, #810 compose-minor-patch, #811 npm-major,
  #812 npm-minor-patch, #813 uv-major, #814 actions-minor-patch, #815 uv-minor-patch). Every ecosystem ran, so the
  config parsed. No ecosystem went over 2 PRs.
- DOCKER-IGNORE: #809 (merged ab8ed9759) moved python 3.13.16 -> 3.13.18 (patch only, no >=3.14) and node 24.21.0 ->
  24.22.2 (no >=25). It left `ghcr.io/astral-sh/uv:0.11.2` untouched. There was no docker-major PR.

## Test Summary
- **validated (parse):** `.github/dependabot.yml` parses as YAML with 6 entries. The `/website` npm entry equals the `/frontend` entry in schedule, `open-pull-requests-limit` and groups (compared programmatically); labels are `[dependencies, platform]`.
- **validated:** `website/package.json` and `website/package-lock.json` both exist at the branch head.
- **not observed:** GitHub's Dependabot config check after merge, and the 2026-12-01 run.

## Files Changed
- `.github/dependabot.yml`: new `npm` `/website` entry; `website/** -> lead (platform triages)` in the routing comment.
- Ride-along closes: `TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY`, `TCK-20261015-DEPENDABOT-DOCKER-IGNORE-PYTHON-MINOR-AND-UV` (evidence re-checked with `gh`, #809-#815).

## Completion Summary
Dependabot now watches `/website` monthly with at most 2 grouped PRs, so a website advisory gets an update PR. Closes #845 through this ticket ID.
Known gap: the first /website run is not yet observed. After merge, check that GitHub's Dependabot config check shows no error and that the 2026-12-01 run opens at most 2 grouped PRs "in /website", and record it here.
