"""The long executor-equivalence test compares every field by content; its digest and compare helpers are exercised here, fast, so a field the digest cannot see fails in the PR lane.

TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS: ``terrain`` (a dict keyed by (x, y) tuples) could not be JSON-serialised, so it was compared by its error text, the same on
both arms, and never by content.
"""
import dataclasses

from tests.integration.kernel.test_executor_equivalence_long import _digest, _md5, first_mismatch
from tests.unit.kernel.test_executor_context_parity import _state


def _snap(state):
    return {100: ("hash", _digest(state))}


def test_a_tuple_keyed_dict_is_digested_by_content():
    one = _md5({(1, 1): "WALL", (2, 1): "plain"})
    assert one == _md5({(2, 1): "plain", (1, 1): "WALL"}), "order of keys must not matter"
    assert one != _md5({(1, 1): "plain", (2, 1): "plain"}), "a changed value must change the digest"
    unserialisable: list = []
    _md5({(1, 1): "WALL"}, unserialisable, "state.terrain")
    assert unserialisable == []


def test_positive_control_a_changed_terrain_value_is_named():
    a = _state(terrain={(1, 1): "WALL", (2, 2): "plain"})
    b = _state(terrain={(1, 1): "WALL", (2, 2): "swamp"})
    assert first_mismatch(_snap(a), _snap(b)) == (100, "state field terrain")
    assert first_mismatch(_snap(a), _snap(a)) is None


def test_a_field_that_cannot_be_serialised_is_named_not_compared_by_its_error():
    cyclic: dict = {}
    cyclic["self"] = cyclic
    state = dataclasses.replace(_state(), feature_flags=cyclic)
    assert _digest(state)["unserialisable"] == ["state.feature_flags"]
    assert _digest(_state())["unserialisable"] == []


def test_no_field_of_a_compiled_world_state_is_unserialisable():
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    from tests.integration.kernel.test_executor_equivalence_long import WORLDS_DIR
    spec, context = WorldRepository(WORLDS_DIR).load_world_with_context("urban_political")
    state, _ = WorldCompiler.compile(spec, 42, context=context)
    assert _digest(state)["unserialisable"] == []


def test_terrain_is_left_out_only_when_asked_and_is_otherwise_compared():
    """``snapshots`` digests terrain at the first and last sample only (it is static during a run); the digest itself leaves it out only on request."""
    a = _state(terrain={(1, 1): "WALL"})
    b = _state(terrain={(1, 1): "plain"})
    assert _digest(a)["state"]["terrain"] != _digest(b)["state"]["terrain"]
    assert "terrain" not in _digest(a, terrain=False)["state"]
    assert _digest(a, terrain=False) == _digest(b, terrain=False)
