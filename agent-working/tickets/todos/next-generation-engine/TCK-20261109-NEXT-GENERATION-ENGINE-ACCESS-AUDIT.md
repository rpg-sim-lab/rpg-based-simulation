---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism]
---

# TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT

## Title
Stage 1: declare each Resolution step's reads and writes, and audit them against observed access with an observe-only hook that is
off by default and hash-neutral.

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 2 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE` (stage 1).

It runs alongside M1. Rpg-planner agreed to that, on the conditions below, relayed by lead-planner-u24 on 2026-11-09. Those
conditions bind the ticket. Owner decisions: #715 6735575831 (Q4 (a): the observe-only audit may run alongside M1).

The work runs on **architecture's implementer, not an RPG lane**, and rpg-planner reviews it.

It is blocked on child 0 (`TCK-20261109-NEXT-GENERATION-ENGINE-ADR`) for the code. Filing and design can start now.

## Scope
1. **Declarations.** For every `refine` step (`src/engine/pipeline.py:136-444`), declare:
   - its reads: tick-start state, and which earlier deltas;
   - its writes;
   - whether it needs sliding state.
   The feasibility review §2 table is the starting point.
2. **Shadow access audit.** A hook at the step-dispatch layer records, per step, the state fields and update entries actually read
   and written on the gate worlds. It compares them with the declarations. It also lists hidden mutations: writes to tick-start state
   outside the apply path (for example cooperation's `timeline.append`, movement claims, the strategic cache flag), and reads of
   process globals.
3. **A report**, under `docs/plans/architecture/`: declared vs observed per step, every mismatch, and every hidden mutation. This is
   the input to child 4.

### Conditions from rpg-planner (binding)

1. **Files.**
   - New modules, plus **one hook at the step-dispatch layer** (the kernel/pipeline phase runner). **No edits inside step logic.**
   - **Hands off:**
     - `tactical.py`, `pipeline_phases/hardening.py`, `scheduler.py` and `military_conflict.py` (open RPG branches);
     - `movement.py` and `intelligence.py` (the COMBAT-RETREAT P2).
   - **Before any code**, send rpg-planner the exact file list, through lead-planner-u24. Rpg-planner re-diffs it against the open
     RPG branches and the M1 tickets, and answers with a slot.
   - Any `docs/engine` touch is named to lead-planner-u24 first.
2. **When.**
   - Filings and design can start now.
   - **The code PR waits until the three RPG heads (LOW-HP, hardening, hit-wake) are pushed.**
   - Each audit PR lands **between M1 behaviour PRs, never during a measurement**, in a gap rpg-planner names.
3. **Heavy slot.**
   - Taken from rpg-planner's queue, one heavy process per host.
   - It comes after the DEFEAT trace and the hardening runs.
   - Unit and scoped tests are not heavy.
4. **Hash-neutral proof.**
   - (a) A pinned `arm_child` run (`PYTHONHASHSEED=0`, 5000 ticks) with the **audit ON**, on the stage tree. Its **end hash equals
     main's** on crowded s42 to s46 and urban s46. Existing base cells are reused where main's tree is unchanged.
   - (b) An **equivalence test in the PR**: audit on and audit off give the same hash and the same event count.
   - (c) **Off by default behind a flag.** It never reads cache-writing lazy properties, and stores nothing in hashed state.
   - (d) The PR states that the audit writes **none of the fields** listed in
     `TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ`.
   - (e) Timing is **NOT MEASURED**, and the PR makes no perf claim.
5. **Review.** Rpg-planner reviews, by comment, every stage PR that touches `src/engine`.

**Cost:**
- design and declarations: one doc session;
- code: new modules plus one hook, with unit tests and the on/off equivalence test;
- runs: 6 pinned 5000-tick cells with the audit on, in rpg-planner's heavy slot. Base cells are reused.

**Leaves out:** any change to step logic, any contract change (child 4), any timing.

## Out of Scope
- Edits inside step logic, and the hands-off files above.
- Merge rules and the contract itself (child 4).
- Any perf measurement or claim.

## Acceptance Criteria
1. Every `refine` step has a declaration.
2. The audit, with the flag on, reports declared vs observed access per step and every hidden mutation, on the gate worlds.
3. Conditions 1 to 5 above are met and stated in the PR: the file list was cleared by rpg-planner, the slot was named, the proofs
   (a) to (e) hold, and rpg-planner reviewed.
4. With the flag off (the default), behaviour is unchanged: gate and paired hashes are as on main.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent)
- TCK-20261109-NEXT-GENERATION-ENGINE-ADR (blocks the code)
- TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC (consumes the report)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ (condition 4d)

## Related Docs
- docs/plans/architecture/next_generation_engine_feasibility_review.md (§2, §2a)
- docs/plans/design_enhancement/subphase_domain_contracts_epic.md (Section F, never started; this revives its declaration step)
- docs/performance/phase_inventory.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/pipeline.py (step dispatch: the hook only)
- src/engine/phase_graph.py (read-only reference)

## Assumptions / Open Questions
- **Who writes the code.** The architecture implementer's write scope is `docs/plans/architecture/**` only, per its role card
  ("until owns grow"). Rpg-planner routes the code to architecture's implementer. That scope has to grow first, by a registry change
  (agent-working-designer) on the owner's say. Until then, the declarations and the report can be written; the hook cannot.
- Python attribute-level read tracing on frozen dataclasses may need a proxy view at the dispatch layer. Its design must satisfy
  condition 4c.

## Implementation Notes
Filed by architecture-planner-u24. The filing rides a later implementation PR (#715 6697748243).

## Test Summary
Planned: unit tests for the hook and the declaration checker; an audit on/off equivalence test (hash and event count); pinned
5000-tick cells with the audit on (condition 4a).

## Files Changed
None yet.

## Completion Summary
Open.
