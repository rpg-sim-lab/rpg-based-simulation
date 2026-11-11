---
status: active
layer: engine
authority: P1
audience: agent
last_verified: 2026-10-03
---

68: 
69: `audit_mode` zeroes the timing and resource signals, so it suppresses the first input, and it silences the overrun report in the second and third (`flags["audit_mode"]`, `src/engine/kernel.py`). It removes the one remaining wall-clock input that changes what is computed, but it is **not sufficient on its own for a deterministic run**: before `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`, identical `audit_mode` runs (raised budget, sequential executor, no dropped work, governor in `NORMAL`) diverged from tick 5 because `DirtySetBuilder.mark_from_update` skipped entity updates by `id()` and a recycled address silently dropped an entity from the dirty set (`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`). That cause is removed, and no trial diverged in 144 short (8-tick) trials after the fix, where bare `main` diverged in 8 of 96; this is a measurement over short runs, not a proof of determinism, and a second `id()`-keyed cache (`get_frozen`, `src/engine/executor.py`) was probed without a stale hit but is not proven safe. `audit_mode` is still not the Canonical contract, which has no implementation yet (`PERF-M1`).
70: 
148: 
149: Workers receive `AuthoritativeState.readonly_view()` — a frozen snapshot. Any attempt to mutate durable state from a worker (outside the authoritative apply path) is a protocol violation caught by audit mode.
150: 
