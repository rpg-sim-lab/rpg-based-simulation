---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
artifact_type: plan
---

# Plan — low-hp retreat with nowhere to go, and the panic freeze

1. (a) tactical.py low-hp pure retreat (hp < 15%): with no destination, hold the subject's own tile in RETREAT mode with no task (no PANIC_RETREAT), designer's ruling. No present-threat gate is added: below 15% the WOUNDED term always holds.
2. (c) the emotional panic branch: one computation `_need_path_first` (need_first and hunt_prey) read by the main order and by `_panic_yields_to_need`; the no-destination freeze yields only when the need is pressing, nothing acts on the subject, tactical hostiles are in sight and no prey is in sight.
3. Tests: the low-hp grid with and without a destination, the acceptance scene, the prey row, two live-panic rows, a 16-tick kernel row; the reading-3 below-line row flips to EAT.
4. Docs: divergence 2.200, STRAT-299, Bible 04 section 1, 2.157 and STRAT-297 wording.
5. Measurement: paired crowded 5x5000 and frontier_living_world s43 against the recorder base, with counters; read e30, e31 and e38.
