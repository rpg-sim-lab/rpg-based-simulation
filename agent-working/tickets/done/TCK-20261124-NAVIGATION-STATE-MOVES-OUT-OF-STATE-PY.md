---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY
phase: done
date: 2026-11-24
tags: []
---

# TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY

## Title
NavigationComponent moves out of src/core/state.py into its own core module, retiring the one-line size raise

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Retiring ticket for the proposed +1 line raise of src/core/state.py (1672 to 1673) caused by #996's arrived_this_attempt field (owner answer: #715, after 7135893456). Precedent: #715 6785100551 and TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS.

## Scope
1. Move NavigationComponent (state.py:496, about 83 lines) and its canonical helpers into a new core module, re-exported from src/core/state.py so every importer keeps working.
2. A pure move: an AST check shows 0 differing definitions (the updates.py precedent).
3. Old checkpoints still load (a test with a pickle that names src.core.state.NavigationComponent).
4. Lower the state.py module-length ceiling to the new size in the same change.

## Out of Scope
- Any behaviour change.

## Acceptance Criteria
1. 0 differing definitions by AST.
2. An old-checkpoint load test passes.
3. The state.py ceiling is lowered and the raise is retired; the code health check is clean.

## Related Tickets
- TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON (#996)
- TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS

## Related Docs
- docs/plans/systemic_world/experience_memory_design.md
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none (a pure move; no staging artifacts)

## Related Code Areas
- src/core/state.py, codebase/baselines/code_health_exceptions.jsonl

## Assumptions / Open Questions
- Filed under the owner's scope freeze (#715 7132422805); the owner then chose to split now (#715 after 7135893456), so it is closed inside #996.

## Durable state, lifecycle and clocks
None added or changed. NavigationComponent is the same record with the same fields in the same order; only its module changed (src/core/navigation_component.py). The checkpoint fingerprint of a NEW checkpoint now keys it `src.core.navigation_component.NavigationComponent`; a checkpoint written before names `src.core.state.NavigationComponent`, which still resolves through the explicit re-export in src/core/state.py.

## Implementation Notes
Owner answer: #715, after 7135893456 (split now, retiring the +1 raise taken at 0d0141804 after #715 7132516556). Done in #996 on rpg-stalemate-nav after the S7 merge of origin/main 2adee5a6c (lead record: #715 after 7135904136).
- NavigationComponent (decorator included, 82 lines) moved byte-identical to src/core/navigation_component.py (new, with a module docstring and the imports it needs: GiveUpRecord, giveup_canonical, MovementMode, TargetPurpose, purpose_canonical). The four names and MovementMode were used only by that class in state.py, so their imports left state.py with it (nobody imports them through state, checked by grep).
- src/core/state.py re-exports it with `from src.core.navigation_component import NavigationComponent as NavigationComponent` (no noqa).
- state.py line count after the S7 merge: 1687 (the merge brought main's own changes); after the move: 1601. The module-length row (codebase/baselines/code_health_exceptions.jsonl l.581) is value = ceiling = 1601, retiring_ticket null: the raise taken for 1673 is gone.
- New test tests/unit/engine/test_checkpoint_old_navigation_path.py: a checkpoint whose header fingerprint and pickle name `src.core.state.NavigationComponent` passes the schema check and unpickles.

## Test Summary
Run at HEAD 4445e0532d788177c4671d850c3a18a464e8b344 (planner slot GO, busy_gate rc 0 before each step; venv-sync2 python; the lock env ci_env_c4cd853 for mypy and code health):
- AST class-identity check (0d0141804:src/core/state.py against src/core/navigation_component.py, decorator included): True.
- tests/unit/engine/test_checkpoint_old_navigation_path.py: 3 passed.
- tests/unit/engine/test_canonical_digest_equals_reference.py: 31 passed.
- Engine checkpoint tests (test_checkpoint_fields, test_checkpoint_group_fields, test_checkpoint_schema, test_scenario_checkpointer, test_beds_survive_a_checkpoint_restore): 76 passed.
- tests/unit/movement: 146 passed. tests/unit/strategic: 697 passed.
- mypy_gate: rc 0.
- Code health: rc 0, no blocking row; "OK: 3 new, 2 worse, 110 improved, 29 gone, 3402 unchanged (5 report-only)" (the new and worse rows are all jscpd, report-only). The src/core/state.py module-length row (1601/1601) is neither worse nor improved, so the tool measures 1601, as the row says; src/core/state.py ruff D102 is 34 against a ceiling of 36 (improved, not tightened here).
No failure and no existing test expectation changed.

## Files Changed
- src/core/navigation_component.py (new)
- src/core/state.py
- codebase/baselines/code_health_exceptions.jsonl (l.581)
- tests/unit/engine/test_checkpoint_old_navigation_path.py (new)
- agent-working/tickets/done/TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY.md

## Completion Summary
NavigationComponent now lives in src/core/navigation_component.py and is re-exported by src/core/state.py; state.py is 1601 lines (was 1673 at 0d0141804) and its module-length ceiling is lowered to 1601, which retires the raise. Behaviour is unchanged. Verification results: see Test Summary.
