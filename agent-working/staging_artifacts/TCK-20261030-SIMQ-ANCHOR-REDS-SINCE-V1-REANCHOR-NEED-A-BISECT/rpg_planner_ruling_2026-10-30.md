---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
artifact_type: plan
date: 2026-10-30
tags: [simulation-quality, regression]
---

# rpg-planner ruling on the bisect result (2026-10-30)

Relayed via lead-planner-u24 and lead-planner to rpg-planner-ubuntu. The ruling is on the bisect result at rpg-ubuntu-simq-anchor-bisect-impl 5b1c1dd55: the first mover is d914bace7 (#769); urban_political_selfmodel_probe_seed42_200t WORLD 0.32 -> 0.25 (hazard_drain_applied 17 -> 12, region_trauma_delta 3 -> 2). The text below is word for word as relayed.

rpg-planner (u24)'s ruling on the bisect, relayed via lead-planner-u24 and lead-planner ("A clean bisect; thanks"):
Q1: YES, re-anchor rather than fix. #769 (div 2.139) is intended, and the WORLD drop is its direct effect. The re-anchor PR must cite d914bace7 / #769 / 2.139 and the bisect table, re-anchor that key, and remove the known-red entry. rpg-planner is sending rpg-designer an fyi.
Q2: YES to the sweep, sized as MEASUREMENT:
- Run the anchored corpus at a25619971 vs d914bace7, with the bisect's settings.
- List EVERY anchored key #769 moved, inside and outside tolerance.
- Re-anchor ONLY the out-of-tolerance keys, in the same PR with the same citation. Report the within-tolerance moves without touching them.
- If a key moved that #769's mechanism doesn't explain, STOP to rpg-planner.
rpg-designer's addition: before any re-anchor, ATTRIBUTE each of the 5 vanished hazard_drain_applied events (17→12) with the entity and the reason: (a) it retreated earlier under #769, or (b) it died earlier or never fought in that hazard region. If any vanished drain belongs to a NON-retreating entity, STOP to rpg-planner, and rule out a flight path crossing a hazard.
(iii) The re-measure at close still applies.
Process: rpg-planner is adding "behaviour-changing rpg tickets re-check SimQ anchors at close" to its review checklist.
Reviewer for the re-anchor PR: still pending the u24 owner's answer on lead-planner-u24.
Slot: the corpus sweep is a heavy run. Ask me for it after B's runs finish, pinned 4-5 under the same memory floor and before the perf window. If it won't fit today, it goes after perf.
