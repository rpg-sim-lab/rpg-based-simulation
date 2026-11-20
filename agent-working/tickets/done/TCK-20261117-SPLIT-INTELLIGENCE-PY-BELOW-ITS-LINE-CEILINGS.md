---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS

## Title
Split src/systems/strategic_systems/intelligence.py so its module and StrategicIntelligenceSystem class fall back below their line ceilings

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The paydown ticket that retires the intelligence.py line-ceiling raises of M1 Phase 1.
- N10 (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK) adds the suspension-expiry helper and wrapper: module length 1833 → 1880 and class length 1671 → 1717.
- The blocker-churn fix (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION) adds the quiet-spell and merge passes to the same file.
- PERC-02b moves about 13 perception sites, some of them in this file.
The split is a mechanical move (no behaviour change), proven by an AST name + body comparison and a hash-equal run.

## Scope
1. Move cohesive groups (project lifecycle, blocker lifecycle, routing helpers) into sibling modules. StrategicIntelligenceSystem keeps thin delegates where callers need them.
2. Bring the module and class below their ORIGINAL ceilings (1833 / 1671), and lower the ceilings.
3. Re-key any path-keyed baselines (mypy, import layers) with a ruling, and check the mechanism-registry implemented_by entries.

## Out of Scope
- Any behaviour change.

## Acceptance Criteria
- intelligence.py module and class are at or below 1833 / 1671 lines, and the ceilings are lowered to the new values.
- Hash-equal on the 3 gate worlds at s42; the AST comparison shows only moves.

## Related Tickets
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
- TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS (the same pattern)

## Related Docs
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Schedule: after N10 and the churn fix land, before run-2 items that touch the file (PERC-02b). The owner decides.

## Implementation Notes
- Filed by rpg-planner.
- Group 1 only (the blocker lifecycle), dispatched by rpg-planner 2026-11-20. The ticket's acceptance is "module and class below their original ceilings"; Group 1 alone meets it (module 1619 ≤ 1833, class 1455 ≤ 1671), so the ticket CLOSES with this change. Later groups (project lifecycle, routing helpers, the PERC-02b sites) are K-package work, not this ticket.
- The moved functions went into the existing `blocker_lifecycle.py` (divergence 2.214's module), not a new one.

## Test Summary
Evidence labels: executed unless marked.
- Move proof (inspected, host-free): `astproof.py` (sha efe7a623 earlier, current copy in /mnt/data2/rpg-measure/intsplit/): the three moved functions are AST body-equal and signature-equal to origin/main's, ignoring docstrings and four hoisted imports; every other class method, the module-level nodes and the class's non-method members are AST-identical.
- ONE deviation from a pure move: `resolve_blockers` did `cadence = cadence or SystemCadence()`, a dead-end assignment. systems may not import engine (import contract), so that single line now runs in the class delegate (intelligence.py is a pinned exception) and the moved function takes `cadence: Any = None` and does not use it. The same expression still runs before the same call. The proof script asserts exactly this.
- Statics at the final src (70dbcc5d3, and the amended baseline head 637307d82 has the same src): lint-imports 17 kept / 0 broken; mypy filter 0 rows; code-health rc 0 (only the 4 known report-only jscpd rows in src/observability); pyrefly report: the 10 moved rows re-keyed, 20 other errors are main drift outside this diff.
- tests/unit/** by directory at 1b6f1b852 (same src): 42 directories rc=0, `motivation` rc=5 (no tests), `worldassembly` 5 failed / 211 passed: the 5 pre-existing grade-stability rows, byte-identical to the main control log.
- Hash-equal S9 (executed): STRICT comparison, 0 differing fields, start and final hash equal in all 3 gate worlds (s42, 5000 ticks): BASE 0c18f6151 vs NEW 637307d82; finals 45063d92 / 03020cc2 / 8c7158d1, equal to the #965 and worker-fix strict finals. strict.txt sha e2a3490b; runner 15236340, comparator 8eb8d171.
- Re-key proof (executed, host-free): `rekey_multiset_proof.py 0c18f6151 HEAD` (stored artifacts, output beside it): with path, line and column stripped the before/after multisets are EQUAL for mypy (1332 = 1332) and pyrefly (699 = 699). The one-off `rekey.py`, `astproof.py` and `baseline_row_diff.txt` sit beside it and are NOT committed under codebase/ or tools/. The pyrefly intelligence.py:390 col 59 row is main drift and was not folded in.
- Mechanism advisory (changed-code check): reviewed, no change (rpg-planner).
- Baselines: the moved rows were re-keyed through the code-health registry's own load_rows/write_rows (the `codebase.health move` command refuses renamed-symbol and partial-count rows); rekey.py sha 84f0e125. Ceilings lowered by the moved amounts only; pre-existing slack (F401, I001) left alone.

## Files Changed
- src/systems/strategic_systems/blocker_lifecycle.py (infer_blockers, generate_crafting_blockers, resolve_blockers moved in)
- src/systems/strategic_systems/intelligence.py (three delegates; two now-unused imports removed)
- codebase/baselines/code_health_exceptions.jsonl, mypy_baseline.txt, pyrefly_baseline.json (re-keyed rows and lowered ceilings)
- docs/parity_ledger/strategic_cognition.yaml (v2_evidence of STRAT-005: the new location; no status change)
- agent-working: this ticket, stored artifacts, monitoring shards; docs/REGISTRY.yaml

## Completion Summary
The blocker lifecycle left StrategicIntelligenceSystem: `infer_blockers`, `generate_crafting_blockers` and `resolve_blockers` now live in `blocker_lifecycle.py` as module functions; the class keeps the same three static entry points as one-line delegates, so callers (blacksmith.py, fused_strategic_pass, eight test files) are untouched. intelligence.py went from 1879 to 1618 lines and the class from 1717 to 1454 (the ratchet tool measures 1619 and 1455); both ceilings were lowered to those values. No behaviour change: the hash-equal run is the result (strict, 0 differing fields, 3 worlds). The moved code reads no perception fields (it reads navigation.wait_count/oscillation_count/position, identity.latest_intent_results, inventory and strategic state). The one deviation from a pure move and the registry-API baseline re-key are named above. No new numeric tuning values; nothing under data/.
