---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS
phase: done
date: 2026-11-11
tags: []
---

# TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS

## Title
Move the per-domain update models out of src/core/updates.py into src/core/update_models/, so the module comes back under its length ceiling

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
This is the paydown ticket for the owner's ceiling raise (#715 6785100551, "Raise + file split ticket (Recommended)"). TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME raised the `src/core/updates.py` module-length ceiling from 1315 to 1316, for one import line. The owner's standing rule since then: a ceiling raise is accepted only with a named paydown ticket. This ticket is that row's `retiring_ticket`.

At main 5c6990e51, `updates.py` is 1315 lines, with 27 classes: the entity-level updates (Equipment, Interaction, Combat, Navigation, Task, Identity, Social, Biological, Attribute, Lifecycle, Reward, Strategic, Stamina, Wound, StatusEffect), EntityUpdate, the world and state updates (ResourceNode, World, Chest, Camp, Faction, Clan), and StateUpdate. The repo already has the pattern: `src/core/update_models/` holds buildings, inventory, quests and resources, and `updates.py` re-exports them (docs/engine/architecture.md §7, "Decoupled Core Models"; docs/core/update_intents.md, "Extension rules").

## Scope
1. Move whole classes, unchanged, into `src/core/update_models/<domain>.py`, following the existing package. A candidate grouping: combat (CombatIntent, CombatUpdate, WoundUpdate, StaminaUpdate, StatusEffectUpdate, EquipmentUpdate), social (RejectionEvent, SocialBondUpdate, SocialUpdate), body (BiologicalUpdate, AttributeUpdate, LifecycleUpdate, RewardUpdate), and world (ResourceNodeUpdate, WorldUpdate, ChestUpdate, CampUpdate, FactionUpdate, ClanUpdate, QuestOpportunityRewardIntent). The implementer settles the grouping by import cycles. EntityUpdate and StateUpdate stay in `updates.py`.
2. `updates.py` re-exports every moved name, so no caller changes. Nothing is renamed, and no field, default, merge rule or `is_noop` changes.
3. Pay the ratchet down honestly: the module-length row for `updates.py` falls to its new value, with ceiling = value. Each new module gets its own baseline rows only if a gate measures it. Remove `retiring_ticket` from the row once it is under its original ceiling.
4. Proof that nothing changed: the repo's unit suites for core, engine, social and combat; mypy_gate; `codebase.health check`; and one pinned crowded_frontier s42 5000-tick cell whose final hash equals main's. The serialised forms (`to_canonical_dict`, the checkpoint pickle) are unchanged, because the class module path is part of a pickle. Check the checkpoint round-trip test explicitly.

## Out of Scope
- Any change to merge semantics (F2, F5 and F7 of the next-generation contract spec §9 stay with that contract).
- The typed-delta work of the next-generation engine contract (child 4/5). Coordinate with architecture-planner-u24 first: if a stage there is about to reshape these classes, this ticket waits for it or folds into it.

## Acceptance Criteria
- `updates.py` is under 1315 lines, and its baseline row has ceiling = value and no `retiring_ticket`.
- Every import of a moved name still resolves; no caller is edited.
- The crowded s42 hash equals main's, and the checkpoint round-trip passes.

## Related Tickets
- TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME (the raise)
- TCK-20260326-BIGMOD (the earlier overgrown-module refactor)
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (contract spec §3 field merge rules)

## Related Docs
- docs/engine/architecture.md §7
- docs/core/update_intents.md
- src/core/update_models/README.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- src/core/updates.py
- src/core/update_models/
- codebase/baselines/code_health_exceptions.jsonl (the updates.py module-length row)

## Assumptions / Open Questions
- Pickle paths: a moved class pickles under its new module. If any stored checkpoint must still load, keep a module alias or a `checkpoint_fields` step. Check this before moving anything.
- Filed by rpg-planner on 2026-11-11, from the owner ruling (#715 6785100551). Slot: after the current RPG heads; light, no paired measurement.

## Implementation Notes
Mechanical, text-preserving move by AST line spans (script in scratch, not committed). Moved whole classes unchanged to `src/core/update_models/{social,strategic,combat,body,world}.py`; `updates.py` re-exports every moved name. EntityUpdate, StateUpdate, NavigationUpdate and IdentityUpdate stay: two architecture guards read `src/core/updates.py` by path (`faction_set=` in IdentityUpdate; `lodged_in_set/_clear=` in NavigationUpdate), and their allowlists were not touched. The executor and kernel were not touched.

Disclosure: the first mechanical pass left `NO_OWNER_SENTINEL` (an annotated assignment the script did not match) in `updates.py` while `decode_owner_faction_id_set` moved to `world.py`, a NameError at runtime in the new module. Ruff F821 found it before the first commit; the constant now moves with its comment block and `updates.py` re-exports it.

## Test Summary
- AST check against main 5e58ae857: every moved definition equals main's, ignoring docstrings (0 missing, 0 extra, 0 differing).
- Docstrings added to the moved methods and modules (substance fix for the new-file lint rows); moved complexity untouched.
- Unit suites at -n 1: tests/unit/core + social + kernel/test_executor_context_parity + the faction-write-path, lodged_in and cognition-bundle guards: 741 passed; tests/unit/engine + combat: 1196 passed, 3 skipped; 4 checkpoint tests: 27 passed.
- `make typecheck-py` (mypy | mypy_baseline filter): rc 0. `codebase.health check`: OK, 0 worse (2 report-only jscpd rows, not ours). `generate_registry.py --check`: in sync.
- Plain 5000-tick cells on a git archive of 16bf7a874 (pinned runner, PYTHONHASHSEED=0, MemoryMax 2.5G): crowded_frontier s42 e0e20c2044d7ca86... and frontier_marches s42 908eb3bb14416087..., both identical to cd83111c5's cells (src/data/config byte-identical to main). Peaks 180 and 260 MB.

## Files Changed
src/core/updates.py (1316 -> 600 lines); src/core/update_models/{social,strategic,combat,body,world}.py (new); src/core/update_models/README.md; docs/engine/architecture.md; docs/core/update_intents.md; codebase/baselines/code_health_exceptions.jsonl; codebase/baselines/mypy_baseline.txt; agent-working/tickets/todos/TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES.md (P3 follow-on, filed by rpg-planner); ticket and staging artifacts.

## Completion Summary
Done. `updates.py` is 600 lines, under its 1315 ceiling; the module-length row is deleted (it named this ticket as its retiring ticket).

Approvals: dispatch #715 6813227854; paydown of the ceiling raise #715 6793483728 / 6785100551. Baseline rulings: code-health #715 6813365478 (history line: 4 rows re-keyed to update_models/body.py and combat.py at unchanged values: ruff C901 1, ruff C901 1, ruff PLR0912 1, complexipy CombatUpdate.merge 30; 5 gone updates.py rows deleted via `codebase.health delete`: module-length 1316, D101, F401, I001, CombatUpdate.merge; 3 updates.py ceilings lowered to the values `tighten` computes: C901 6->4, PLR0912 5->4, D102 33->6; no value rises); mypy #715 6813426261 (6 mypy_baseline lines re-keyed from src/core/updates.py:0 to src/core/update_models/social.py:0, messages and count unchanged).

Known gaps: the 6 re-keyed mypy errors in SocialUpdate.merge are not fixed here; they are the P3 follow-on TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES. The moved complexity (body.py C901, combat.py C901 and PLR0912, CombatUpdate.merge 30) is unchanged by design. Hash cells cover crowded_frontier s42 and frontier_marches s42 only. `make knowledge-index-update` not run: worktrees use main's index; lead-planner-u24, 2026-11-12.
