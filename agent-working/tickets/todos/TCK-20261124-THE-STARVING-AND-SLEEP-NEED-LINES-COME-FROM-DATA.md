---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261124-THE-STARVING-AND-SLEEP-NEED-LINES-COME-FROM-DATA
phase: open
date: 2026-11-24
tags: []
---

# TCK-20261124-THE-STARVING-AND-SLEEP-NEED-LINES-COME-FROM-DATA

## Title
The starving line and the sleep line come from a data file, not from code constants

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Filed with the lead's yes (#715, lead-planner-u24 record of 2026-11-24, item 4). #996's import fix (architecture review APPROVE WITH CONDITIONS, condition 1) moves STARVING_LINE (95.0) and SLEEP_LINE (98.0) into one core source, src/core/need_lines.py. StarvationTable's defaults read it, and the strategy HUNGER_LINE equals STARVING_LINE instead of keeping a second copy. That gives one source, but the values are still tuning constants in code. The standing rule is that simulation settings belong in data files.

## Scope
1. The starving line and the sleep line are read from a data file under data/ (the designer names the file; a need-profile or survival settings file is the likely home). They load through the existing content/registry path, once, at world assembly.
2. src/core/need_lines.py becomes the typed holder of the loaded values, or it is removed. Every reader (StarvationTable defaults, strategy HUNGER_LINE, need_services_at and any other caller found by search) reads the one loaded value.
3. Values are unchanged (95.0, 98.0). The test is byte-identical behaviour, with the kernel pins unchanged.
4. Bible ch01 (Passive Decay Rates, Penalty Threshold) cites the data file. Parity entry updated.

## Out of Scope
- Changing either value (that is an owner ask).
- Per-kind lines (a later need-profile question for the designer).

## Acceptance Criteria
1. No numeric 95.0 / 98.0 need-line literal remains in src/ (static check).
2. A test that changes the data value changes the reader's line (with a failing control).
3. Kernel pinned fixtures and the state digest are unchanged.
4. Import contracts are unchanged, with no new exception.

## Related Tickets
- TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON (#996; introduces src/core/need_lines.py)
- TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS (sleep line semantics)

## Related Docs
- docs/mechanics/01_entity_anatomy.md (Passive Decay Rates)
- docs/world_rules/life-body/survival-needs.md (SURV-07)

## Related Stored Artifacts
- none yet

## Related Code Areas
- src/core/need_lines.py (after #996), the StarvationTable defaults, src/strategy/experience_due.py HUNGER_LINE, need_services_at

## Assumptions / Open Questions
- This lands after #996 merges.
- The data file's home is the designer's call.

## Durable state, lifecycle and clocks
No new durable state. These are content settings loaded once.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
