---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261107-THREE-CROWDED-V3-STARVATIONS-GET-SCOPED-KNOWN-ENTRIES
phase: done
date: 2026-11-07
tags: [testing]
---

# TCK-20261107-THREE-CROWDED-V3-STARVATIONS-GET-SCOPED-KNOWN-ENTRIES

## Title
Five V3 starvations (crowded_frontier s42 e30, s45 e37, s45 e31, s46 e9; frontier_living_world s45 e53) get owner-accepted scoped known entries that expire on 2026-11-30

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Owner acceptances on #715: issuecomment-6692734974 item 2 (crowded_frontier s42 entity 30 and s45 entity 37) and issuecomment-6697054601 item 1 (crowded_frontier s46 entity 9, from #828's arm). Added at the re-sync onto 667199567 (lead-planner-u24, 2026-11-07): issuecomment-6702815851, #828's combined run (crowded_frontier s45 entity 31, frontier_living_world s45 entity 53); #828 needs them on main before it merges. lead-planner-u24 sent the go after #835 put the three owning tickets on main (e9fd48be8). tools/test_architecture/ is testing's; the owning tickets are rpg-planner's.

## Scope
Append five scoped V3 `state: fail` entries to tools/test_architecture/rpg_gate_known.yaml, one case each:
1. crowded_frontier/42 entity 30, ticket TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE.
2. crowded_frontier/45 entity 37, ticket TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX.
3. crowded_frontier/46 entity 9, ticket TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED.
4. crowded_frontier/45 entity 31, ticket TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE (6702815851).
5. frontier_living_world/45 entity 53, ticket TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH (6702815851).
Each: owner rpg-planner, added_on 2026-11-07, expires_on 2026-11-30, and a note saying the owning ticket's fix PR deletes the entry.

## Out of Scope
- Every existing entry (N14, frontier_living_world/43 e38, V1), unchanged.
- The gate baseline (v1 stale since a25619971; re-record is a separate decision).
- Any src change, and the owning tickets' fixes.

## Acceptance Criteria
- [x] AC1: the yaml diff only appends the five entries.
- [x] AC2: tests/unit/tools/test_known_reds.py, tests/unit/tools/test_rpg_gate_baseline.py and tests/static/test_ci_rpg_gate_workflow_shape.py pass.
- [x] AC3: `lint_file(rpg_gate_known.yaml, RPG_GATE_SPEC)` reports no problems.
- [x] AC4: each entry owns its own case and nothing else: a second entity on the same (world, seed), or the same entity id on another seed, stays unowned.

## Related Tickets
- TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE (owner of entry 1, rpg-planner)
- TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX (owner of entry 2, rpg-planner)
- TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED (owner of entry 3, rpg-planner)
- TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH (owner of entry 5, rpg-planner); TCK-20261028-LOW-HP-RETREAT-... also owns entry 4
- TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED (scoped-entry mechanism)
- TCK-20261031-N14-KNOWN-V3-ENTRY-RENEWED-TO-1130 (previous edit of this file)

## Related Docs
- none

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- The file only takes a date expiry. "Expires when its ticket lands, or on 2026-11-30, whichever is first" is expires_on 2026-11-30 plus the note; rpg-planner put the deletion into each owning ticket's acceptance criteria (lead-planner-u24, 2026-11-07).
- Entry 3 (s46 e9) is #828's arm V3, so on main it is a stale mapping until #828 lands. lead-planner-u24 agreed to ship it here so there is one testing PR.
- e30's and e37's ticks (t2211, t2338) come from gate run 42034924002 at 36d4fd78e (#669). e9's tick is not in the owner comment or its ticket, so the note gives none.
- Scoped entries are judged one at a time: a run-level V3 on crowded_frontier/45 whose examples include both e31 and e37 (two owning tickets) is owned by neither entry and shows UNOWNED, as does one with any other entity. That is the mechanism's rule (TCK-20261022), stated here; the owner sees it as a fail if both starve in one run.
- A later baseline candidate records known_file_sha256, so this edit changes that hash. That is expected.

## Implementation Notes
Appended at the end of `known:`. Scoped entries may share `match: "V3"`, and no two entries name the same case, so order among them does not matter.

## Test Summary
`pytest tests/unit/tools/test_known_reds.py tests/unit/tools/test_rpg_gate_baseline.py tests/static/test_ci_rpg_gate_workflow_shape.py`: 137 passed. `lint_file(rpg_gate_known.yaml, RPG_GATE_SPEC)`: []. An ownership check with `owner_of_finding` on synthetic findings found each case owned by its own ticket. crowded s42 [30, 31], crowded s43 [30] and crowded s45 [30] came back UNOWNED; after the two added entries, crowded s45 [31] and frontier s45 [53] are owned, crowded s45 [31, 37] and frontier s45 [53, 54] are UNOWNED.

## Files Changed
- tools/test_architecture/rpg_gate_known.yaml (five entries appended)

## Completion Summary
Five scoped V3 entries added under #715 6692734974 item 2, 6697054601 item 1 and 6702815851, each expiring 2026-11-30, with its fix PR deleting it. Known gap: none beyond e9 being a stale mapping on main until #828 lands.
