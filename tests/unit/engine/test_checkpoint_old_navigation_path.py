"""A checkpoint written BEFORE NavigationComponent moved to src/core/navigation_component.py (TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY) names it `src.core.state.NavigationComponent`
in its header fingerprint and in its pickle. It must still pass the schema check and unpickle: src/core/state.py re-exports the class, so both names resolve to the one class."""
import dataclasses
import pickle

import pytest

from src.core.navigation_component import NavigationComponent as MovedNavigationComponent
from src.core.state import NavigationComponent
from src.engine import checkpoint_schema
from src.engine.checkpoint_schema import check_schema, dump_with_schema, read_header
from src.scenarios.schema import SimulationScenarioDefinition
from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401
from tests.unit.engine.checkpoint_helpers import write_checkpoint
from tests.unit.engine.lodging_kernel import REACH, hero, kernel

pytestmark = pytest.mark.usefixtures("remove_restored_run_dirs")

OLD_KEY = "src.core.state.NavigationComponent"
NEW_KEY = "src.core.navigation_component.NavigationComponent"
SPEC = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")


@pytest.fixture(scope="module")
def state():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        yield k._state
    finally:
        k.shutdown()


def test_the_old_name_and_the_new_name_are_the_one_class():
    assert NavigationComponent is MovedNavigationComponent
    assert checkpoint_schema._resolve(OLD_KEY) is NavigationComponent and checkpoint_schema._resolve(NEW_KEY) is NavigationComponent


def _written_under_the_old_name(state, monkeypatch):
    """The payload and fingerprint a build from before the move wrote: the class reported its module as src.core.state."""
    with monkeypatch.context() as m:
        m.setattr(NavigationComponent, "__module__", "src.core.state")
        return dump_with_schema(state)


def test_a_checkpoint_naming_the_old_path_passes_the_schema_check_and_unpickles(state, monkeypatch):
    payload, schema = _written_under_the_old_name(state, monkeypatch)
    assert OLD_KEY in schema and NEW_KEY not in schema  # the old build's fingerprint, not today's
    assert b"src.core.state" in payload and b"src.core.navigation_component" not in payload  # and its pickle names the old module
    check_schema(schema)  # the fingerprint of the old path resolves to the current class: accepted, nothing refused
    restored = pickle.loads(payload)
    assert type(next(iter(restored.entities.values())).navigation) is NavigationComponent


def test_a_checkpoint_naming_the_old_path_restores_through_the_loader_front_half(tmp_path, state, monkeypatch):
    """The header read, the spec check, the fingerprint check and the unpickle that ScenarioCheckpointer.restore runs, on a file whose header and payload name the old path."""
    payload, schema = _written_under_the_old_name(state, monkeypatch)
    path = write_checkpoint(tmp_path / "old.bin", payload, SPEC.id, schema)
    with path.open("rb") as f:
        header = read_header(f)
        assert header["spec_id"] == SPEC.id and OLD_KEY in header["schema"]
        check_schema(header.get("schema"))
        restored = pickle.loads(f.read())
    assert dataclasses.asdict(next(iter(restored.entities.values())).navigation) == dataclasses.asdict(next(iter(state.entities.values())).navigation)
