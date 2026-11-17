# Compliance IDs: INFRA-215
"""ScenarioCheckpointer — checkpoint/restore for ScenarioRuntimeService (E31C)."""
from __future__ import annotations

import json
import os
import pickle
import struct
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from src.engine.checkpoint_fields import check_group_counter, fill_missing_fields
from src.engine.checkpoint_schema import check_schema, dump_with_schema, read_header

if TYPE_CHECKING:
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from src.scenarios.schema import SimulationScenarioDefinition


class ScenarioCheckpointer:
    """Save/restore ScenarioRuntimeService state across process restarts.

    File format (binary):
      - 4-byte little-endian uint32: length of JSON header in bytes
      - JSON header bytes (UTF-8): {"tick": N, "spec_id": "...", "rng_checkpoint": ..., "schema": {class: [field names]}}
      - Remainder: pickle blob of AuthoritativeState
    """

    @staticmethod
    def save(svc: "ScenarioRuntimeService", path: "str | Path") -> None:
        """Serialise current kernel state to a checkpoint file at *path*.

        Raises RuntimeError if the kernel has not been started.
        """
        if svc._kernel is None:
            raise RuntimeError(
                "Cannot checkpoint: ScenarioRuntimeService has not been started."
            )
        state = svc._kernel.state
        header = {
            "tick": svc.tick,
            "spec_id": svc._spec.id,
            "rng_checkpoint": state.rng_checkpoint,
        }
        payload, header["schema"] = dump_with_schema(state)
        header_bytes = json.dumps(header).encode("utf-8")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            f.write(struct.pack("<I", len(header_bytes)))
            f.write(header_bytes)
            f.write(payload)

    @staticmethod
    def restore(
        path: "str | Path",
        spec: "SimulationScenarioDefinition",
    ) -> "ScenarioRuntimeService":
        """Restore a ScenarioRuntimeService from a checkpoint file.

        The restored service has its kernel pre-seeded to the checkpoint state.
        Calling .start(tick_limit=N) or .resume(tick_limit=N) continues from
        the checkpoint tick.

        Raises:
            FileNotFoundError: if *path* does not exist.
            ValueError: if the checkpoint spec_id does not match *spec.id*.
            CheckpointSchemaError: (a ValueError) if the header is unreadable, has no schema fingerprint, or names records that differ from the current ones; always before unpickling.
            CheckpointFieldMissingError: (a ValueError) if the checkpoint predates a field that cannot be derived (a group with a contract_id).
        """
        from src.engine.scenario_runtime import ScenarioRuntimeService
        from src.config.profiles import RuntimeProfile, HardwareClass
        from src.platform.rng import DeterministicRNG
        from src.engine.kernel import Kernel

        path = Path(path)
        with path.open("rb") as f:
            header = read_header(f)
            # spec first: a checkpoint of another scenario is refused for that reason, whatever else it lacks
            if header["spec_id"] != spec.id:
                raise ValueError(
                    f"Checkpoint spec_id {header['spec_id']!r} does not match "
                    f"supplied spec id {spec.id!r}."
                )
            check_schema(header.get("schema"))
            state = pickle.loads(f.read())

        fill_missing_fields(state)  # the one post-unpickle step: fill a field the checkpoint predates (only where a ruling derives it) or refuse with a typed error
        check_group_counter(state)  # after the fill: the counter must be above every non-squad stored group id (GroupCounterBehindStoreError)

        # Reconstruct RNG from the checkpoint embedded in state.
        # base_seed=state.seed matches _build_kernel() for a service built with an initial state.
        # set_state() restores only the per-domain stream generators; the stateless draws
        # (get_float, get_int, ...) seed from base_seed, so it must be the run's seed.
        rng = DeterministicRNG(base_seed=state.seed)
        if state.rng_checkpoint is not None:
            rng.set_state(state.rng_checkpoint)

        profile = RuntimeProfile(
            name=spec.id,
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=512,
            max_cpu_percent=100.0,
            max_worker_count=0,
            max_queue_depth=1000,
            max_replay_buffer_kb=64,
            max_observability_budget_percent=5.0,
            max_tick_budget_ms=200.0,
        )
        # Pass run_id explicitly to suppress the Domain.INIT RNG draw in
        # Kernel.__init__ that would otherwise advance the stream by 1 after
        # set_state() restores it, breaking the determinism AC.
        # The id is unique per restore (pid plus a uuid4, which is not the simulation RNG): create_run_directory replaces an existing directory of the
        # same id, so one id per spec made two restores of one spec delete each other's run directory.
        kernel = Kernel(
            profile,
            state,
            rng,
            flags={"no_replay": True},
            run_id=f"restored_{spec.id}_{os.getpid()}_{uuid.uuid4().hex[:8]}",
        )

        svc = ScenarioRuntimeService(spec)
        svc._kernel = kernel
        svc._tick = header["tick"]
        return svc
