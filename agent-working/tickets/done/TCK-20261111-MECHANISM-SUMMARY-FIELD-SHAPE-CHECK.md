---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK
phase: done
date: 2026-11-11
tags: [documentation, reference]
---

# TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK

## Title
The mechanism registry validator checks the shape of the optional per-mechanism `summary`

## Status
DONE

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
`validate()` in `tools/mechanism_registry/registry.py` gains one block before the `implemented_by` check: when a mechanism has the key `summary`, it must be a string, not blank, and a single line (no `
` or `` inside the stripped text). Each failure is one error naming the mechanism id. Absent stays valid and no key allowlist was added. `docs/plans/mechanism_registry_initiative.md` lists no entry fields, so it needed no change.
AC3 checked on main df3527c69 (after #866): all 110 mechanisms carry a `summary` and none produces a new error.

## Test Summary
`tests/tools/test_mechanism_summary_shape.py`: 14 passed (absent; valid; non-string x5; empty x3; multi-line x3; the committed `mechanisms.yaml` has no summary error). The fixture is a bare one-mechanism file, so the tests compare against the baseline errors it already trips (orphan systems) instead of asserting an empty list.

## Files Changed
tools/mechanism_registry/registry.py, tests/tools/test_mechanism_summary_shape.py

## Completion Summary
An optional `summary` is now shape-checked: non-empty, single-line string, one error per bad mechanism. The 110 committed summaries validate.
