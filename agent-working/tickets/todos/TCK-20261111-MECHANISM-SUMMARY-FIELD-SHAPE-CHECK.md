---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK
phase: open
date: 2026-11-11
tags: [documentation, reference]
---

# TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK

## Title
The mechanism registry validator checks the shape of the optional per-mechanism `summary`

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P3

## Request Summary
rpg-planner (u24) is adding an optional plain-language `summary` string per mechanism in
`registries/mechanisms.yaml` (TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY) for the
generated website wiki (#845; owner decision #715 6789779149). Checked on main:
`tools/mechanism_registry/registry.py::validate()` has no key allowlist, so `summary` already
passes, and so do `summary: 42` and `summary: ""`. The wiki would render those as-is.

## Scope
- In `validate()`: when a mechanism has `summary`, it must be a non-empty, single-line string.
  Absent stays valid.
- Tests for absent, valid, non-string, empty and multi-line values.

## Out of Scope
- Any mechanisms.yaml content (rpg's).
- Making `summary` required, or adding a key allowlist.

## Acceptance Criteria
1. A mechanism without `summary` validates exactly as before.
2. A non-string, empty or multi-line `summary` yields one validate() error naming the mechanism.
3. The committed mechanisms.yaml on main at implementation time validates with no new errors.

## Related Tickets
- TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY (rpg, content)
- TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY

## Related Docs
- docs/plans/mechanism_registry_initiative.md (check whether it lists entry fields; update alongside if so)

## Related Stored Artifacts

## Related Code Areas
- tools/mechanism_registry/registry.py, tests/tools/test_mechanism_registry*.py

## Assumptions / Open Questions
- Lands after or independently of the rpg content ticket; neither blocks the other.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
