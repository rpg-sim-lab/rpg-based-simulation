---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
phase: done
artifact_type: investigation
date: 2026-11-18
tags: []
---

# Investigation: churn fix

Cause: the stored congestion blocker was replaced by every re-inference and removed on first quiet sight, so each timeout (50 ticks) was followed by a fresh blocker without suppression and a new resolve_blocker about every 80 ticks. Failure history was discarded with the blocker (B5), and an early removal made the rebuild immediate.
Ordering fact: capacity_enforcement (phase 42) runs on the update before apply and can list a just-ended record in projects_remove, so the end tick lives on the blocker, not only on the project.
Disclosed gap: a resolve_blocker that completes via typed_completion does not stamp the blocker (moot per designer).
Measured: builds vs main urban s42 429 -> 274, s123 339 -> 207; rebuild gaps follow the 100/200/400/800 backoff (designer recount from raw chunks).
