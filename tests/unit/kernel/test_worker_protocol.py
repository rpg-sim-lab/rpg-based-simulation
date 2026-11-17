import dataclasses
import inspect

from src.core.worker_protocol import WorkerPacket
from src.engine import movement


def test_worker_packet_town_center_has_a_real_consumer():
    """WorkerPacket.town_center was removed as dead duplicate state (TCK-20260824-TOWN-CENTER-POINTER-FIX: zero consumers) and is back because a consumer
    reads it through the packet: ``MovementSystem._route_step`` (src/engine/movement.py:112) asks its context for ``town_center`` (the far-town flow-field branch), and the
    ``MOVE`` action runs ``resolve_move`` inside the executor (src/engine/domain/movement_actions.py:27), where the context is the packet. A packet that lacked it answered the default and took a different route than the
    state did (TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS). The test keeps the old intent: the field exists only while that consumer does."""
    field_names = {f.name for f in dataclasses.fields(WorkerPacket)}
    consumer = inspect.getsource(movement.MovementSystem._route_step)
    assert ("town_center" in field_names) == ('"town_center"' in consumer)
