---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
phase: open
date: 2026-11-09
tags: [testing, architecture]
---

# TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE

## Title
Milestone 1's name-check probe: no role, kind or faction name switch left in a decision path, as a green-from-day-one ratchet whose allowlist empties as the retirements land (the content-alone probe is split to TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.5 done item 1: "no decision reads a role, kind or faction name, a new kind works from content alone, and the 'no name checks in decision code' probe finds no name switch left in a decision path. 'Works from content alone' is proven by a named probe: a test kind declared only in content, with no code change, perceives, eats and fights by its declarations." §12.3 lists the name-check probe as a standing check.

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. The name-check probe: a mechanical scan of the decision paths for role, kind and faction name comparisons, with an explicit, reasoned allowlist. Run it early, because its output is the inventory for the retire-name-branches item.
2. The content-alone probe: a test kind declared only in test content, with no code change, perceives, eats and fights by its declarations through the real kernel.
- Whether these live under tests/architecture is testing-planner's call (route: tests/architecture/** belongs to testing-planner).

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- The name-check probe runs in CI and reports every name switch it finds. It goes green only when milestone 1's retirements are done.
- (moved to the split ticket) The content-alone probe passes on the milestone 1 record commit.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
tests/, decision code (read only)

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
Split (testing-planner, 2026-11-15, on rpg-planner's sequencing ruling): this ticket is now scope item 1 only, the name-check probe. Scope item 2, the content-alone probe, moved to TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS and is HELD. Its AC ("passes on the milestone 1 record commit") would only fail today, and #781 is still open. The second AC below belongs to that ticket.

Planner rulings (testing-planner + rpg-planner, 2026-11-15; owner dispatch #715 6883358041):
- **Home:** tests/architecture/. An AST scan; the tool may sit in tools/test_architecture/ with the test calling it.
- **Green from day one, as a ratchet** (the spawn-site guard pattern, tests/architecture/test_spawn_sites_declare_source.py):
  - Every current switch is an allowlist row: file, symbol, the compared name, a one-line reason, and the citation TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES.
  - A new switch fails. A stale row (its switch is gone) fails.
  - "Done" means the allowlist is empty; the epic's done check reads that.
  - This replaces the AC wording "goes green only when retirements are done" (rpg-planner: not red until then).
- **Decision path** (rpg-planner): code run during the tick that chooses or resolves what an entity does.
  - SCAN (gating): src/ai, src/cognition, src/strategy, src/actions, src/engine (all of it, incl. combat_rewards.py HERO_KILL), src/systems, src/domains/*, src/economy, src/town, src/quests, src/progression, src/entities.
  - REPORT-ONLY on the first run, not gating: src/world, src/core, src/content_semantics. rpg-planner rules each hit from the inventory. After that, each row moves into gating or into a reasoned exclusion.
  - EXCLUDE: src/api, views, rendering, observability, logging, replay, cli, lab, perf, certification, simulation_quality, testing, scenarios, platform, config, worldassembly, worldbuilding, worldgeneration, worldmodules, content (kinds are declared there by name, legitimately).
- **A switch is:**
  - a role, kind or faction compared to a name literal;
  - `EntityRole.X` or a kind or faction enum used in a branch, a match, membership or a dict key;
  - a lookup table written in code and keyed on names;
  - allegiance or hostility tables keyed on faction names.
  Reading a content-declared relation keyed by id is data, not a switch.
- **Output:** rows of file:line, symbol, and compared name, as text plus `--json`. The retire ticket's step-1 inventory uses it directly, adding its own 3-category column for hero rows. Attach the first full inventory to the PR, counted, with a hand-checked sample of 10 rows marked true or false positive.
- **Tests:** a synthetic package (each switch shape found; data-by-id not found; excluded package not scanned; report-only package reported, not gating; a new switch fails; a stale row fails), plus the real tree green with the committed allowlist.
- Cheap: no host slot needed. Single process; no pytest -n>1 while rpg cells run.

## Test Summary

## Files Changed

## Completion Summary
