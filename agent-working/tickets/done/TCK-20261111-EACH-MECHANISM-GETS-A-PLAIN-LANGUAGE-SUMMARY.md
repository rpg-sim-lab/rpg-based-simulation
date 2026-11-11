---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY
phase: done
date: 2026-11-11
tags: []
---

# TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY

## Title
Each mechanism in the registry gets a plain-language summary

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
The website wiki (#845) renders "How the world runs" straight from registries/mechanisms.yaml and falls back to a humanized id where no summary exists. Add a one-or-two-sentence `summary` to each of the 110 mechanisms. Owner-approved: #715 6789779149, refining 6789714730. Dispatched by rpg-planner.

## Scope
- One `summary` line per mechanism, inserted after its `layer` line. No other field, line or order changes.
- Plain language for a reader: what the mechanism does in the world. No code names, paths, function names, ticket or divergence ids.
- True to the entry's current state: every gap, partial, orphan or gated mechanism says what exists now and what does not.

## Out of Scope
- Any validator or reader change (agent-working-planner adds the optional field).
- Changing a mechanism's state, notes, bindings or verification.

## Acceptance Criteria
- 110 of 110 entries carry a `summary`; the diff is summary lines only.
- Registry validate, the mechanism_* tool tests and the generated-view checks pass with the new key.
- No summary reads as if an unfinished mechanism fully works.

## Related Tickets
- TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE (unrelated; the previous batch on this seat).

## Related Docs
- registries/mechanisms.yaml (its own state and verified blocks were the source).
- docs/mechanics/ (Bible chapters); no disagreement with the registry found that changes a summary.

## Related Stored Artifacts
None (hotfix tier).

## Related Code Areas
- registries/mechanisms.yaml

## Assumptions / Open Questions
- Summaries were written from each entry's state, notes and verified block. A few entries have a thin note (declared_cognition_schema, committed_intentions, strategic_redirection, group_coordination, settlement_capacity_axis, fidelity_drift, team_up, crafting); their summaries are deliberately generic and are listed for rpg-planner's check.

## Implementation Notes
Inserted by script (id to summary map), one line per entry, then diffed: 110 insertions, 0 deletions, 0 other changes.

## Test Summary
- make mechanism-registry-validate: ok. mechanism-registry-html-check, mechanism-wiring-map-classdef-check, mechanism-status-language-check: ok.
- tests/unit/tools/test_mechanism_*.py and test_terr_mapping_mechanism_state_stability.py: 277 passed. Architecture/docs/integrity/static/refactor registry-keyed tests: 11 passed.
- Timing NOT MEASURED. No simulation cells run.

## Files Changed
- registries/mechanisms.yaml (+110 summary lines)
- agent-working/tickets/done/TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY.md
- agent-working/tickets/working_log.csv, agent-working/agent-monitoring/ shards, docs/REGISTRY.yaml (close bookkeeping)

## Completion Summary
All 110 mechanisms now carry a plain-language summary; no other registry field changed, and every check that reads the file accepts the new key.
