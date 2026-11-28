---
status: active
layer: engine
authority: P1
audience: developer
---

# `src` Known Limitations

This document records the current technical limitations, unsupported features, and runtime constraints of the `src` engine.

> **Machine-readable state:** For a queryable capability matrix, see `docs/engine/capability_registry.yaml` and `src/engine/capability.py`. This document keeps only human-readable context and notes.

## 1. Gameplay / Mechanics Limitations

### 1.1 Spatial / Navigation
- **Linear Stepping Only**: Pathfinding through dynamic obstacles (e.g., other entities or newly spawned objects) is best-effort. V2 currently relies on direct linear stepping toward coordinates for supported proofs.
- **Congestion Weakness**: While congestion is handled by yielding, high-density entity overlaps are not yet hardened against all edge cases.
- **Mutual-pursuit diagonal deadlock** (`TCK-20260810-NAVIGATION-SINGLE-AXIS-STEPPING-DIAGONAL-PURSUIT-DEADLOCK`): `NavigationSystem.get_next_step()` (`src/systems/world_systems/navigation.py:99-103`) is a single-axis-priority stepper — it moves exactly one axis per tick, favoring Y on an exact `|dx| == |dy|` tie. When TWO entities are simultaneously, mutually pursuing each other (both live-retargeting to the other's current position every tick, per `TCK-20260809-COMBAT-PURSUIT-PER-TICK-TRACE`) and land on a perfectly diagonal offset, both entities' own tie-break resolves identically (Y-axis), and their moves cancel each other's progress every tick — an infinite, deterministic orbit with the Manhattan distance between them held perfectly constant. Confirmed analytically (a standalone re-implementation of the tie-break rule reproduces the exact real corpus trace) and empirically via a real, non-mocked `Kernel.tick_once()` loop. A single-sided pursuer chasing a static or non-reactive target is NOT affected — it converges normally via a staircase path (verified separately); the deadlock requires BOTH sides to be reactively re-targeting each other. **Real corpus prevalence measured, not assumed**: across 3 seeds (42/123/456) × up to 8 corpus worlds (`dungeon_crawl`, `urban_political`, `wilderness_survival`, `crowded_frontier`, `swamp_border_world`, `hero_guild_routing`), 2000 ticks each, exactly 1 real pursuit pair (out of the full sample) ever entered a genuine, sustained (≥20-tick) deadlock — the specific pair already known from `TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS`'s own investigation, seed 42, `dungeon_crawl` only. All other seed/world combinations showed either zero mutual-pursuit interactions on an exact diagonal offset, or trivially short (1-9 tick) coincidental ties that resolved normally on the next tick. **Disposition**: a real, confirmed, deterministic bug, but rare enough in practice (a specific spawn-geometry coincidence, not a systemic pattern) that a stepping-algorithm change was judged disproportionate to the real, measured impact — documented here rather than fixed, per this ticket's own explicit "document-and-defer if rare" scope branch.

### 1.2 Resource loops
- **No Complex Regeneration**: Resource nodes do not currently support complex regeneration logic (e.g., seasonal growth, depletion cooldowns). Nodes are static or reset on scenario reload.
- **Town Buildings**: `TownResolutionSystem` currently supports Blacksmith (crafting), Inn (REST), and Tavern (EAT) building types. Guilds, Class Halls, and other building types are not yet functionally integrated.
- A decaying corpse's items other than gold and raw meat leave the world with no typed sink: gold becomes a ground purse and raw meat leaves through MEAT_DECAYED, but nothing records anything else (`TCK-20261118-A-DECAYING-CORPSE-DESTROYS-EVERY-ITEM-EXCEPT-GOLD-AND-MEAT-WITH-NO-SINK`). ch. 03 atomic conservation is still the target law; the ruled fix makes them ground items at the corpse tile.
- Wild births (`TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND`): the own-job run measured one cell (frontier_living_world s42, 5000 ticks: 7 spider births). Undead risings were NOT EXERCISED: 0 risings is expected by content (`rise_chance_per_check` 0.002 per 30-tick check, a corpse decays 100 ticks after death, so about 0.2 expected risings on the cell, P(0) about 0.8), so the rising checks R1-R4 need a forced rise (`TCK-20261128-MEASURE-UNDEAD-RISINGS-ON-A-CELL-THAT-HAS-A-RISING-SOURCE`). The combat cost of newborns (check 3) is NOT MEASURED as a cost finding (the kit's DeathWatch had a defect); the recount from the final states is COMBAT deaths head 23 vs control 19, 0.140 vs 0.128 per 1000 live entity-ticks (ratio 1.10), 0 newborn victims, killer kinds NOT MEASURED (kit on `evidence/births-kit @ 2d52926ac`, not in main). Humans do not conceive inside the compressed test windows (mate gate, divergence 2.225).
- Six social actions (TRADE, TEAM_UP, TRAIN, PROPOSE_MARRIAGE, JOIN_CLAN, LEAVE_CLAN) are built and unit-tested but have no issuer in play, and no clan exists in play (TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY). Making any of them reachable is an owner gameplay decision.

### 1.3 Strategic AI
- **Material-Only Blockers**: The `StrategicIntelligenceSystem` only recognizes and resolves crafting blockers for "Material" resources. Social, capability, or plot-based blockers are unsupported.
- **Location-Only Leads**: Strategic leads are restricted to coordinate-based locations. Concept or person-based leads are not yet modeled in the supported slice.
- **The Perception Threshold Margin Holds Only At The Default Alertness**: the gate's threshold (0.15) sits 10% above the still-body ceiling (0.135: a baseline observer's still hearing or smell) at the default alertness 0.5; at alertness 1.0 a baseline observer would hear a still body (0.18). No src caller passes `alertness` (a guard test fails if one does); whoever wires it re-checks the margin (PERC 3a, divergence 2.229, TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT). The calibration also makes the gate's reach longer than the 10-tile decision radius for a large body by day (16 Manhattan tiles): a decision reads only what lies within its own radius.
- **The Perception Calibration's Own-Job Run Leaves Three Things Open**: measured on 3 gate worlds x s42 x 1000 ticks, base ac759e0ba to fix bbce8de04 (#715 GO 7238294011; evidence branch `evidence/perception-gate-calibration-kit` @ 9622465db; TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT). (1) The hunt path is not exercised: `hunts_started` is 0 in every world on both arms, so the run says nothing about hunts under the calibrated gate. (2) The engagement count moved without attribution: crowded_frontier 144 to 97, frontier_living_world 129 to 222, urban_political 69 to 85; the drop is not explained (follow-up TCK-20261128-ATTRIBUTE-THE-CROWDED-FRONTIER-ENGAGEMENT-DROP-AFTER-THE-PERCEPTION-CALIBRATION). (3) The gate costs wall time: about 12% per tick in frontier_living_world (x1.13) and urban_political (x1.12), x1.02 in crowded_frontier (measured, not optimised: standing rule). `bodies_hit` is not measured (a kit off-by-one).
- **Unchecked Sense Profiles On Mid-Run Spawns**: bodies spawned mid-run by `EntityGenerator` (used by lairs, bosses and calamities) aren't yet checked for a usable sense profile at build. A body of a species without one isn't refused (PERC-02a, ch. 04); instead it perceives nothing, and the gate logs ERROR (`TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK`). Campaign episode, scenario-runner and checkpoint-restored bodies are checked since #968.

- **A Dead Body's Quest Project Ends While Its Quest Stays Open**: when a subject dies, every live project it holds ends `ABANDONED` with `ended_by` `ProjectEnd.DEATH` (divergence 2.226, STRAT-357), but a quest project's own `quest_status` is left as it was; the quest domain does not learn of the death through this path. No measured case: three gate worlds, s42, 5000 t, had 0 such quests still open (TCK-20261031-DEATH-CLOSES-NO-PROJECT). A passive HP death is also classified one tick after its `alive=False`, so its project end lags that tick (0 lag rows in the same run).

### 1.4 Commerce Limitations

- **Reputation-based shop discounts** — Previously unsupported. **Now implemented** as of TCK-20260619-E33D-REP-DISCOUNTS. Formula and mechanics: see `docs/mechanics/03_economic_laws.md §4.1`. Faction-scoped discounts remain out of scope (no per-faction reputation dict on `SocialComponent` — DEV-001).

### 1.5 Feature Flag Defaults (Phase 10 Rollout Gates)

Eight of the 11 Phase 10 feature flags in `src/domains/optimization/feature_flags.py` default to
`FeatureMode.OFF`. Three default to `FeatureMode.ON`: `ENABLE_COMBAT_ENGAGEMENT`
(`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`), `ENABLE_BELIEF_ASSIMILATION` and
`ENABLE_SOCIAL_COOPERATION` (both `TCK-20260824-ROLLOUT-FLAG-DECISIONS`, DEV-003). Each was
flipped deliberately, with its reason in the comment block at the flag's definition, and is
named in the allowlist of intended ON defaults in
`tests/integration/test_scenario_feature_flag_defaults.py`. The flags are:

- `ENABLE_WORLD_CAPABILITY_LAYER`
- `ENABLE_SELF_MODEL_COGNITION`
- `ENABLE_ADVENTURE_ROUTING`
- `ENABLE_COMBAT_ENGAGEMENT` (default ON)
- `ENABLE_BELIEF_ASSIMILATION` (default ON)
- `ENABLE_INFORMATION_INTENT_EXECUTION`
- `ENABLE_PROGRESSION_EVOLUTION`
- `ENABLE_SOCIAL_COOPERATION` (default ON)
- `ENABLE_WORLD_EMERGENCE`
- `ENABLE_LIFE_ARC_CAMPAIGNS`
- `ENABLE_ENHANCED_TRACE_EVENTS`

**Implication for balance and behavioural measurement:** Any scenario or test that needs to
measure behaviour gated behind one of these flags must explicitly enable the flag via the
`overrides` constructor argument or `FeatureFlagManager.set_flag_mode()`. The existing
`_build_kernel(enable_routing=True)` pattern in
`tests/integration/scenarios/test_balance_regression.py` is the canonical example.

**`ENABLE_ADVENTURE_ROUTING` no longer gates anything (as of
`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`):** the phase it used to gate,
`adventure_decision` (`AdventureDecisionPhase`), was deleted from `src/engine/pipeline.py`'s
`refine()`. Its replacement, `AdventureGoalScorer` (`src/ai/goals/adventure_scorer.py`), is a
tier-5 `GoalScorer` that runs unconditionally as part of `StrategicIntelligenceSystem`'s
per-entity scoring — it does not read `ENABLE_ADVENTURE_ROUTING` or any other feature flag (see
`docs/parity_ledger/strategic_cognition.yaml` STRAT-252). The flag entry still exists in
`FeatureFlagManager` and remains default-`OFF` for backward compatibility with existing scenario
configs and tests that set it, but flipping it ON or OFF no longer changes any live behavior.
The other 10 flags in this list are unaffected and still gate real pipeline phases via
`run_phase(..., feature_flag=...)`.

**Do not change the default to `ON` without first re-running `tools/balance_measure.py`** on
the affected scenario (e.g. `urban_political`, seed 42, 100 ticks) to establish new baseline
constants, and updating the corresponding constants in `test_balance_regression.py`.

The sentinel test `test_adventure_routing_defaults_off()` in
`tests/integration/scenarios/test_balance_regression.py` guards the `ENABLE_ADVENTURE_ROUTING`
default. If you intentionally change the default to `ON`, that test will fail with an explicit
error message and instructions for updating the baseline.

Decision recorded in `docs/guidelines/intentional_divergences.md` § DEV-002
(TCK-20260627-P0A-ADVENTURE-FLAG).

## 2. Runtime / Performance Constraints

### 2.1 Execution Modes
- **Worker Parity**: While concurrency (Thread/Worker) is implemented, bit-identical parity vs original `src` is only officially ratified for the **Sequential** execution mode.

### 2.2 System Contention
- **Deterministic Resolution**: Contention for limited resources (e.g., two entities looting the same corpse) is resolved by deterministic registration order. Complex social negotiation or "roll-off" logic is not yet implemented.
- **HTTP Admission Control — Single-Process Only**: Per-client HTTP admission control now exists (`src/api/admission_control.py`, `INFRA-378`), resolving the previously-unbounded "no rate limiting on the HTTP API surface" boundary this doc tracked. It is scoped to single-process in-memory state — there is no distributed/multi-worker-process rate-limit coordination. An operator running `src/api/server.py` behind multiple worker processes (e.g. `uvicorn --workers N`) gets independent per-process admission state, not a shared per-client limit across the whole deployment.

### 2.3 Phase Isolation Detection

**Isolation breaches in non-audit phases are only fully caught in `audit_mode=True`.**

The Kernel's `_guard_stability()` method computes the MD5 fingerprint (`AuthoritativeState.fingerprint()`, over selected state domains, not all fields; see §2.4) before read-only phases (Scheduling, Collection) and raises `ProtocolViolationError` on any mutation. This full check is **only active when `Kernel` is initialized with `audit_mode=True`** (used in certification scenarios — see `src/certification/harness.py`).

A **lightweight gross isolation guard** (`_guard_gross_isolation()`) runs unconditionally in standard (non-audit) mode. It checks only `len(state.entities)` and `state.tick` — two O(1) integer reads with negligible overhead on all hardware classes. This detects:
- Entity creation or deletion mid-phase (gross lifecycle violation)
- Tick number advancing outside the authoritative pipeline

It does **not** detect field-level mutations within existing entities (e.g., an HP change during Collection). Those require `audit_mode=True`.

**Summary of detection coverage by run mode:**

| Violation type | Standard mode | `audit_mode=True` |
|---|---|---|
| Entity count change mid-phase | Detected (lightweight guard) | Detected (full hash) |
| Tick advancement mid-phase | Detected (lightweight guard) | Detected (full hash) |
| Field-level mutation within entity | **Not detected** | Detected (full hash) |

Source: D09 Finding 5 (Risk 11/15). Ticket: TCK-20260627-P1G-STABILITY-GUARD.

### 2.4 Canonical State Hash Availability by Runtime Mode

`_phase_persistence()` in `src/engine/kernel.py` records a per-tick digest value under the payload
key `"hash"` of the `TICK_END` replay event. Whether that value is a real SHA-256 (the proof
digest, `flat-sha256-v5`; see `docs/engine/deterministic_execution.md`) or not computed (`null` with a
`digest_status`) depends on the active `GovernorPolicy`, and on `audit_mode`. Replays recorded before
`TCK-20261006-PERF-M1-KERNEL-DIGESTS-VIA-SCHEDULER` carry the string `"SKIPPED"` instead; see the `TICK_END` schema note in `deterministic_execution.md`:

| RuntimeMode | `replay_richness` | `replay_allowed` | TICK_END `hash` value |
|---|---|---|---|
| NORMAL | "FULL" | True | SHA-256 canonical hash |
| CONSTRAINED | "FULL" | True | SHA-256 canonical hash |
| DEGRADED | "MINIMAL" | True | `null` (`digest_status` `not_computed_live_policy`), unless `audit_mode` is on (audit mode forces the SHA-256 hash in every mode that allows replay) |
| SURVIVAL | "OFF" | False | no TICK_END event emitted |

In **NORMAL** and **CONSTRAINED** modes — the two most common runtime configurations —
`replay_richness == "FULL"`, so the proof digest is computed on every tick (`CanonicalHashScheduler.compute_digest`)
and the canonical SHA-256 is present in every `TICK_END` event.

In **DEGRADED** mode, `replay_richness` drops to `"MINIMAL"` to shed hashing overhead.
The `TICK_END` event is still emitted, but `hash` is `null` and `digest_status` is `not_computed_live_policy`.
Consumers inspecting TICK_END sequences in DEGRADED-mode runs must treat that as "not computed", never as a match.

In **SURVIVAL** mode, `replay_allowed = False`: no TICK_END event is emitted at all.

The **final canonical hash** (`CanonicalHashScheduler.compute_digest` at the run-end boundary in `Kernel.shutdown()`)
is always computed regardless of mode — it is not gated on `replay_richness`.

**Limit (`TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK`): the per-tick digest memoizes the strategic and social strata.** The kernel's per-tick replay digest reuses the canonical dict of a strategic or social component it has already built (`CanonicalFragmentMemo`). A component whose container (a dict, list or set inside the frozen record) is mutated in place keeps its old dict for as long as that component object lives, so that change is invisible to the per-tick digest. No such write exists in `src/` today (an AST scan of every write to a field of the two components found none); The rule that components are rebuilt with `replace()` is the first guard. Under `audit_mode` the kernel also runs `CanonicalFragmentMemo.audit()` every `CANONICAL_MEMO_AUDIT_PERIOD` ticks (100) and raises `ProtocolViolationError` on a stale entry, so the write is detected within that many ticks; outside `audit_mode` it is not detected, and a component mutated in place and replaced within one period is not seen. The final digest is called without the memo argument.

#### Lightweight fingerprint (`StateFingerprinter`)

In all modes where `replay_allowed = True` (NORMAL, CONSTRAINED, DEGRADED), the
`REFINED_UPDATE` event includes a `"fingerprint"` key populated by
`AuthoritativeState.fingerprint()` → `StateFingerprinter.get_fingerprint()`.

This fingerprint covers the following domains:

- Entity identity, position, HP, gold, readiness, lifecycle, skills, inventory, bonds, reputation
- Full per-entity strategic state (projects, blockers, leads, directives, concerns, contracts, boredom)
- Global resources, resource nodes, regions, local scars, groups, macro world state

The fingerprint uses **MD5** (not SHA-256). It is a broad-coverage dirty signal, not a
cryptographic determinism proof. It is the primary per-tick observability signal in
DEGRADED mode, where the canonical hash is skipped.

**Fields present in `CanonicalStateHasher` but absent from `StateFingerprinter`:**
buildings, corpses, ground\_items, chests, home\_storage, camps, blocked\_tiles, town\_tiles,
building\_tiles, periodic\_due\_ticks, work\_debt, rng\_checkpoint.

Divergences in those domains are not captured by the fingerprint. The canonical SHA-256
remains the authoritative determinism proof for complete state verification.

Source: D09 Finding 6 (Risk 8/15). Ticket: TCK-20260627-P2F-CANON-HASH-DOC.

#### Run-level `verification_level` label

The conditional gates described above (the Tier-2 `audit_mode` fingerprint gate in §2.3
and the DEGRADED/SURVIVAL canonical-hash gate above) remain deliberately conditional —
they are not made unconditionally always-on. Instead, a run's outputs carry an explicit,
truthful `verification_level` label so a consumer of the run's results knows whether the
strongest per-tick proof was available throughout the run.

`RuntimeStatus.max_mode_reached` (`src/engine/runtime_status.py`) tracks the **worst**
`RuntimeMode` reached at any point during the run — updated unconditionally inside
`RuntimeStatus.reset_dwell()`, so it is independent of the replay stream and correctly
covers SURVIVAL mode (which emits no `TICK_END` events at all) as well as a run that
dipped into DEGRADED and later recovered to NORMAL before shutdown.

At shutdown, `Kernel.shutdown()` derives:

```
verification_level = "REDUCED" if max_mode_reached >= RuntimeMode.DEGRADED else "FULL"
```

This value is cumulative, not instantaneous — a run that recovered to NORMAL by the time
`shutdown()` is called still reports `"REDUCED"` if it ever touched DEGRADED or SURVIVAL.
It surfaces in three places:

- `ShutdownResult.verification_level` (`src/core/lifecycle.py`)
- `RunManifest.verification_level` (`src/observability/reporting/artifact_repository.py`),
  written to `run_manifest.json`
- `run_report.json` / `run_report.md`'s `metadata.verification_level` key
  (`src/observability/reporting/run_report.py`)

Ticket: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC. Parity ledger: INFRA-363.

## 3. Tooling / Observability
- **Metric Granularity**: Some runtime signals (e.g., per-entity strategic bandwidth) are visible in the engine but not yet exported to the external Prometheus/Grafana baseline.

---
*Last updated: 2026-08-19.*
