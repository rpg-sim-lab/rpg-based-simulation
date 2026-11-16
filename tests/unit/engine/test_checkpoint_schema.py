"""The schema fingerprint of a scenario checkpoint (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION, INFRA-215, divergence 2.160).

Every refusal is proved to happen BEFORE ``pickle.loads``: the loader is replaced by one that fails the test if called."""
import dataclasses
import io
import json
import pickle
import struct
from types import SimpleNamespace

import pytest

from src.core.group_record import GroupRecord
from src.core.state import AuthoritativeState, BuildingState, NavigationComponent
from src.engine import checkpoint_schema
from src.engine.checkpoint_fields import FIELD_RULES
from src.engine.checkpoint_schema import (
    CheckpointHeaderError,
    CheckpointSchemaError,
    CheckpointSchemaMismatchError,
    CheckpointSchemaMissingError,
    check_schema,
    class_key,
    dump_with_schema,
    read_header,
)
from src.engine.scenario_checkpoint import ScenarioCheckpointer
from src.scenarios.schema import SimulationScenarioDefinition
from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401
from tests.unit.engine.checkpoint_helpers import write_checkpoint
from tests.unit.engine.lodging_kernel import REACH, hero, kernel

pytestmark = pytest.mark.usefixtures("remove_restored_run_dirs")

SPEC = SimulationScenarioDefinition(id="s", world_composition="frontier_living_world", perspective="hero_guild_perspective")
NAV = class_key(NavigationComponent)


@pytest.fixture(scope="module")
def state():
    k = kernel([hero(1, REACH[0], action=None)], beds=1)
    try:
        group = GroupRecord(id=10003, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0), contract_id="r1", contract_holder_id=1)
        yield dataclasses.replace(k._state, groups={10003: group})
    finally:
        k.shutdown()


