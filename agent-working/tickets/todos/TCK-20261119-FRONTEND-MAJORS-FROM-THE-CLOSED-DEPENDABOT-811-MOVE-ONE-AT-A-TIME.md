---
status: active
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME
phase: open
date: 2026-11-19
tags: [security]
---

# TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME

## Title
Move the frontend majors from the closed Dependabot #811 one at a time, holding TypeScript at 5.9 until typescript-eslint supports 7

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
The owner closed Dependabot #811 (the npm-major group) unmerged on 2026-11-19 and asked for the finding to become a ticket. The ask came via lead-planner-u24, recorded on #715 as 7002590099.

The finding, checked in #811's package-lock.json by lead-planner-u24 (inspected):
- `npm ci` fails in both the Frontend CI job and the frontend image build.
- #811 bumps typescript ~5.9.3 to 7.0.2. The pinned typescript-eslint 8.72.0 and its @typescript-eslint/* packages declare the peer typescript ">=4.8.4 <6.1.0", so the install refuses.
- Because the install failed, the other moves in the group never ran:
  - jsdom 28.1 to 31.0;
  - @testing-library/jest-dom 6.9 to 7.0;
  - @types/node 24.10 to 26.6;
  - globals 16.5 to 17.14.

## Scope
Follow the shape of TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES. Work on a new branch from origin/main and take one move at a time, in this order: globals, @types/node, @testing-library/jest-dom, jsdom. For each move:
1. Apply the move alone: the version in `package.json`, then `npm install` under Node 24, plus any peer bump it strictly needs.
2. Run `npx vitest run`, `npm run build` and `npm run lint` on rpg-planner's HOST FREE, under `systemd-run --user --scope -p MemoryMax=3G`.
3. Report to rpg-planner: the diff, what passed or failed, and any source or config change the move needs. Change no `frontend/src/**` code or config until rpg-planner answers.
4. If rpg-planner says go, commit the move as its own commit. If not, revert it and record the reason here.

TypeScript stays at ~5.9 until a typescript-eslint release supports TypeScript 7. Check the latest typescript-eslint peer range when this ticket is picked up. If a release supports 7, the TypeScript move comes last, together with that typescript-eslint bump.

## Out of Scope
- Any frontend feature, refactor or behaviour change beyond what a move strictly needs.
- The npm minor/patch group (#881), which goes through its own merge OK.

## Acceptance Criteria
- Each move is landed as its own commit or recorded here with a reason.
- vitest, build and lint pass at the final head, and `npm ci` succeeds.
- TypeScript is unchanged unless typescript-eslint supports the new major.

## Related Tickets
- TCK-20261025-FRONTEND-MAJOR-DEPENDENCY-MOVES (the same shape, done)
- TCK-20261014-DEPENDABOT-GROUPED-MAJORS-MONTHLY (why the majors come grouped)

## Related Docs
- docs/guides/stack2.md §4 (game client versions)

## Related Stored Artifacts
- None.

## Related Code Areas
- frontend/package.json, frontend/package-lock.json

## Assumptions / Open Questions
- Dependabot will open a fresh major PR next month. When it does, close it with a pointer to this ticket, or rebase this ticket's work onto it.
- RPG work comes first on the u24 host.

## Durable state, lifecycle and clocks
None. These are dev and test dependencies only; no simulation state.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
