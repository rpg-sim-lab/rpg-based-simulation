---
status: active
layer: engine
authority: P1
audience: developer
---

65: The only RNG draw physically inside Collection-phase packet construction is
66: `src/engine/executor.py:301` (`packet_seed = rng.get_int(Domain.DEFAULT, state.tick,
67: item.owner_id, 0, 1000000)`), assigned to `WorkerPacket.seed` (`src/core/worker_protocol.py:29`)
66: `src/engine/executor.py:301` (`packet_seed = rng.get_int(Domain.DEFAULT, state.tick,
67: item.owner_id, 0, 1000000)`), assigned to `WorkerPacket.seed` (`src/core/worker_protocol.py:29`)
68: at `executor.py:307`. This value is **dead**: `packet.seed` is never read by `worker_logic.py`,
