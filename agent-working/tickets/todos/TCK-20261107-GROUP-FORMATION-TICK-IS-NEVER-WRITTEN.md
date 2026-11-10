---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261107-GROUP-FORMATION-TICK-IS-NEVER-WRITTEN
phase: open
date: 2026-11-07
tags: []
---

# TCK-20261107-GROUP-FORMATION-TICK-IS-NEVER-WRITTEN

## Title
GroupRecord.formation_tick is never written: every group carries 0 in the digest, while the docs say it holds the formation tick

## Status
BLOCKED

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by lane C (rpg-implementer-3) during #828's residual-churn check. Read on arm 7384a28c9f3d, crowded_frontier s45, 5000t, with final_hash 2209d09642c0d93d15ee376238f96cd1d14395d1f4cc6b234e67994053b34e76 matching. The read was read_groups2.py (sha256 cc90bd96626446fe8f4eb6fc0f8a1d6c6ed9a28f6f362a37b906e1a84dd89d57), output /mnt/data2/scratch-c3/cf45/groups2_arm_cf45.json (sha256 1940f906b37e0ff90da7d32345ab952d7bbed3231debaf93e75ed8ad8ea2f108).

Five recruit-contract groups (10049, 10053, 10054, 10088, 10089) formed between t1436 and t2501. Each has formation_tick 0 at first sight, at dissolution and at the end of the run. On the same groups, last_leadership_check_tick is stamped with the formation tick, so #828's AC 4 holds. rpg-designer ruled that this is a separate defect outside #828.

On main (531010a9a) the only src hits are the default `formation_tick: int = 0` (src/core/state.py:735) and `to_canonical_dict` (state.py:764). No formation path writes the field and no decision reads it. Other places that use it:
- tests/unit/social/test_group_lifecycle_fields.py: construction and round-trip only.
- docs/simulation/domains/party_contract.md:29 says it is the "Tick at which the group was formed", which is not true at runtime.
- The parity ledger, social_narrative.yaml:2443, claims the field exists (from TCK-20260619-E41A-GROUP-LIFECYCLE, SOC-227).

## Scope
Counts first:
1. Writers. None found in src on main; confirm, including any construction through checkpoint restore.
2. Readers. Search tests, tools, the API presenters and schemas, frontend and the replay and inspection tools. Each reader is named with file:line.
3. Choose one of two options, and state the choice and its cost at scoping, per #715 6697776913 and 6698958617:
   - (a) Remove the field. This is the smaller change if no reader turns up. It updates the docs (party_contract.md), the parity ledger entry and the unit test.
   - (b) Fill it at the one place a group is created. Older checkpoints hold 0, so the derive-or-refuse rule (src/engine/checkpoint_fields.py FIELD_RULES) needs an entry. That entry either derives the value at load from last_leadership_check_tick, which is the formation stamp, or refuses the checkpoint. The ticket says which.
   - rpg-designer's lean (2026-11-07), given the readers found so far: **(b), fill it.** The contract doc (party_contract.md:29) and the ledger entry (social_narrative.yaml:2443) both say the field holds the formation tick, so the intended behaviour is "filled" and the code is what's wrong. Removing it would mean rewriting a contract doc and a ledger entry to match a defect. (a) stays open only if the counts turn up a reason against filling.
   - Until the fix lands, the ledger entry claims behaviour the code doesn't have. Set that entry's `status` to `divergent`, with a `divergence_note` naming this ticket. This is a docs-only change in the same hit-wake PR, and the fix sets the entry back to verified.
4. Either option moves the canonical hash, removal because the key leaves the digest and filling because the value changes. Simpler option and its cost (rpg-designer): it rides with the next change that moves hashes anyway, the hit-wake fix, and shares that fix's measurement. It does not get a measurement run of its own.

## Out of Scope
- #828's AC 4 (last_leadership_check_tick), which holds.
- Other GroupRecord lifecycle fields, unless the reader count shows the same never-written pattern. If it does, report that pattern and do not fix it here.
- Widening the state digest (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ).

## Acceptance Criteria
- The writer and reader counts are reported with file:line.
- The option is chosen and stated with its cost before implementation. For (b), the FIELD_RULES entry and its derive-or-refuse choice are named.
- After the change, the docs (party_contract.md), the parity ledger entry and the unit tests agree with the code. A test covers a live formation path: for (b) it shows a formed group carrying its formation tick, and for (a) it shows the field is absent.
- The hash move is disclosed in the PR that carries the hit-wake fix and is measured once with it. No baseline is edited to make a check pass.
- Hot-loop: no. The change happens once, at group creation or as a removed key.

