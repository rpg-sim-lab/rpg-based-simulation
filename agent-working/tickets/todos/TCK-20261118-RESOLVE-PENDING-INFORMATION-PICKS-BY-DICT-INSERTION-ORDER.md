---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261118-RESOLVE-PENDING-INFORMATION-PICKS-BY-DICT-INSERTION-ORDER
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-RESOLVE-PENDING-INFORMATION-PICKS-BY-DICT-INSERTION-ORDER

## Title
resolve_pending_information picks a population's actor by dict insertion order, not by a declared rule

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
This is backlog, filed per rpg-designer-ubuntu's G1 addendum 2, Q13. It is not part of M1.

`WorldCompiler.resolve_pending_information` (src/worldbuilding/compiler.py:394-397) gives each pending information response and self-model event to the first entity whose `population_id` matches. It finds that entity with `next()` over `entities.items()`, so the order is dict insertion order.

In campaign mode the roster is rebuilt from `persistent_entities` (src/domains/campaigns/orchestrator.py ~261, ~1080-1093). That dict keeps the position of existing keys and appends new ones, so which actor is chosen depends on construction order, not on any stated rule. The result is deterministic, but no rule declares it.

Births (TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND) makes this visible: a surviving newborn can receive its population's information when it is the last member left. That behaviour is disclosed and pinned by tests in that ticket.

## Scope
- Rule work first. rpg-designer decides whether the shared resolver declares an explicit order, such as ascending id or oldest member first. This is pre-bind: the resolver is shared with u24.
- Then implement the declared order and pin it with tests.

## Out of Scope
- Any M1 item.
- Changing the resolver before the ruling.

## Acceptance Criteria
- The resolver's actor choice follows a declared, documented rule, and a test pins it.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH

## Related Docs
None.

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_g1_addendum2_2026-11-18.md (Q13)

## Related Code Areas
src/worldbuilding/compiler.py, src/domains/campaigns/orchestrator.py

## Assumptions / Open Questions
None yet.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
