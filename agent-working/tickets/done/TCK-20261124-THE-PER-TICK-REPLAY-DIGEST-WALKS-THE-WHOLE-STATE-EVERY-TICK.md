---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
phase: done
date: 2026-11-24
tags: []
---

# TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK

## Title
The per-tick replay digest rebuilds and re-sorts the whole canonical state every tick: make it cheaper with byte-identical digests

## Status
DONE

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

## Durable state, lifecycle and clocks
The memo (CanonicalFragmentMemo) is derived, non-authoritative state held by one Kernel instance: created in Kernel.__init__, filled by the per-tick replay digest, pruned to the live components of the state just digested (at most 2 x the entity count), never pickled into a checkpoint, never replayed, never shown by a presenter; a new or restored kernel starts empty. It adds no authoritative state, no field to any record, no clock (the audit cadence is the tick number). It is inspectable through its len, its hit and miss counters and `audit()`.

## Implementation Notes
- 2026-11-24, lead-planner agreed (session message): the scheme is v5 (the brief's v4 was a relay error); AC2 is the merge-base comparison under one GO, with c12afb16a10d as context only; dirty-set coverage is proven first or the dirty set is not used. The design doc is readable now through the shared object store: `git show fbb531a2b:docs/plans/design_enhancement/performance_optimization/replay_write_path_design.md` (committed, unpushed).
- 2026-11-24, rpg-implementer-ubuntu: approach A, a kernel-owned typed memo, approved by rpg-planner-ubuntu after the investigation stopped on condition 3 (a new record slot is a checkpoint schema append: it changes every checkpoint and refuses the old ones unless two ruling-backed FIELD_RULES rows are added). Plan, rejected options and every addendum: stored_artifacts/TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK/{investigation,plan,test_plan}.md.
- What changed: `CanonicalFragmentMemo` (src/engine/checkpoint.py), held by `Kernel._canonical_memo` and passed only by the per-tick replay digest; `strategic_canonical_dict` / `social_canonical_dict` (src/core/state.py) are the old inline blocks moved verbatim; `EntityState.to_canonical_dict(memo=None)`; a memo-path build is never stored in the entity's own `_canonical_cache` (found in review: it leaked the memo's dicts into the final digest); under audit_mode the kernel audits the memo every `CANONICAL_MEMO_AUDIT_PERIOD` = 100 ticks (`CanonicalFragmentMemo.raise_if_stale`, ProtocolViolationError). No digest, scheme (flat-sha256-v5), checkpoint, replay or fingerprint change.
- Mechanism advisory (run at close): 4 drift findings (personality, buildings, city, camp cite src/core/state.py). rpg-planner-ubuntu's judgment: no entry change, since the cited behaviour is unchanged.
- Local measurement outside the product: dirty set cannot be used (all 55 entities dirty every tick; about 20 collections have no DirtySet field; leaks observed); per-tick cost split about 51 % dict build, 47 % json.dumps, 3 % sha256 at ticks 250 to 300 of frontier_living_world s42; memo hit rate 77 % (frontier) and 83 % (crowded) over 2000 ticks.
- Not done, on purpose: Stage 2 (a JSON-text splice), any fingerprint, cadence, replay-write-path or scheme change, any perf claim.