## Related Tickets
- TCK-20260619-E41A-GROUP-LIFECYCLE (added the field)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (#828, where this was found)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
- The hit-wake fix, which this rides with

## Related Docs
- docs/simulation/domains/party_contract.md
- docs/parity_ledger/social_narrative.yaml (GroupRecord lifecycle fields entry)
- docs/engine/deterministic_execution.md (canonical hash)

## Related Stored Artifacts
- None yet. The evidence is lane C's scratch output, cited by sha256 above.

## Related Code Areas
- src/core/state.py GroupRecord (src/core/group_record.py on the #828 branch)
- src/systems/world_systems/groups.py, src/systems/social_systems/party_lifecycle.py (group creation)
- src/engine/checkpoint_fields.py FIELD_RULES

## Assumptions / Open Questions
- Is 0 ever an intended value, for example for a group formed at t0? The counts settle it.
- Filed by rpg-planner on rpg-designer's ruling of 2026-11-07. Dispatch is in rpg-planner's order, with the hit-wake fix.

## Implementation Notes
2026-11-07 (rpg-implementer) Counts, main 667199567. Readers: none (state.py:735 default, :764 canonical emit; tests/unit/social/test_group_lifecycle_fields.py construction and round-trip only; tools, API, presenters, frontend 0 hits). Writers before the fix: none. Group-creation sites: src/systems/world_systems/groups.py:326 (recruit-contract party) and src/engine/military_conflict.py:341 (faction squad); the ticket said one, there are two.
Chosen: (b), fill both with state.tick. Cost: the canonical dict changes by construction (hash differs), measured once with the hit wake (arm F, 1 seed, equal counters, death list and per-entity end state).
No FIELD_RULES row, and no derive or refuse: FIELD_RULES fires only on an UNSET slot (checkpoint_fields.py, _UNSET), and formation_tick exists in every checkpoint since TCK-20260619-E41A-GROUP-LIFECYCLE, so a row never fires. last_leadership_check_tick cannot derive it: party_lifecycle.py:90, :108 and :126 re-stamp it at every check. A restored group formed before this ticket keeps formation_tick 0, so 0 on a restored group is ambiguous (real tick-0 formation or pre-fix); nothing reads the field. Groups are retained in state.groups after dissolution (groups.py:78-83), so a stale 0 is not aged out; the planner's reference to 2.156 as a retention rule is not correct (2.156 is the retreat clear window). Accepted by rpg-designer and rpg-planner, 2026-11-07. party_contract.md section 1 names the ambiguity.
Tests: tests/unit/social/test_group_formation_tick.py, one case per writer; both fail with the two src lines reverted.

## Test Summary
tests/unit/social/test_group_formation_tick.py (2 passed; both fail with the two src lines reverted). Scoped: tactical, engine, kernel, social, faction, core, integrity, architecture not-slow: 2098 passed, 4 skipped, 1 xfailed. code-health OK, typecheck-py clean.

## Files Changed
src/systems/world_systems/groups.py, src/engine/military_conflict.py (one stamp each), tests/unit/social/test_group_formation_tick.py, docs/simulation/domains/party_contract.md, docs/parity_ledger/social_narrative.yaml (SOC-227 evidence).

## Completion Summary
NOT LANDED. Parked with the hit-wake fix by the owner (#715 6776436829), so the closure below is the parked branch's text, not main's.
- The build exists only on lane C's local rpg-hit-wake (b46c429e7, 2162e1f19): two formation_tick stamps plus tests/unit/social/test_group_formation_tick.py. On main the field is still never written.
- It rode hit-wake by the designer's ruling (shared hash move, one measurement), so it parks with it.
- Un-park options (rpg-designer to rule; rpg-planner dispatches):
  - land it alone, with its own hash-move measurement;
  - or keep it with hit-wake's revisit.
- Note: SOC-227 on main still claims the field holds the formation tick. The ledger's `divergent` marking rode the parked branch, so main's ledger stays wrong until this lands.

Parked branch's own summary: Option (b): formation_tick is stamped with state.tick at both group-creation writers; no FIELD_RULES row (it cannot fire; old checkpoints keep 0, which is ambiguous on a restored group and said so in party_contract.md). The hash moves by construction and is measured once with the hit wake (arm F, 1 seed). Counts and reasoning in Implementation Notes.
