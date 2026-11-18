---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE: plan

## Approach
An AST scan, `tools/test_architecture/name_switch_scan.py`, and a ratchet test, `tests/architecture/test_no_name_switches_in_decision_paths.py`, with the committed allowlist `tests/architecture/name_switch_allowlist.yaml`. Rulings are the ticket's Implementation Notes (testing-planner + rpg-planner, owner #715 6883358041).

1. Scanner: package lists SCAN (gating), REPORT_ONLY, EXCLUDE exactly as ruled; every `src/` directory must be in one list. Four switch shapes: compare, match, lookup, table. Output rows file:line, symbol, name (text and `--json`).
2. Ratchet: allowlist row = (file, symbol, name) + count + reason + the retire ticket. New switch, over-count, under-count and stale row all fail.
3. Inventory: the first full scan, counted, in investigation.md with a 10-row hand-checked sample.

## Decisions
- Rulings of 2026-11-15 (testing-planner relaying rpg-planner): `runtime` EXCLUDE; `content_semantics` SCAN; `core/builder.py` birth record promoted to gating (`PROMOTED_GATING`); the identity compat maps are reasoned exclusions (`REASONED_EXCLUSIONS`); `species`/`archetype` words added; `getattr(x, "kind", ...)` and one-step local bindings read.
- `kind` counts only on an entity-like receiver or as `entity_kind`/`monster_kind`/`creature_kind`; `role` and `faction` count on any receiver. First attempt (any `*_kind`) gave 342 gating rows, most for other records' kinds (work_kind, event_kind, lead.kind); the tightened rule gives 78; after the review fixes and rulings the inventory is 139 switches (114 gating, 15 report-only, 10 excluded), see investigation.md.
- Name sets bound to a name (`_CANDIDATE_ROLES = (EntityRole.A, ...)`) count as table rows: found by comparing a grep of every `EntityRole.`/`Faction.` use in SCAN with the scan output.
- Out of scope: the content-alone probe (TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS, held).