## Test Summary
- New tests (31 + 12, none heavy): tests/unit/engine/test_canonical_digest_equals_reference.py (digest, compact JSON, pretty JSON and data dict equal to a verbatim copy of the old build, tests/unit/engine/canonical_reference.py, every tick x 70 on frontier_living_world and crowded_frontier, warm and cold; kernel TICK_END hashes; force_full_scan and certification path; spawn, death, insert, delete; fully filled components and encoder-sensitive values; E9-E11 an in-place write, a poisoned entry and a caller edit are found by the audit; E14 pickle restore cold == warm; E16 a restore that fills a strategic field starts with an empty memo; E17 the grief flush on a warm kernel; E18 and the cache walk: the memo path never leaks a dict into the plain path; the periodic audit (a) to (d) and read-only; real audit_mode runs through ticks 100 and 200) and tests/tools/test_replay_digest_kit.py (12). Mutations M1 to M7 each fail the equality file.
- Regression at the final code (cpus 0-3, 3G, sequential): tests/unit/engine 1313 pass; unit/kernel+core+perf+replay 1007 and unit/kernel+perf 581 pass; tests/architecture 259 to 278 pass; integration/kernel 146 pass; tests/tools all pass (two corpus tests MemoryError inside the 3G chunk and pass alone); certification minus long-run 78 pass. code-health OK (2 report-only jscpd rows in src/observability not mine; kernel.py 1350 lines against its 1357 ceiling, no ceiling touched), mypy OK, import contracts 17 kept 0 broken, docs-registry in sync.
- Known failures that are identical on a clean origin/main archive (not caused by this change): tests/certification/test_cert_long_run_stability.py x3 and the QueueDrainWorker thread-leak error attached to tests/static/test_workflow_run_blocks_take_github_context_via_env.py; the tests/perf timing tests fail on the conftest 60 s resource timeout (11 rows compared, main vs branch, the same except test_perf_mixed_stress which also timed out on main). One architecture test (test_state_digest_covers_every_field) failed twice in the combined run inside this worktree only and passes alone and on three clean archives.
- AC1 met (equality over 2 worlds, audit mode, dirty-set paths, planted mutations). AC2 met: sealed run /data/vboxuser/replay-digest-runs/76732f45626238f766a5bc1ca6ddf34ca53b073c/out, SHA256SUMS sha256 ce0c3f9af354fa2d58c990f7f5c6519f6d9d47a4b51db529efc9e2a487d6074a (149 entries), KIT_SHA256SUMS e6cb23bda757398870975f03d2e9b9f6ed4311f4970d1159377b623bd92d8fae; NEW 76732f456, BASE 36a7e2089 (the merge base); frontier_living_world s42 2000t final hash ee6a180a55cf3d450d04fd56943a7acca5cd880c14fb35fd8dc7c4244400d013 (NEW = BASE) and crowded_frontier s42 a658e258ffb756c849dcbcf5f640c0d885fd383456232a0072a7d7beeef70872 (NEW = BASE); 20 chunks per arm per world, 0 differing under the frozen mask (cooperation_phase_ms and sub_phase_costs.*, found by a BASE smoke and proven complete by a second smoke), raw chunk sha256s equal 0 of 20 (information only: wall-clock timers); positive controls ok; the c12afb16a10d context comparison does not match (main changed since that tree; context only). AC3 met (the kernel's governor and replay branches untouched; the named tests pass). AC4 met (no new whole-state serialization; one typed memo per kernel, bounded at 2 x entities by per-digest pruning, never pickled).

## Files Changed
- src/core/state.py, src/engine/checkpoint.py, src/engine/kernel.py (the memo, the moved strata, the audit call).
- docs/engine/deterministic_execution.md ("The canonical hash") and docs/engine/known_limitations.md (the limit line).
- tests/unit/engine/canonical_reference.py, tests/unit/engine/test_canonical_digest_equals_reference.py, tests/unit/engine/test_kernel_digest_via_scheduler.py (a spy takes **kwargs), tests/tools/test_replay_digest_kit.py.
- tools/rpg_measure/replay_digest_{arm.py,compare.py,launch.sh,wall_clock_keys.jsonl} (the AC2 kit).
- agent-working/stored_artifacts/TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK/ (investigation, plan, test plan, owner decision, PR notes), this ticket, docs/REGISTRY.yaml, monitoring shards.
- Parity ledger and mechanism registry: no entry changed (behaviour unchanged; the mechanism advisory is rpg-planner-ubuntu's judgment).

## Completion Summary
The per-tick replay digest now reuses the strategic and social canonical dicts of components that did not change, through a kernel-owned, bounded, never-persisted memo, and produces the same bytes: AC2 final hashes and every chunk (wall-clock timers masked) equal NEW vs BASE on two worlds at 2000 ticks. A memoized component mutated in place would stay invisible to the per-tick digest; that is detected under audit_mode within 100 ticks and is stated in deterministic_execution.md and known_limitations.md. AC5 (the before and after measurement under perf's kit, with perf's own GO) is OPEN: this ticket makes no performance claim; the only numbers here are the local profile shares, the memo hit rates and the audit cost (20.1 ms per call on frontier_living_world and 10.3 ms on crowded_frontier at tick 300, 0.20 and 0.10 ms per tick amortised at N = 100). Follow-ups outside this ticket: TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE (rpg-planner-ubuntu's); pyrefly's 133 advisory differences with the shared venv are untriaged.
