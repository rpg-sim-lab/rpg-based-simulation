---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT
phase: done
date: 2026-11-09
tags: [architecture, engine, determinism]
---

# TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT

## Title
Stage 1: declare each Resolution step's reads and writes, and audit them against observed access with an observe-only hook that is
off by default and hash-neutral.

## Status
DONE

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

- **Ruling (rpg-planner, 2026-11-10; no read-proxy, per Q2):** the audit's READS are **statically derived** from each step's entry function, labelled "statically derived, not observed" in the declarations and the report. Writes and hidden mutations are **observed**. This narrows "actually read" in Scope 2. Runtime read tracing would be a separate proxy ticket (child 4 decides whether one is needed).

## Implementation Notes
Code (WIP, local, not pushed): `src/engine/access_audit/{observe,recorder,hook,declarations,static_reads}.py`; one dispatch call in `pipeline.run_phase` (`dispatch_phase`, imported at module top: a side-effect-free module import); flag `ENABLE_ACCESS_AUDIT` registered in `_DEFERRED_FEATURE_FLAGS` (OFF) with a `docs/guides/feature_flags.md` row. The recorder is passed in through `state.feature_flags["ACCESS_AUDIT_SINK"]`; with the flag off nothing is built. Tests: `tests/unit/engine/access_audit/`. The 6 pinned cells and the merged-tree re-proof are done; the report is `docs/plans/architecture/next_generation_engine_access_audit_report.md`.
Debt: the recorder is a runtime object held on `GameState.feature_flags["ACCESS_AUDIT_SINK"]` (`compare=False`; checkpointing is unsupported while it is on). Acceptable for a flag-off, observe-only audit, not a pattern for child 4 to build on.
Filed by architecture-planner-u24. The filing rides a later implementation PR (#715 6697748243).

Departures from `docs/plans/architecture/next_generation_engine_access_audit_plan.md` (both cleared by rpg-planner and architecture-planner-u24):
- File names, plan section 2 -> as built: `observer.py` -> `observe.py` (pure helpers) + `recorder.py` (the recorder) + `hook.py` (the dispatch call); `report.py` built as planned (`render` turns the cells' `*.audit.json` into the report data tables, replacing an out-of-repo script; test `test_report.py`); tests `test_declarations_cover_every_step.py` -> `test_declarations.py`, `test_observer.py` -> `test_observe.py` + `test_observer_controls.py` (the positive controls), `test_audit_on_off_equivalence.py` -> `test_audit_flag_and_equivalence.py`; added `static_reads.py`.
- Sink: plan section 3 says the records live in an auditor object the kernel owns; as built the recorder is passed in through `state.feature_flags["ACCESS_AUDIT_SINK"]` (not hashed, `compare=False`; checkpointing unsupported while it is on). Stated as a deviation in the PR.
- Timeline elements: mutable pydantic models (`src/observability/events.py:54`) whose only writer appends; the per-step token is the element ids, plus a sampled content check every 100 ticks against the first-seen digest (reported as sampled, not per step). A candidate `frozen=True` hygiene ticket (architecture, child 4 section 5); none filed here.

- In-place INPUT-update table (ruling relayed by rpg-planner, arch and lead accept (A)): tick counts not recorded (the recorder keeps a per-run set); departs from plan section 6 for this table only. The table is a LOWER BOUND: steps seen mutating their input; others may do so undetected (an equal-length in-place edit inside a bucket is not seen). Child 4's copy-on-write rule is enforced by its own Level A proof, not by this list. Carry this line into the PR body.

## Test Summary
- Unit: `tests/unit/engine/access_audit/` 76 passed at `-n 1` (declarations cover every step; observe; flag and on/off equivalence; positive controls incl. the full-deque append, id-reuse control and field-diff row; report).
- Evidence (condition 4a): 6 audit-ON cells (crowded_frontier s42-46, urban_political s46, 5000 ticks, `PYTHONHASHSEED=0`, approved wrapper sha256 39706ba7…) on src head f19379c43: every end hash equals the main 993400a52 base cell; 160k observations each; 35 of 43 steps observed (8 flag-OFF); sampled timeline check 0 edits in 300 samples, 860 replaced (id reuse). Main is now 2ea0e4d8f with an empty `src data config` diff against 993400a52. Timing NOT MEASURED, no perf claim.
- Full test.yml set at `-n 1` on the pinned scratch venv (report head 0837fef5b): all pass except four commands, each with one failure: cmd 17 (wider-scope pin 355 vs 361, fixed by the pin edit af1466e37); cmd 21 (local env: no ruff in the repo `.venv`; CI installs the lint group); cmd 22 (`docs/REGISTRY.yaml` regenerated at close); cmd 23 (`test_http_surface_matches_the_recorded_snapshot`, fails identically on a `git archive` of main 2ea0e4d8f with the same python, so not this branch). `mypy_gate` rc 0 (no new errors); `codebase.health check` rc 0.

## Files Changed
- New: `src/engine/access_audit/{__init__,declarations,hook,observe,recorder,report,static_reads}.py`; `tests/unit/engine/access_audit/` (6 files); `docs/plans/architecture/next_generation_engine_access_audit_report.md`.
- Edited: `src/engine/pipeline.py` (one dispatch call + module-top import), `src/domains/optimization/feature_flags.py` (`ENABLE_ACCESS_AUDIT` OFF), `docs/guides/feature_flags.md` (row), `tests/unit/tools/test_mechanism_registry_completeness_check.py` (pin: scope_files 355 -> 361, unbound_files 249 -> 255, the 6 new access_audit files, measurement infrastructure), `docs/REGISTRY.yaml` (regenerated).

## Completion Summary
Stage 1 observe-only access audit built and run. Reports: declared against observed writes for 35 of 43 steps, in-place input-update mutation (evolution, world_dynamics), hidden mutations on the watch list, sampled timeline check, process globals (none changed), cross-entity proxies. Deviations, all cleared by rpg-planner, architecture-planner and lead: (1) plan section 3: the recorder is passed via `state.feature_flags["ACCESS_AUDIT_SINK"]`, not held by a kernel-owned auditor; checkpointing is unsupported with the audit on; not a pattern for child 4. (2) Plan section 6: the in-place table has no tick counts (the recorder keeps a per-run set) and is a lower bound. (3) File names vs plan section 2: `observer.py` -> `observe.py` + `recorder.py` + `hook.py`. Pin edit to the completeness test (6 files, unbound). The report is evidence for child 4; it files no ticket (frozen=True hygiene for the mutable pydantic timeline events is child 4's to raise). Reads are statically derived, not observed. No staging artifacts existed for this ticket, so none were migrated.
