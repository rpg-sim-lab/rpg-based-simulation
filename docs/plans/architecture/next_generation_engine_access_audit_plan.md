---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, planning]
---

# Stage 1 plan: the observe-only access audit

The plan for `TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT`, child 2 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`. Written by
architecture-planner-u24, 2026-11-09.

- The ADR it serves: `docs/architecture/next_generation_engine_adr.md` (accepted, #715 6742854335).
- Dispatch: plan and file list only (#715 6743047506). **No code until the flight, hardening and hit-wake RPG heads have pushed.**
- Routing: rpg-implementer-2 (lane B) writes the code, sequenced by rpg-planner (owner, #715 6743082252). Architecture writes the
  declarations data and the report. Rpg-planner reviews every PR that touches `src/engine`.
- Rpg-planner's conditions in the ticket bind this plan. The answers here come from rpg-planner's 2026-11-09 re-diff, relayed by
  lead-planner-u24.

## 1. What it does

For every Resolution step that `refine` dispatches through `run_phase` (`src/engine/pipeline.py:103-135`), the audit does three
things:
1. **Declares** reads (tick-start state, and which earlier deltas), writes, and whether the step needs sliding state, as data. The
   feasibility review §2 table is the starting point.
2. **Observes**, with the flag on:
   - **writes**: the diff between the update passed into `phase_fn` and the update it returns, per field of `EntityUpdate` and
     `StateUpdate`;
   - **hidden mutations**: a fingerprint of tick-start state taken before and after `phase_fn`, which catches writes that bypass the
     update (cooperation's `timeline.append`, movement claims, `route_plans`, spatial and movement caches, the strategic
     `_has_hostiles_or_dead_cache` flag);
   - **process globals**: a fixed watch list (registries, the content catalog, the terrain cache, the observability config), checked
     the same way.
3. **Reports** declared against observed, per step: every mismatch and every hidden mutation. The report is
   `docs/plans/architecture/next_generation_engine_access_audit_report.md`, and it is the input to child 4, the contract spec.

**Reads are not traced in v1.** The step lambdas capture `state` from the refine scope, so the dispatch layer cannot see per-step
reads without replacing the object the steps see. v1 takes reads from the declarations plus static inspection: evidence class S, not
T. See §5.

## 2. Files (cleared by rpg-planner against `main` `1fb40ac76`)

Re-diff result: none of the three RPG heads touches `pipeline.py`, `feature_flags.py` or the new paths, and no M1 ticket names
`pipeline.py`.

**Edited:**
1. `src/engine/pipeline.py`, at the dispatch layer only:
   - inside `run_phase` (`:103-135`): when the audit is on, record the update diff and the state fingerprint around `phase_fn`;
   - one line that builds the auditor, placed **after** the refine prologue's feature-flag block (`:66-91`), never inside it.
   - No edit inside any step lambda or step module.
2. `src/domains/optimization/feature_flags.py`: register `ENABLE_ACCESS_AUDIT` = OFF.

**New:**
3. `src/engine/access_audit/__init__.py`
4. `src/engine/access_audit/declarations.py`: the per-step declarations, as data
5. `src/engine/access_audit/observer.py`: the update diff, the fingerprint diff and the process-global watch list
6. `src/engine/access_audit/report.py`: declared against observed, as JSON plus markdown
7. `tests/unit/engine/access_audit/test_declarations_cover_every_step.py`
8. `tests/unit/engine/access_audit/test_observer.py`
9. `tests/unit/engine/access_audit/test_audit_on_off_equivalence.py`: condition 4b
10. `docs/plans/architecture/next_generation_engine_access_audit_report.md`, written after the runs

**Not touched**, which covers everything in flight:
- `tactical.py`, `pipeline_phases/hardening.py`, `scheduler.py` and `military_conflict.py`;
- `movement.py` and `intelligence.py`;
- `src/core/updates.py`, `src/engine/checkpoint.py`, `combat.py`, `patches.py`, `tactical_flight_guard.py` and
  `src/systems/world_systems/groups.py`;
- `src/core/state.py`, `tools/rpg_measure/**`, and any `docs/engine` file.

**Overlap to sequence:** `TCK-20261023-PRESSURE-SIGNALS-SWITCH-FEATURE-FLAGS-OUTSIDE-THE-HASH` (not dispatched) deletes
`pipeline.py:86-91`, the `ENABLE_` mapping from `pressure_signals` in the same prologue. The audit goes first, and rpg-planner holds
that ticket until the audit PR merges. That is why the auditor line goes after the flag block.

## 3. The switch, and what "hash-neutral" means here

- **How it is switched on:** `state.feature_flags["ENABLE_ACCESS_AUDIT"] = ON`. `feature_flags` is `compare=False`
  (`src/core/state.py:1365`), and `CanonicalStateHasher` never reads it.
- **What that proves:** only that the **flag** sits outside the digest. It does **not** prove that the **observer** changes nothing.
  Conditions 4a and 4b prove that.
- **The flag stays observe-only for good.** No behaviour may ever be hung on it, the same class as the pressure-signals finding.
- The observer never reads cache-writing lazy properties (condition 4c). It stores nothing on state; its records live in the auditor
  object, which the kernel owns for the run.

### 3a. What the hidden-mutation detector can see (ubuntu review R-B1)

An identity-plus-length fingerprint misses in-place changes that keep both, for example a dict value changed in place or two list
elements swapped. So the fingerprint has two tiers:
- **Watch list, content-hashed.** These are the known mutation sites and everything carried across ticks by reference:
  - every entity's `timeline`;
  - `route_plans`, `movement_cache`, `occupancy_snapshot`, `_occupancy_map_cache`, `transient_claims` and
    `_has_hostiles_or_dead_cache`;
  - `world_indexes` and the spatial-query and semantic-index memo attributes.
  Each is hashed by its canonical contents (keys, values and order), reading plain attributes only, never lazy properties.
- **Everything else on `AuthoritativeState` and each `EntityState`:** attribute identity, plus container identity and length.

**What it cannot see, stated in the report:**
- an in-place change that keeps identity and length in a field **outside** the watch list;
- a write to an attribute that did not exist before the step and is removed again before the step returns;
- mutation of an object reached only through a process global outside the §1 watch list.
A hit in the second tier promotes that field to the watch list for the next run.

**Positive controls** (`test_observer.py`). Each known mutation kind is injected into a fake step, and the test asserts the detector
reports it, with the step and the field:
1. a timeline `append`;
2. a `route_plans` `object.__setattr__`;
3. an in-place dict value change;
4. an equal-length list element swap;
5. a cache flag flip.
One more control proves the second-tier blind spot is real: an in-place change outside the watch list, asserted **not** detected.
That keeps the stated limits honest.

## 4. Evidence (conditions 4a to 4e)

| | What | How |
|---|---|---|
| 4a | flag on gives an identical end hash | An **evidence wrapper**, in the pattern of lane A's `arm_child_flight.py`: `build_kernel`, set the flag on `kernel.state.feature_flags`, the same tick loop, the same `final_hash`. `PYTHONHASHSEED=0`, 5000 ticks, on crowded s42 to s46 and urban s46. The wrapper's ON hash must equal plain `arm_child`'s hash on all 6 cells. Base cells are reused where main's tree is unchanged. No change to `tools/rpg_measure` for v1. |
| 4b | an on/off equivalence test in the PR | same hash and same event count, audit on against off |
| 4c | off by default; no lazy-property reads; nothing in hashed state | §3 |
| 4d | writes none of the fields in `TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ` | stated in the PR, with the observer's write list |
| 4e | timing NOT MEASURED | the PR makes no perf claim |

**Slot:** the 6 cells are heavy and come from rpg-planner's u24 queue: after the hit-wake re-measure, before A+B. Unit and scoped tests
are not heavy.

## 5. Reads: v1 has none; a v2 proxy is its own ticket

- **v1:** no read-proxy. Reads come from the declarations plus static inspection (class S).
- **v2**, a read-proxy of `state` built in the prologue, is allowed only:
  - as its own ticket, after v1's report has been read;
  - with its plan sent to rpg-planner first;
  - with its own 4a and 4b cells, plus an on/off event-count check.
- **Hazards a v2 proxy must handle, or be rejected for:**
  - the prologue's `object.__setattr__(state, "occupancy_snapshot", …)`: a proxy must forward attribute writes to the real
    object, or that cache lands on the proxy;
  - steps that call `getattr` or `isinstance` on state: a proxy must pass identity and `isinstance` through.

## 6. What the report must answer (for child 4)

- For each step: declared against observed writes, field by field.
- Every hidden mutation, with the step, the field and the tick count it was seen in.
- **"No hidden mutation observed" only for the kinds a positive control proved detectable (§3a), never "none exist".** The
  report repeats §3a's blind spots.
- Every process-global change.
- The steps whose observed writes reach another entity's entry. These are the cross-entity rows that child 4's merge rules must
  cover: cooperation's JOIN_PARTY promotion, trust and grudge, and the combat witness tier.

## 7. Out of scope

- Any edit inside step logic, and the files listed under "Not touched".
- Merge rules and the contract itself (child 4).
- Read tracing (v2, above).
- Any timing or perf claim.
