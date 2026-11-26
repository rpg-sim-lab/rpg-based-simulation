---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261124-BUILDINGS-AND-FACTIONS-START-WITH-GOLD
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-BUILDINGS-AND-FACTIONS-START-WITH-GOLD

## Title
Wage-paying buildings and factions start with declared gold, so the money loop does not run dry at the start

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner direction #715 7130838054 item 3: starting gold for buildings and factions is fine (for example 1000 or 10000), and the economy gets balanced later. Under the owner's scope freeze (#715 7132422805) this is a follow-up outside #995. The owner's focus direction (#715 7131896269) applies: the economy only has to work well enough. If #995's W run shows broke bodies collapsing, this comes to the owner first.

## Scope
1. Starting gold for wage-paying buildings and faction treasuries is declared world content (the EXCH-02 pattern, divergence 2.97), not code.
2. The designer proposes the values to the owner before any data change.
3. Bible ch03 §4.1 and parity are updated in the same change.

## Out of Scope
- Economy balance beyond "the loop does not run dry".

## Acceptance Criteria
1. The owner's values are recorded on #715, and the data matches them exactly.
2. Purses over time in a W cell show wages paid through the run (report).
3. Atomic conservation holds (the existing conservation tests).

## Related Tickets
- TCK-20261009-FIRST-COIN-IS-DECLARED-WORLD-CONTENT-EXCH-02
- TCK-20261009-THE-FACTION-TREASURY-PAYS-WAGES-FOR-TOWN-WORK-DECISION-37
- #995 (rpg-free-meal-atomic)

## Related Docs
- docs/mechanics/03_economic_laws.md §4.1
- docs/guidelines/intentional_divergences.md 2.97, 2.109

## Related Stored Artifacts
- none yet

## Related Code Areas
- building and faction content data (tills and treasuries)

## Assumptions / Open Questions
- Which buildings count as wage-paying is the designer's call.

## Durable state, lifecycle and clocks
No new durable state: content values only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
