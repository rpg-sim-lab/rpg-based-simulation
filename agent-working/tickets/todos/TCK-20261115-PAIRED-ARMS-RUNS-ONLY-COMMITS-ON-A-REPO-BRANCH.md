---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261115-PAIRED-ARMS-RUNS-ONLY-COMMITS-ON-A-REPO-BRANCH
phase: open
date: 2026-11-15
tags: [platform, security]
---

# TCK-20261115-PAIRED-ARMS-RUNS-ONLY-COMMITS-ON-A-REPO-BRANCH

## Title
The paired-arms workflow keeps no token on disk and refuses a base or new commit that is not on a repo branch, before any arm runs.

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
- **Where it came from.** The owner asked for a proposal to run paired measurements on GitHub Actions (#715 6891576449, item 3).
  platform-planner found the workflow already built: `.github/workflows/paired-arms.yml`, from #775, with zero runs. Its first
  dispatch is AC1 of testing's `TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST`. The review found two gaps.
- **What testing-planner asked for** (owner of the workflow, per `docs/plans/test_architecture/reference/paired_arms_off_host.md`;
  relayed by lead-planner from lead-planner-u24 on 2026-11-15):
  - the hardening goes first;
  - platform drafts it as a hotfix, and testing-planner reviews it;
  - it lands before any dispatch.
- Claimed on #634 (6891636364).

**The gaps:**
1. Every `actions/checkout` in the workflow persists `GITHUB_TOKEN` in `.git/config` (the default). The arms jobs then run code from
   the dispatched shas, so that code can read the token. The token is `contents: read` on a public repo, so the impact is small,
   but there is no reason to leave it there.
2. The arms job fetches `base_sha` and `new_sha` by sha ("any commit reachable on GitHub"). That includes a fork pull request's
   commit under `refs/pull/*`, so a dispatch could run code that was never pushed to a repo branch. Only users with write access can
   dispatch, but a mistyped or pasted sha is enough.

## Scope
1. `persist-credentials: false` on every `actions/checkout` step in `.github/workflows/paired-arms.yml` (the plan, arms and
   aggregate jobs).
   - The arms job's own `git fetch` of the two shas must still work without the persisted token. The repo is public, so an
     anonymous fetch over https works.
2. In the plan job, before the matrix is emitted, refuse a `base_sha` or `new_sha` that no repo branch contains:
   - fetch every branch without blobs: `git fetch --no-tags --filter=blob:none origin '+refs/heads/*:refs/remotes/origin/*'`. The
     checkout's default depth-1 history cannot prove containment, so this fetch is not shallow;
   - for each sha, fail the step with `::error::` naming the input when `git cat-file -e <sha>^{commit}` fails, or when
     `git branch -r --contains <sha>` prints nothing;
   - the shas come in through `env:`, never by `${{ }}` inside `run:` (the existing context guard);
   - the `arms` job already `needs: plan`, so a refusal stops every arm.
3. Static tests in `tests/static/test_ci_paired_arms_workflow_shape.py`:
   - every checkout step in the file has `with: persist-credentials: false`;
   - the plan job has a step that runs the branch-containment check before the step that writes the matrix, and it reads
     `BASE_SHA`/`NEW_SHA` from `env`.

## Out of Scope
- Dispatching the workflow (AC1 of `TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST`, testing's, after this lands, on the owner's
  go).
- Any change to `tools/test_architecture/paired_arms.py` or `tools/rpg_measure/paired.py`.
- The DET-PORT question (Ubuntu 25.10 host vs the 24.04 runner), which is testing's, before AC1's result is read.
- Other workflows' checkouts. If the same gap matters elsewhere, it gets its own ticket.

## Acceptance Criteria
1. Every `actions/checkout` in `paired-arms.yml` sets `persist-credentials: false`, and a static test fails if one doesn't.
2. The plan job refuses a sha that no repo branch contains, before the matrix output, and a static test pins that order and the
   `env:` input.
3. The existing guards still pass: `tests/static/test_ci_paired_arms_workflow_shape.py`, `test_workflow_actions_pinned_by_sha.py`
   and `test_workflow_run_blocks_take_github_context_via_env.py`.
4. testing-planner reviews and OKs the diff before the push ask.
5. `actionlint` (if available locally) or a YAML parse of the file passes.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (testing; in progress; its AC1 dispatch waits on this)
- TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS (done; paired.py --collected)

## Related Docs
- docs/plans/test_architecture/reference/paired_arms_off_host.md

## Related Stored Artifacts
- none

## Related Code Areas
- .github/workflows/paired-arms.yml
- tests/static/test_ci_paired_arms_workflow_shape.py

## Assumptions / Open Questions
- `.github/workflows/paired-arms.yml` is unowned in the route registry. Testing owns it by its design doc and asked for this change.
- `tests/static/test_ci_paired_arms_workflow_shape.py` routes to rpg (`tests/**`), but it is testing's own AC4 guard. testing-planner
  reviews it, and rpg-planner-ubuntu is told.
- A blob-less fetch of every branch is assumed to take seconds on this repo. The implementer checks this locally with the same
  command.

## Implementation Notes
- Hotfix tier, so no staging artifacts.
- Dispatch is under S4 (#715 6473439661): testing-planner, the workflow's domain owner, OK'd the shape.
- It is built after the world farm's review fixes, on the same branch and PR (same platform track).

## Test Summary
Not started.

## Files Changed
- none yet

## Completion Summary
Open.