@pytest.fixture
def no_loads(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("pickle.loads was called")
    monkeypatch.setattr(pickle, "loads", boom)


def _checkpoint(tmp_path, state, edit=None, spec_id="s"):
    payload, schema = dump_with_schema(state)
    schema = {k: list(v) for k, v in schema.items()}
    if edit:
        edit(schema)
    return write_checkpoint(tmp_path / "c.bin", payload, spec_id, schema)


def _raw(tmp_path, header_bytes, declared=None, payload=b"x"):
    path = tmp_path / "raw.bin"
    path.write_bytes(struct.pack("<I", len(header_bytes) if declared is None else declared) + header_bytes + payload)
    return path


def test_headerless_checkpoint_is_refused_before_unpickling(tmp_path, state, no_loads):
    header = json.dumps({"tick": 7, "spec_id": "s", "rng_checkpoint": None}).encode()
    path = _raw(tmp_path, header, payload=pickle.dumps(state))
    with pytest.raises(CheckpointSchemaMissingError, match="no schema fingerprint") as err:
        ScenarioCheckpointer.restore(path, SPEC)
    assert isinstance(err.value, ValueError) and err.value.to_detail()["reason"] == "missing"


def test_spec_id_is_checked_before_the_fingerprint(tmp_path, state, no_loads):
    """A headerless checkpoint of another scenario gets the spec_id error (rpg-designer's order pin), and so does a mismatching fingerprint."""
    header = json.dumps({"tick": 7, "spec_id": "other", "rng_checkpoint": None}).encode()
    with pytest.raises(ValueError, match="spec_id") as err:
        ScenarioCheckpointer.restore(_raw(tmp_path, header), SPEC)
    assert not isinstance(err.value, CheckpointSchemaError)
    bad = _checkpoint(tmp_path, state, lambda s: s[NAV].reverse(), spec_id="other")
    with pytest.raises(ValueError, match="spec_id") as err:
        ScenarioCheckpointer.restore(bad, SPEC)
    assert not isinstance(err.value, CheckpointSchemaError)


def _insert(schema):  # the saved record lacks a middle field the current one has
    del schema[NAV][1]


def _reorder(schema):
    schema[NAV][0], schema[NAV][1] = schema[NAV][1], schema[NAV][0]


def _rename(schema):  # the current record has no field of the saved last name
    schema[NAV][-1] = "an_old_name"


def _removal(schema):  # the saved record has a field the current one no longer has
    schema[NAV].append("a_removed_field")


@pytest.mark.parametrize("edit, change", [(_insert, "inserted"), (_reorder, "reordered"), (_rename, "removed or renamed"), (_removal, "removed or renamed")], ids=["insert", "reorder", "rename", "removal"])
def test_an_insert_reorder_rename_or_removal_is_refused_before_unpickling(tmp_path, state, no_loads, edit, change):
    with pytest.raises(CheckpointSchemaMismatchError, match=change) as err:
        ScenarioCheckpointer.restore(_checkpoint(tmp_path, state, edit), SPEC)
    assert isinstance(err.value, ValueError)
    detail = err.value.to_detail()
    assert detail["reason"] == "mismatch" and [c["class"] for c in detail["classes"]] == [NAV]


def test_an_append_without_a_field_rule_is_refused_through_restore(tmp_path, state, no_loads):
    """The converse of FIELD_RULES: a missing trailing field no row fills is refused, never loaded with an unset slot."""
    covered = {(r.record, r.field) for r in FIELD_RULES}
    schema = dump_with_schema(state)[1]
    victim = next(k for k, v in schema.items() if (k.rsplit(".", 1)[1], v[-1]) not in covered)
    with pytest.raises(CheckpointSchemaMismatchError, match="appended without a fill rule"):
        ScenarioCheckpointer.restore(_checkpoint(tmp_path, state, lambda s: s[victim].pop()), SPEC)


def _record_classes(state):
    from src.core.strategic import ProjectState
    classes = {c.__qualname__: c for k in dump_with_schema(state)[1] if (c := checkpoint_schema._resolve(k))}
    classes["ProjectState"] = ProjectState  # appears in a payload only once an entity holds a project
    return classes


# last_hit_attackers / last_hit_damages were declared BEFORE ``_canonical_cache`` by the group-hit batch (#933). Their FIELD_RULES rows were removed (rpg-designer, this ticket): every
# pre-#933 checkpoint lacks a fingerprint and is refused, and a fingerprinted one lacking the pair is an INSERT, refused here. The field order stays.
PRE_933_PAIR = ("last_hit_attackers", "last_hit_damages")


def test_a_pre_933_shaped_combat_header_is_refused_as_an_insert(tmp_path, state, no_loads):
    from src.core.state import CombatComponent
    names = [f.name for f in dataclasses.fields(CombatComponent)]
    assert all(names.index(n) < names.index("_canonical_cache") for n in PRE_933_PAIR), "the order changed: this test no longer describes the shape"
    combat = class_key(CombatComponent)
    with pytest.raises(CheckpointSchemaMismatchError, match="inserted: last_hit_attackers, last_hit_damages") as err:
        ScenarioCheckpointer.restore(_checkpoint(tmp_path, state, lambda sch: sch[combat].__delitem__(slice(names.index("last_hit_attackers"), names.index("_canonical_cache")))), SPEC)
    assert [c["class"] for c in err.value.classes] == [combat]


@pytest.mark.parametrize("rule", FIELD_RULES, ids=[r.name for r in FIELD_RULES])
def test_an_append_named_in_field_rules_passes_the_check(state, rule):
    """The fill itself is proved through restore() in test_checkpoint_group_fields.py (the old-shape checkpoints with a fingerprint header)."""
    cls = _record_classes(state)[rule.record]
    names = [f.name for f in dataclasses.fields(cls)]
    check_schema({class_key(cls): names[: names.index(rule.field)]}, FIELD_RULES)
    with pytest.raises(CheckpointSchemaMismatchError, match="appended without a fill rule"):
        check_schema({class_key(cls): names[: names.index(rule.field)]}, [])


def test_a_saved_class_that_is_gone_is_refused_and_a_non_src_module_is_never_imported(monkeypatch):
    imported = []
    real = checkpoint_schema.importlib.import_module
    monkeypatch.setattr(checkpoint_schema.importlib, "import_module", lambda name, *a: imported.append(name) or real(name, *a))
    with pytest.raises(CheckpointSchemaMismatchError, match="class removed or renamed") as err:
        check_schema({"src.core.state.NoSuchRecord": ["a"], "os.path.Evil": ["a"], "evil_module.Thing": ["a"]})
    assert len(err.value.classes) == 3
    assert all(name == "src" or name.startswith("src.") for name in imported)


@pytest.mark.parametrize("make", [
    lambda t: _short(t),
    lambda t: _raw(t, b'{"tick": 1', declared=500),
    lambda t: _raw(t, b"\xff\xfe\x00"),
    lambda t: _raw(t, b"{not json"),
    lambda t: _raw(t, b"[1, 2]"),
    lambda t: _raw(t, b'{"spec_id": "s"}'),
    lambda t: _raw(t, b'{"tick": 1}'),
    lambda t: _raw(t, b'{"tick": 1, "spec_id": "s", "schema": {"a.B": "x"}}'),
], ids=["shorter-than-prefix", "length-past-end", "bad-utf8", "bad-json", "not-an-object", "no-tick", "no-spec_id", "schema-malformed"])
def test_an_unreadable_header_is_a_typed_refusal_before_unpickling(tmp_path, no_loads, make):
    with pytest.raises(CheckpointHeaderError) as err:
        ScenarioCheckpointer.restore(make(tmp_path), SPEC)
    assert isinstance(err.value, ValueError) and err.value.to_detail()["reason"] == "header"


def _short(tmp_path):
    path = tmp_path / "short.bin"
    path.write_bytes(b"\x01\x00")
    return path


def test_a_current_checkpoint_round_trips_byte_equal(tmp_path, state):
    svc = SimpleNamespace(_kernel=SimpleNamespace(state=state), tick=3, _spec=SimpleNamespace(id="s"))
    path = tmp_path / "c.bin"
    ScenarioCheckpointer.save(svc, path)
    with path.open("rb") as f:
        header = read_header(f)
        payload = f.read()
    assert payload == pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL)  # the recording pickler changes no byte
    check_schema(header["schema"])
    again_payload, again_schema = dump_with_schema(pickle.loads(payload))
    assert again_payload == payload and again_schema == header["schema"]


def test_the_classes_met_on_load_are_exactly_the_header_classes(state):
    payload, schema = dump_with_schema(state)
    met = set()

    class Spy(pickle.Unpickler):
        def find_class(self, module, name):
            cls = super().find_class(module, name)
            if isinstance(cls, type) and dataclasses.is_dataclass(cls):
                met.add(class_key(cls))
            return cls

    Spy(io.BytesIO(payload)).load()
    assert met == set(schema) and class_key(GroupRecord) in met and class_key(BuildingState) in met


def test_every_field_rule_names_a_record_and_a_real_field_of_it(state):
    classes = _record_classes(state)
    for rule in FIELD_RULES:
        assert rule.record, f"{rule.name}: record unset, so its appended field would be refused"
        assert rule.field in [f.name for f in dataclasses.fields(classes[rule.record])], rule.name
