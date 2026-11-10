---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261109-RESOLVE-ATTACK-IS-CALLED-TWICE-PER-TICK-FOR-ONE-HIT-AND-ONLY-ONE-RESULT-REACHES-HP
phase: open
date: 2026-11-09
tags: [combat, determinism]
---

# TCK-20261109-RESOLVE-ATTACK-IS-CALLED-TWICE-PER-TICK-FOR-ONE-HIT-AND-ONLY-ONE-RESULT-REACHES-HP

## Title
resolve_attack is called twice per tick for one hit and only one result reaches hp

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Lane C trace (urban s46, W id 4 at t216, hit-wake DEFEAT trace) shows `resolve_attack` called twice in one tick for one hit while only one result reaches hp. Name the second caller; check whether side effects are applied twice (durability, XP, events, emotions, learning).

## Scope
Investigation first: find both call sites, which result is committed, and which side effects the discarded call (or the doubled call) applies.

## Out of Scope
Changing the free swing, combat damage or its legality; the flight guard (TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE).

## Acceptance Criteria
- Both callers named with file:line; a test pinning the count of resolve_attack calls per hit.
- Each side effect listed as applied once or twice, with evidence.

## Related Tickets
TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE

## Related Docs
docs/engine/contracts/combat_contract.md

## Related Stored Artifacts
/mnt/data2/scratch-c3/ (defeat_{B,W}_5000.json)

## Related Code Areas
src/engine/combat.py; src/engine/movement.py

## Assumptions / Open Questions
Which of the two calls is the opportunity-attack path versus the queued ATTACK is not yet known.

## Implementation Notes
Filed from the flight ticket; not started.

## Test Summary
None.

## Files Changed
None.

## Completion Summary
Open.
