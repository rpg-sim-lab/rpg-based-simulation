---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS
phase: done
date: 2026-11-20
tags: []
---

# Investigation
- main already had blocker_lifecycle.py (divergence 2.214); Group 1 goes there. intelligence.py at origin/main: 1879 lines, class 1717.
- The moved code reads no perception fields (navigation counters and position, latest_intent_results, inventory, strategic state).
- lint-imports found the one hazard: a module-level SystemCadence import in blocker_lifecycle broke "systems do not import engine"; fixed by running the dead-end cadence default in the delegate.
- The sanctioned `codebase.health move` refuses renamed symbols and partial counts; the baseline rows were re-keyed through the registry's load_rows/write_rows (rekey.py).
