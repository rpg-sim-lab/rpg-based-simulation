---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
artifact_type: test_plan
---

# Test plan

Scoped runs at `-n1` with the scratch-deps venv first on PATH; timing NOT MEASURED (perf pause).

- `tests/unit/engine/test_last_hit_damage.py` (13): carrier merge, write condition, canonical round trip, digest v4 and its stripped form.
- `tests/unit/tactical/test_flight_weighs_free_swing.py` (20): the designer's rows, LEASH_RETURN mirror, FLEE_THREAT with the felt attacker not engaged, the FLIGHT_REASONS coverage walk, drop-guard discrimination, swap rows.
- `tests/mechanic_scenarios/test_flight_weighs_free_swing_through_kernel.py` (3): kernel scenario with a control arm.
- Updated pins: `test_proof_digest_contract.py`, `test_proof_digest_populated_parity.py`, `test_hash_scheduler.py`, `test_benchmark_record.py`, `test_long_run_record.py`.
- Run results: 136 passed on the field commit; 431 passed in `tests/unit/perf`.
- Known gap: the broad sweep was never completed on this branch; CI is the first full run.
- Measurement evidence: `evidence/` (wrapper, rows builder, three row files).

## Proof Plan

- Level: unit (carrier, guard rows), mechanic scenario (kernel run with a control arm), paired 5-seed simulation measurement.
- Proof kind: behaviour change guarded by discriminating tests (drop-guard checks) plus a measured paired comparison against the unguarded base.
- Oracle source: the designer spec rows; the base arm's stripped digest for hash equivalence; the Tier 1 and Tier 2 bar fixed before the runs.
- Expected effect: a fighter whose last felt blow would kill it stays and answers the hostile; DEFEAT deaths on the flight tick fall, COMBAT rises (relabel), deaths do not rise overall.
- Selected commands: `pytest tests/unit/engine/test_last_hit_damage.py tests/unit/tactical/test_flight_weighs_free_swing.py tests/mechanic_scenarios/test_flight_weighs_free_swing_through_kernel.py tests/unit/perf -n1 -m "not slow"`; the arm wrapper in `evidence/` for the measurement.
