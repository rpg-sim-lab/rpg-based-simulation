---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER
artifact_type: test_plan
tags: []
---

# Test plan (written before code; the tests ship with the code)

Real-kernel: a subject with 0 gold standing at an inn with a free bed whose fatigue project points at it is dispatched REST each strategic cadence; after N typed refusals one blocker `blocker_service_REST_<b>` exists, the fatigue goal's utility for that target falls to <= 0.1 x its raw value (the 0.2 floor for hunger and fatigue stated in the assertion), and a different way is chosen when one exists; before N nothing is filed. Same shape for EAT (INSUFFICIENT_GOLD) and SELL.
Negative controls (each must fail on the matching mutant): a delivered service (accepted result or paid transfer) inside the N window files nothing and resets the count; N-1 refusals file nothing; refusals older than the window do not accumulate; NO_BED_FREE, TARGET_LOCKED, GROUP_ROLLBACK, ACTION_EXHAUSTION are not counted; an untyped refusal (diet, keeps_coin) is not counted; a second blocker is not filed for the same (action, building) while one stands (dedup).
Mutants for the review: m1 count every typed reason (NO_BED_FREE must then fire: a control fails); m2 never reset on delivery (the false-fire control fails); m3 no window (the window control fails); m4 filing without the quiet-spell expiry (the expiry control fails).
Typed/round trip: the new refusal record serializes, deserializes and hashes; omitted from the canonical dict while empty; state hash equals main's when no refusal is ever stamped; the replay fingerprint changes only with a filed blocker; the apply fast path and the checkpoint field rule keep the field.
Data path: N, the window, the counted-reason list and the severity are read from blocker_settings.yaml through the existing reader; a missing field or N < 1 is a schema error; the catalog fingerprint changes with the value.
Docs/parity: the Bible ch04 text, the parity row and the divergence entry exist and cite the tests.
Existing tests to run: tests/unit/strategic (blockers, giveups, project end), tests/unit/engine (building_services, service_admission, lodging, actions phase), the content matrix and schema tests (blocker_settings), the parity ledger tests, mypy on touched src (typecheck-py baseline filter), then the paired measurement.
Measurement acceptance (HARD): own-job (ii) false fires = 0, (iii) still-looping = 0, (iv) hash equal to main in any cell with (i) = 0; the v6 urban 2,400 t cell must show the 3 runs gone or each ended by a blocker within about N x 10 ticks.

## Rulings folded in (rpg-designer-k2-fix-plan-rulings.md a73bc655d487395b...) and the tests written
(A) tests/unit/engine/test_no_bed_for_purse.py (5): the predicate (free bed, purse half, one coin short, CLAMP never), a body without the coin trait and a bedless building unchanged, the first-execution REST refused for a broke subject (typed NO_BED_FREE, project WAY_CLOSED), a real-kernel arrival of a broke keeps_coin subject ends WAY_CLOSED with no REST dispatched, a subject with the price still gets the REST and the bed; the existing tests/unit/engine/test_lodging_no_bed_and_arrival.py (finds_no_bed) pass unchanged.
(B) tests/unit/strategic/test_service_refusal_blocker.py (18): data values and no code default, N refusals file the blocker, N-1 / a gap over the window / an uncounted reason / another action file nothing, a lapsed streak is not re-inferred, one blocker per way, the pure streak count, the patch (append, clear only the matching way, cap, clear-then-add), canonical omission and typed round trip, update merge and is_noop, REST stamped with the typed reason and no failure reason, a delivery clears the held refusals, EAT keeps its failure reason and is also counted, the soft suppression (x0.2 floor), the quiet-spell removal at 200 and not before, and three real-kernel tests (N typed refusals file the blocker; N-1 file nothing; a delivered meal clears the streak and files nothing).
Not written: mutants m1-m4 as scratch self-checks (they were listed for the review) and a test that the blocker makes the goal choose ANOTHER way (that is own job B(iii), measured).
