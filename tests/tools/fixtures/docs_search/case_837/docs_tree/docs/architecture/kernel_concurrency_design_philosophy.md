---
status: active
layer: architecture
authority: P1
audience: developer
---

101:    groups, corpses, ground items) is `deep_freeze()`'d once in the kernel thread before dispatch
102:    and cached by object identity (`src/engine/executor.py`). Workers never hold a mutable
242: - `src/engine/kernel.py`, `src/engine/executor.py`, `src/engine/worker_manager.py`,
