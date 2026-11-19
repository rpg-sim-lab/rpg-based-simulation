---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN
phase: done
date: 2026-11-19
tags: [process-improvement]
---

# Investigation
Token access: gh run list/download of another run's artifact needs actions: read on the workflow token (verified locally with a user token on main run 44323101062; the workflow-token path is read on the first real run, post-merge check on #631). Row identity: finding_key AND state. Selection rule, staleness bound and the open risk are in the ticket (Selection rule) and the rpg_gate_report / rpg_gate_main_report docstrings. Real data: PR run 44366629746 has a genuinely new urban_political O2.population drift, so it reruns 6 pairs, not 1.
