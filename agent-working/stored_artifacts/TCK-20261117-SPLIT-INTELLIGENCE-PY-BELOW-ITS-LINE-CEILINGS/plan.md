---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS
phase: done
date: 2026-11-20
tags: []
---

# Plan
1. Move infer_blockers, generate_crafting_blockers, resolve_blockers from StrategicIntelligenceSystem into the existing blocker_lifecycle.py (Group 1 only); the class keeps one-line static delegates so callers are untouched.
2. Prove the move by AST name+body comparison; one deviation (the cadence default runs in the delegate: systems may not import engine).
3. Re-key the moved baseline rows (mypy, pyrefly, code-health) and lower the intelligence.py module/class ceilings to the measured values; then statics, unit sweep by directory, and a strict hash-equal run on the 3 gate worlds.
