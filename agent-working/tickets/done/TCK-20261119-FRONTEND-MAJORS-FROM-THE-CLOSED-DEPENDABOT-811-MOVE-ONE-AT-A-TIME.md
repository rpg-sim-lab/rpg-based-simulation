---
status: historical
layer: frontend
authority: P1
audience: agent
ticket_id: TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME
phase: done
date: 2026-11-19
tags: [security]
---

# TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME

## Title
Move the frontend majors from the closed Dependabot #811 one at a time, holding TypeScript at 5.9 until typescript-eslint supports 7

## Status
DONE

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

- 2026-11-24, rpg-planner-ubuntu: Dependabot #1004 (npm-major group without TypeScript) was closed by owner decision #715 7122284965; this ticket runs on ubuntu. Targets: globals 17.14.x, @types/node 26.x, @testing-library/jest-dom 8.0.0 (not 7.0), jsdom 31.0.1. jsdom 31's engines field is node ^22.22.2 || ^24.15.0 || >=26.0.0; CI's setup-node 24 and docker/frontend.Dockerfile's node:24.22.3 meet it. jsdom 31 serializes CSS numbers at 6 significant digits (jsdom/lib/jsdom/living/css/serialize.js:1040), so frontend/src/test/GameCanvas.zoom.test.tsx's style.transform read-back loses precision (#1004's Frontend job failed at lines 92 and 121); the component is correct and unchanged.

## Test Summary
- Node 24.22.1 (/data/vboxuser/node24), each check under `systemd-run --user --scope -p MemoryMax=3G`. After each move: `npx tsc -b`, `npx vitest run`, `npm run build`, `npm run lint`, `npm ci` from clean, `npm audit --omit=dev`.
- Move 1, globals ^17.14.0: vitest 369/369, build ok, `npm ci` ok, audit 0. Lock: globals only.
- Move 2, @types/node ^26.6.6: `tsc -b` 0 errors before and after (no type error changed), vitest 369/369, build ok, `npm ci` ok, audit 0. Lock: @types/node and its dependency undici-types 7.16.0 to 8.9.0.
- Move 3, @testing-library/jest-dom ^8.0.0: vitest 369/369, build ok, `npm ci` ok, audit 0. 8.0.0's only breaking change is dropping vitest below 5; peers @testing-library/dom >=10 <11 (10.4.1) and vitest >=5 <6 (5.1.1) are met; matchers used (toBeInTheDocument, toHaveStyle, toHaveAttribute) are unchanged; `src/test/setup.ts` still imports `@testing-library/jest-dom/vitest`.
- Move 4, jsdom ^31.0.1: the bump alone failed 4 tests, all in GameCanvas.zoom.test.tsx (lines 52, 79, 92, 121; jsdom 31 serializes CSS numbers at 6 significant digits). Test-only fix (helpers `serialized`, `onLevel`, `onWholePixel`, `levelOf`, no epsilon) then vitest 369/369, build ok, `tsc -b` 0, `npm ci` ok, audit 0. Transitive major jumps from jsdom 31: data-urls 7 to 8, entities 6 to 9, html-encoding-sniffer 6 to 7, tr46 6 to 7, undici 7 to 8, w3c-xmlserializer 5 to 6, whatwg-url 16 to 17.
- Mutation proofs (each reverted): (a) raw pan in the translate (no `snapToDevicePixel`) fails 4 tests (pan at DPR 1.25 and 1.5, overview pan at DPR 1.25 and 1.5); rpg-planner-ubuntu's own mutation `pan.x + 0.1` failed 8. (b) a x1.01 zoom step alone is absorbed by the component's `snapZoom` (21/21 pass); with `snapZoom` also removed, 17 of 21 fail.
- Lint: `npm run lint` reports 21 problems (17 errors, 4 warnings) on origin/main 494098c9d and the sorted error/warning lines are identical after every move.
- Other style read-backs in src: PixelIcon.test.tsx:68 (38.4px, short decimal, passes) and string compares only; none changed.

## Files Changed
- frontend/package.json, frontend/package-lock.json
- frontend/src/test/GameCanvas.zoom.test.tsx (test-only read-back helpers)
- agent-working/tickets/done/ (this ticket), agent-working/tickets/todos/TCK-20261124-FRONTEND-LINT-IS-RED-ON-MAIN-AND-CI-DOES-NOT-RUN-IT.md (filed)

## Completion Summary
All four majors landed as one commit each, in the ticket's order, each on rpg-planner-ubuntu's go (owner GO #715 7122284965): globals 0943654f9, @types/node 4ed998cab, @testing-library/jest-dom a9dc4972d, jsdom b533c6445 (with the test-only zoom fix). No component, config or Node change; CI's setup-node 24 and docker/frontend.Dockerfile's node:24.22.3 already meet jsdom 31's floor. TypeScript stays at ~5.9 (not in scope this time).

GAP, stated plainly: acceptance criterion 2 ("vitest, build and lint pass at the final head") is NOT met for lint. Lint was already red on origin/main (21 problems: 17 errors, 4 warnings), identical before and after every move, and CI's Frontend job runs only `npm ci`, `npx vitest run` and `npm run build`, so it does not run lint. vitest, build and `npm ci` pass at the head. Followed up by TCK-20261124-FRONTEND-LINT-IS-RED-ON-MAIN-AND-CI-DOES-NOT-RUN-IT.
