---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
artifact_type: test_plan
date: 2026-11-17
tags: []
---

# Test plan: births

## Unit
- Content: profile loads for each eating kind; refusal for hunger none, unknown id, out-of-range fields; no profile = no births.
- Cooldown field: remove then add in one update (same-tick re-add survives); merge unions the lists; removing an absent key is a no-op; serialise round trip if patches are serialised.
- BirthService: mother id order; mate = lowest eligible id; Chebyshev radius edge (inside/outside on a diagonal); each entity a parent at most once per check; draw keyed by (seed, tick, mother id) is order independent (shuffle candidate order, same births); fed_line edge (equal passes); cadence 30; mother pays min(cost, room); cooldown blocks both parents until expiry then allows; expired entries pruned; non-eating kinds and CHILD/dead/inactive bodies never birth; cross-species never pairs.
- Newborn: kind = species_of(parents), occupation None, CHILD, age 0, gold 0, both parent ids, birth_tick, hunger = t0 value, role MONSTER/CITIZEN rule, mother's faction, body = t0 stats at full HP, personality draw keyed by newborn id; CHILD goal multipliers still apply.
- Region +1 nudge per birth, additive across births in one region.
## Integration / scenario
- Mechanic scenario (tests/mechanic_scenarios): a real birth under default flags (two fed adult wolves near each other, run to the next 30-tick check with a fixed seed chosen by the test's own keyed draw, assert W1-W5 and K6/K6b/K8 on the result); the mother must eat again before a second birth.
- tests/integration/scenarios/test_demographics.py population-pressure test retargeted.
- Determinism: same seed twice gives the same state hash; checkpoint save/load around a birth tick.
- Architecture: spawn-site table has one births site; BirthService leaves the input state unmutated; entity added only via the apply path.
## Removed
- Section 5 of plan.md lists each deleted or rewritten old test.
## Local checks before any push (S10)
- Targeted tests including slow and extra_slow (tests/mechanic_scenarios/**, tests/integration/scenarios/**), import contract, code health, mypy on touched files, ruff. Full CI-equivalent only if the PR touches the kernel/engine loop (world_dynamics.py hook is a section of it: I will run the CI-equivalent and say so), tools/test_architecture, conftest/pytest config or CI config.
