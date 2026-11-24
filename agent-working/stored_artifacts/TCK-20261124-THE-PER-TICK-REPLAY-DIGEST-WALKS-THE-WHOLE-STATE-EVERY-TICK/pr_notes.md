---
status: historical
layer: performance
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK
date: 2026-11-24
tags: []
---

# PR notes: the per-tick replay digest memo (draft for the PR's Review notes)

## What and why
The kernel's per-tick replay digest rebuilt the whole canonical state every tick (about 51 % dict build, 47 % `json.dumps`, 3 % sha256 at ticks 250 to 300 of frontier_living_world s42). Every entity object is replaced every tick, so the entity-level memo never hits, while most components are the same objects as the tick before. A kernel-owned `CanonicalFragmentMemo` now reuses the strategic and social strata of unchanged components for the PER-TICK digest only. The digest, `flat-sha256-v5`, the checkpoint format, the replay form and the fingerprint are unchanged.

## AC2 evidence (sealed)
NEW 76732f456 vs BASE 36a7e2089 (the merge base), frontier_living_world s42 and crowded_frontier s42, 2000 ticks, replay on, audit_mode, cpus 4-5. Final hashes equal (ee6a180a… and a658e258…); 20 chunks per arm per world, 0 differing with the frozen wall-clock leaves masked; raw chunk sha256s equal 0 of 20 (information only). Run dir /data/vboxuser/replay-digest-runs/76732f45626238f766a5bc1ca6ddf34ca53b073c/out, SHA256SUMS ce0c3f9af354fa2d58c990f7f5c6519f6d9d47a4b51db529efc9e2a487d6074a, KIT_SHA256SUMS e6cb23bda757398870975f03d2e9b9f6ed4311f4970d1159377b623bd92d8fae. The perf context hash c12afb16a10d (tree 613a8365bcd1) does not match BASE: main changed since, context only.

## Audit cost
CANONICAL_MEMO_AUDIT_PERIOD = 100, audit_mode only: 20.1 ms per call on frontier_living_world and 10.3 ms on crowded_frontier at tick 300, 0.20 and 0.10 ms per tick amortised. Perf's audit_mode measurement will contain it. AC5 (perf's own before and after) is open: no performance claim here.

## Known gaps
- The scan for in-place writes to a field of the two components does not follow a container passed to a helper as an argument or reached by getattr, and is no proof about future code.
- A memoized component mutated in place stays invisible to the per-tick digest until the component is replaced. Under audit_mode it is detected within 100 ticks; outside audit_mode it is not. A component mutated in place and replaced within one period is not seen. Stated in deterministic_execution.md and known_limitations.md.
- Pre-existing on main, identical on a clean archive: the three certification long-run stability tests and one thread-leak error; the tests/perf timing tests fail on the 60 s resource timeout.
- pyrefly (advisory) shows 133 differences with the shared venv's version: untriaged.
- A worktree-only failure of test_state_digest_covers_every_field in a combined run (passes alone and on three clean archives).

## For later PRs
A PR that lands after this one and changes EntityState.to_canonical_dict, strategic_canonical_dict or social_canonical_dict must update tests/unit/engine/canonical_reference.py in the same change. Whichever of this PR and #996 lands second re-runs test_canonical_digest_equals_reference.py after its resync.
