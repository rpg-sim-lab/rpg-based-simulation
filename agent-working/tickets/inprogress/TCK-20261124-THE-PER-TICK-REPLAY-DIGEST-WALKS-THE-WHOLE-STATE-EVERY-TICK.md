---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
phase: inprogress
date: 2026-11-24
tags: []
---

# TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK

## Title
The per-tick replay digest rebuilds and re-sorts the whole canonical state every tick: make it cheaper with byte-identical digests

## Status
INPROGRESS

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Owner decision #715 7123298032, item 2: "Faster hash, same output". perf-planner drafted the brief, and lead-planner relayed it to rpg-planner-ubuntu on 2026-11-24.

The evidence is perf step 0 (GO 7122627318; result /data/vboxuser/perf_runs/obs_attr_result.md, sha256 5b06fd294766184ef48c5035fbf7a28a1e266735ef6f967c28f94771c6b314cb). The run was PROVISIONAL: frontier_living_world s42, 2000 ticks, audit_mode, on a loaded host, frozen tree 613a8365bcd1.
- The per-tick replay digest costs 74.3 ms per tick, which is 81 % of the 91.9 ms replay cost. The digest is `CanonicalHashScheduler().compute_digest(state, tick, reason="replay")` at src/engine/kernel.py:1113 (`_phase_persistence`), which calls `CanonicalStateHasher.get_hash` in src/engine/checkpoint.py.
- The digest is also what grows over a run: replay-on arms go from 160 to 198 ms between run halves, while digest-stubbed arms stay flat.
- The fingerprint costs about 4.9 ms, which is inside the noise.

`get_hash` builds a full nested dict (`to_canonical_data`): every entity's `to_canonical_dict()` plus every keyed collection, each sorted. `json.dumps(sort_keys=True)` then sorts every level again, and the result is hashed with SHA-256.

## Scope
- Make `CanonicalStateHasher.get_hash` (as reached by the per-tick replay call) cheaper, with BYTE-IDENTICAL output: the same canonical JSON bytes, so the same digest string for every state. The approach is the implementer's, to be stated in plan.md and approved by rpg-planner-ubuntu before code. Candidates from the brief:
  - Per-entity or per-entry cached canonical JSON fragments, rebuilt only for what changed (for example from the DirtySet, src/core/dirty.py). Any cache must be proven equal to the full walk.
  - Emit already-sorted fragments instead of building a dict and then re-sorting it in `json.dumps`.
  - A faster encoder, only if it is byte-identical for every value type: floats (repr and exponent forms), big ints, non-str dict keys (int, tuple and None key coercion by json), NaN/Infinity, bool vs int, nested empty containers and non-ASCII strings.
- Keep `to_canonical_json`, `to_canonical_data` and the scheme as they are. `PROOF_DIGEST_SCHEME` is `flat-sha256-v5` on main (checkpoint.py:21; the brief said v4) and does not change.
- An old-vs-new equality test. The current full walk is kept as the reference function (test-only, or as a private slow path). The test compares the two over:
  - real ticks of at least 2 worlds, frontier_living_world among them;
  - audit-mode and non-audit paths;
  - ticks where the dirty set is partial, ticks with force_full_scan, entity spawn and death, and collection insert and delete;
  - a planted in-place mutation that a cache would miss, which must be caught by the test or the design.
- Update docs/engine/deterministic_execution.md ("The canonical hash") if its description of how the digest is built changes, and the parity ledger (docs/parity_ledger/infrastructure.yaml) and mechanism registry entries if checkpoint.py's behaviour notes change.

## Out of Scope
- The fingerprint (`StateFingerprinter`), the replay write path and chunk writer, hash cadence and policy (when the digest is computed), `compute_digest` semantics, and the scheme version.
- Any change to what the digest covers (for example TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ and TCK-20261023-PRESSURE-SIGNALS-SWITCH-FEATURE-FLAGS-OUTSIDE-THE-HASH stay separate).

## Acceptance Criteria
1. The new old-vs-new equality test passes over at least 2 worlds' real ticks, including the audit-mode and dirty-set paths, and the planted-mutation case is shown handled. All existing hash, replay, certification and parity tests pass.
2. Replay bytes are unchanged: the per-chunk sha256 of every chunk_*.json and the final hash are equal between the branch and its own merge base on frontier_living_world s42, 2000 ticks, replay on, audit_mode. Both arms run under one heavy-slot GO from lead-planner, on fresh git-archive trees with a record set. On the same base, the final hash is also compared with perf's reference c12afb16a10d at /data/vboxuser/perf_runs/obs_out_613a8365bcd1_s42_attr/tree-data-runs/1_OFF_replay, as context only: that reference was recorded at 613a8365bcd1, so equality with it is not required if main has changed simulation behaviour since.
3. The governor's no_replay and buffer-drop paths are unchanged (tests named in the plan).
4. No new whole-state serialization on the tick thread (hot-path contract). Any cache is per-entry, bounded by the state, and has a stated lifecycle (durable-state rule: if it survives the tick, it is typed, located, and inspectable).
5. perf-planner measures before and after under its kit, with its own GO. This ticket reports the result and makes no performance claim of its own.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
- TCK-20261122-WHAT-OBSERVABILITY-COSTS-THE-TICK-RECORDING-ON-VS-OFF-ON-MAIN
- TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER

## Related Docs
- docs/engine/deterministic_execution.md ("The canonical hash")
- docs/engine/contracts/substrate_baseline_contract.md (section 7, Canonical Checkpoint Law)
- docs/engine/performance_contract.md
- docs/performance/hash_callsite_inventory.md
- docs/plans/design_enhancement/performance_optimization/replay_write_path_design.md (on perf-replay-write-path-design, fbb531a2b, local)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK/owner_decision_2026-11-24.md

## Related Code Areas
- src/engine/checkpoint.py (CanonicalStateHasher, CanonicalHashScheduler)
- src/engine/kernel.py (_phase_persistence, line ~1113)
- src/core/dirty.py, src/core/state.py (to_canonical_dict producers)
- tests/unit/engine (hash tests)

## Assumptions / Open Questions
- Whether every mutation that changes a `to_canonical_dict()` result goes through a path the DirtySet sees is not verified. src/core/dirty.py has a `DirtySetLeakError`, which suggests leaks have been a concern. The investigation answers this before any cache design is chosen. If it can't be shown, the design must not rely on the dirty set.
- The 74.3 ms figure is provisional (one world, one seed, a loaded host). The share (81 %) is the actionable number.

## Implementation Notes
- 2026-11-24, lead-planner agreed (session message): the scheme is v5 (the brief's v4 was a relay error); AC2 is the merge-base comparison under one GO, with c12afb16a10d as context only; dirty-set coverage is proven first or the dirty set is not used. The design doc is readable now through the shared object store: `git show fbb531a2b:docs/plans/design_enhancement/performance_optimization/replay_write_path_design.md` (committed, unpushed).

## Test Summary

## Files Changed

## Completion Summary
