---
status: active
layer: combat
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS
date: 2026-11-18
---

# Test plan: each monster kind declares why it fights

Phase 1 is docs only: no test runs needed. The list below is for the code step (scoped runs, `--basetemp` on /data, no heavy jobs without GO on #715).

## New tests (one per declared reason, plus the edges)
- hates_living: an undead engages a living body in perception; ignores a non-living body (per Q2); does not engage what it cannot perceive (night and tick passed).
- guards_place: a spirit engages a perceived body inside the radius of its home tile; ignores the same body outside it; does nothing when nobody is inside (per Q3).
- hunts_by_diet: a hungry troll or dragonkin takes prey its diet can eat and it can overcome; a sated one does not (existing appraisal tests extended to a non-wild faction).
- Faction independence: the same monster in two different factions behaves identically (no faction label read). Property-only fixtures.
- People side: people-kinds keep faction hostility among themselves (human vs bandit unchanged); a people-kind regards an aggressor monster per Q5.
- Symmetric legality (CONFLICT-03): permitted both ways when either reason names the other; refused when neither does.
- Content load: a kind that declares no reason fails the check or is explicit about it; unknown reason value rejected.
- Source scans: no production caller passes a defaulted night or tick; no call site outside the extracted hostility module asks the faction question for a monster (pins the 13 sites in investigation.md section 2).
- Determinism: twin run hash spread 0.

## Regression pins to re-read
`tests/unit/engine/test_wild_creature_regarded_by_appraisal.py`, `test_hungry_wolf_hunts_prey_it_out_bands.py`, COMB-334 and the CONFLICT-03 legality tests, the strict xfail naming M1's single-appraisal child.

## Docs and ledger
Update CONFLICT-03 amendment, Bible 02 and 04 text, the divergence 2.107 INTERIM paragraph, parity entries (COMB-334 and neighbours), in the same change.
