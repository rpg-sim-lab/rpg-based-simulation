---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261109-FRONTEND-LINT-TOOLING-PULLS-A-MINIMATCH-OPEN-TO-GLOB-DOS
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-FRONTEND-LINT-TOOLING-PULLS-A-MINIMATCH-OPEN-TO-GLOB-DOS

## Title
Frontend lint tooling pulls minimatch 10.2.6, which is open to a glob-pattern denial of service (Dependabot alert #250); force 11.0.1 with an npm override if eslint still works

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Dependabot alert #250 (medium, opened 2026-11-08 17:18) flags GHSA-g3hv-75wg-m249: minimatch >=7.0.0 <11.0.1 can be driven into a denial of service through globparts amplification. The first patched version is 11.0.1. lead-planner raised it. Owner decision, logged at #715 6724653808: "A: override now (Recommended)". The same comment is the owner's go to dispatch this ticket.

Checked by rpg-planner-ubuntu on origin/main 8d9f3ebf3 and on the npm registry on 2026-11-09:
- frontend/package-lock.json has one minimatch, 10.2.6, marked dev. Three parents pull it in: eslint 10.13.0 (^10.2.5), @eslint/config-array 0.23.5 (^10.2.4) and @typescript-eslint/typescript-estree 8.72.0 (^10.2.2).
- The latest release of each parent still declares ^10 (eslint 10.14.0 asks ^10.2.6, config-array 0.23.5 asks ^10.2.4, typescript-estree 8.72.1 asks ^10.2.2). No parent bump fixes the alert. The only fix today is an npm `overrides` entry that forces 11.0.1 under parents that declare ^10.
- The lockfile has not changed since #740, so this is a newly published advisory, not a regression.
- Exposure is low. minimatch runs only at lint time, on patterns from our own config. It is not in the shipped bundle.

## Scope
1. In frontend/package.json, add an `overrides` entry that forces minimatch to 11.0.1 (pin `11.0.1` or use `^11.0.1`; say which and why). Regenerate frontend/package-lock.json with npm under Node 24, the version CI uses.
2. Check, under Node 24, the same way #740 (TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES) did:
   - `npm ci`;
   - `npm ls minimatch` shows only 11.0.1, with no invalid or ELSPROBLEMS;
   - `npm audit` shows no minimatch advisory;
   - `npx vitest run` passes (baseline 31 files / 369 tests at #740; report today's count);
   - `npm run build` passes;
   - `npm run lint` gives exactly the problems it gave before the override. Record the baseline count and mix on the unchanged lockfile first; #740 recorded 21.
3. Decide:
   - If every check in step 2 holds, land the override as its own commit.
   - If eslint breaks under minimatch 11 (a crash, a config load failure, or a lint result that differs from the baseline), drop the override. Change nothing in frontend/. Record the failure in Implementation Notes and fall back to option B: wait for eslint or typescript-eslint to move to ^11, then take the normal parent bump. Tell rpg-planner-ubuntu, so the owner can decide whether to mark the alert as tolerable risk. The owner does that, not the implementer.

## Out of Scope
- Any other frontend dependency move.
- Changing eslint.config.js or any frontend/src file to make lint pass under minimatch 11. A lint difference means the override is dropped (step 3); the config is not edited to hide it.
- Dismissing or closing the Dependabot alert. That is the owner's action; a landed override closes it on its own.

## Acceptance Criteria
- AC1: On landing, frontend/package.json has the minimatch override, and the lockfile resolves minimatch only to 11.0.1.
- AC2: On landing, `npm ci`, `npx vitest run`, `npm run build` and `npm audit` pass under Node 24, and `npm run lint` matches the recorded baseline. The close reports each result with counts.
- AC3: If dropped instead, frontend/ is byte-identical to origin/main, and the close records the exact eslint failure and the fallback to option B.
- AC4: CI's frontend job (`.github/workflows/test.yml`: `npm ci`, `npx vitest run`, `npm run build`) is green on the PR.

## Related Tickets
- TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES (done, #740): the verification pattern and the lint baseline.
- TCK-20261014-DEPENDABOT-AND-BASE-IMAGE-PINS (done)

## Related Docs
None. No behaviour change.

## Related Stored Artifacts
None.

## Related Code Areas
- frontend/package.json, frontend/package-lock.json

## Assumptions / Open Questions
- A frontend install/build/test run uses a heavy-run slot from lead-planner, as #740 did. Ask lead for the slot before step 2.
- npm `overrides` lets a child resolve outside its parent's declared range. That is why the eslint check in step 2 is the real test, not `npm ls` alone.

## Implementation Notes
(empty)

## Test Summary
(empty)

## Files Changed
(empty)

## Completion Summary
(empty)
