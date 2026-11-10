---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
artifact_type: investigation
---

# Investigation

- Origin: the hit-wake trace on urban s46 found every DEFEAT (14) to be a flight decided on the tick of the fatal free swing, with hp at or below that swing (owner decision #715 6735931881).
- Free swing (COMB-009) fires in `MovementSystem.resolve_move` for engaged hostiles unless `skip_oa`; an evasive retreat (style 2 in RETREAT mode) skips it; a position swap bypasses it.
- The six `FLIGHT_REASONS` emission sites in `tactical.py` were found by walking `MovementCandidateSelector.FLIGHT_REASONS`; KITING and KEEP_DISTANCE are outside that set and are disclosed in 2.202.
- Side finding: `resolve_attack` is called twice per tick for one hit and only one result reaches hp (urban s46, W id 4, t216); filed as a P2.
- Result: Tier 1 COMBAT relabel in both worlds (DEFEAT falls, COMBAT rises, deaths fall overall); Tier 2 0 FED of 31 subjects (5 RELABEL, 6 OUTLIVE, 2 diverged, 18 DRIFT); subjects that fire mostly die later anyway; the guard cannot reach a subject with no flight decision and an ENTITY_ACT task (Addition 2 rows in `evidence/rows_*.json`).
