---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261124-FRONTEND-LINT-IS-RED-ON-MAIN-AND-CI-DOES-NOT-RUN-IT
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-FRONTEND-LINT-IS-RED-ON-MAIN-AND-CI-DOES-NOT-RUN-IT

## Title
Frontend lint is red on main (17 errors, 4 warnings), and CI's Frontend job does not run it

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Found during TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME (rpg-implementer-ubuntu, verified by rpg-planner-ubuntu on 2026-11-24). `npm run lint` in frontend/ reports 21 problems (17 errors, 4 warnings) on origin/main 494098c9d, after a clean `npm ci`, under Node 24.22.1. The same 21 problems remain after the four major moves; none of the moves added one. CI's Frontend job (.github/workflows/test.yml, around lines 756-762) runs `npm ci`, `npx vitest run` and `npm run build` only, so lint regressions reach main unseen.

The problems by rule (rpg-planner-ubuntu's count at b533c6445):
- react-hooks "Cannot access refs during render" and related render/ref errors: 12 (GameCanvas.tsx:147-149, :439; InspectPanel.tsx:1012-1013; and others);
- react-hooks/exhaustive-deps: 3 (warnings);
- react-hooks/set-state-in-effect: 1;
- @typescript-eslint/no-explicit-any: 3;
- @typescript-eslint/no-unused-vars: 1;
- react-refresh/only-export-components: 1.
Files: src/App.tsx, src/components/{GameCanvas,InspectPanel,Sidebar}.tsx, src/contexts/MetadataContext.tsx, src/hooks/{useCanvas,useSimulation}.ts, src/test/useSimulation.test.tsx, src/visualAssets/MapHarness.tsx.

## Scope
- Fix each lint problem in the code it names, without changing behaviour; the existing vitest suite must stay green.
- A rule may be disabled or downgraded only on rpg-planner-ubuntu's written yes, with the reason recorded here.
- Then add a `npm run lint` step to CI's Frontend job, so a lint error fails CI.

## Out of Scope
- Any frontend feature or refactor beyond what a lint fix strictly needs.
- Dependency moves (TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME).

## Acceptance Criteria
1. `npm run lint` in frontend/ exits 0 at the final head.
2. vitest and build pass, and no component behaviour changes.
3. CI's Frontend job runs lint and fails on a planted lint error (shown once, then reverted).

## Related Tickets
- TCK-20261119-FRONTEND-MAJORS-FROM-THE-CLOSED-DEPENDABOT-811-MOVE-ONE-AT-A-TIME

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts

## Related Code Areas
- frontend/src/components/GameCanvas.tsx, InspectPanel.tsx, Sidebar.tsx
- frontend/src/hooks/useCanvas.ts, useSimulation.ts
- .github/workflows/test.yml (Frontend job)

## Assumptions / Open Questions
- The react-hooks ref-during-render errors come from eslint-plugin-react-hooks 7's React Compiler rules. Some may need a real restructure of how refs are read; if a fix would change rendering, ask rpg-planner-ubuntu first.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
