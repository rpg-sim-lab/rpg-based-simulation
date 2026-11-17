"""Worker failures (docs/engine/contracts/bounded_concurrency_contract.md section 4, TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS).

* ``PacketFieldMissingError`` (an undeclared state read on a packet) is NOT a worker failure: it passes through every handler and stops the run.
* Every other worker exception keeps Failure-to-No-Op: a FAILURE result with an empty update. Each of those is counted by wrapping ``failure_no_op``;
  the long executor-equivalence test asserts the count is zero, and the positive controls here prove the counter sees a forced failure on each silent path.
"""
import pytest

import src.engine.worker_manager as wm
from src.core.worker_protocol import PacketFieldMissingError, ResultStatus
from src.engine.worker_manager import WorkerManager, _process_chunk_wrapper
from tests.unit.kernel.test_executor_context_parity import _packet, _state


@pytest.fixture
def noop_count(monkeypatch):
    """Count every FAILURE no-op by wrapping the module-level ``failure_no_op`` that all four handlers call."""
    real, seen = wm.failure_no_op, []

    def counting(packet):
        seen.append(packet.packet_id)
        return real(packet)

    monkeypatch.setattr(wm, "failure_no_op", counting)
    return seen


def _packets(n=3):
    return [_packet(_state(), 1) for _ in range(n)]


def _undeclared_read(packet):
    return getattr(packet, "quest_registry", None)  # a state field the packet does not carry


def _crash(packet):
    raise RuntimeError("boom")


@pytest.mark.parametrize("workers", [0, 1, 2])
def test_an_undeclared_read_stops_the_run_on_every_pool_shape(workers, noop_count):
    manager = WorkerManager(max_workers=workers)
    try:
        with pytest.raises(PacketFieldMissingError):
            manager.execute_batch(_packets(), _undeclared_read)
        with pytest.raises(PacketFieldMissingError):
            manager.execute_batch(_packets(), _undeclared_read, force_local=True)  # the synchronous local path (also the submission-failure rerun)
    finally:
        manager.shutdown()
    assert noop_count == [], "an undeclared read must never become a no-op"


def test_the_process_chunk_wrapper_lets_the_guard_error_through():
    with pytest.raises(PacketFieldMissingError):
        _process_chunk_wrapper(_packets(2), _undeclared_read)


@pytest.mark.parametrize("workers", [0, 2])
def test_any_other_worker_exception_is_a_counted_failure_no_op(workers, noop_count):
    manager = WorkerManager(max_workers=workers)
    try:
        results = manager.execute_batch(_packets(3), _crash)
    finally:
        manager.shutdown()
    assert len(results) == 3 and all(r.status is ResultStatus.FAILURE for r in results)
    assert all(r.update.navigation is None and r.update.combat is None for r in results)
    assert len(noop_count) == 3


def test_positive_control_the_counter_sees_the_silent_process_chunk_path():
    """The ``_process_chunk_wrapper`` handler (the pool of processes) swallows silently; the counter must see it too."""
    seen = []
    real = wm.failure_no_op
    wm.failure_no_op = lambda packet: (seen.append(packet.packet_id), real(packet))[1]
    try:
        out = _process_chunk_wrapper(_packets(2), _crash)
    finally:
        wm.failure_no_op = real
    assert [r.status for r in out] == [ResultStatus.FAILURE, ResultStatus.FAILURE] and len(seen) == 2


def test_positive_control_the_counter_sees_a_whole_chunk_failure(monkeypatch, noop_count):
    """``_collect``: a chunk future that raised as a whole answers every packet with a no-op."""
    manager = WorkerManager(max_workers=2)
    monkeypatch.setattr(manager, "_wrap_work", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("chunk worker died")))
    try:
        results = manager.execute_batch(_packets(4), lambda p: [])
    finally:
        manager.shutdown()
    assert len(results) == 4 and all(r.status is ResultStatus.FAILURE for r in results) and len(noop_count) == 4
