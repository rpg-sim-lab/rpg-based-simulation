# Compliance IDs: WORLD-122
"""The risen origin (M1): a corpse becomes a new subject (rows R1-R4), its goods leave exactly, a loot or meal on the rise tick wins, and the content refuses what cannot rise."""
import dataclasses
import os
import shutil
import tempfile
from types import SimpleNamespace

import pytest
import yaml

from src.content.repository import CatalogRepository, RisenProfileError
from src.core.builder import V2EntityBuilder
from src.core.models.inventory import ItemStack
from src.core.models.world_records import CorpseState
from src.core.spawn_source import SpawnKind, SpawnSource
from src.core.state import AuthoritativeState
from src.core.updates import StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.engine.pipeline_phases.resources import ResourceTransactionPhase
from src.engine.world_dynamics import _meat_decayed_events
from src.observability.run_ledger import RunLedger
from src.world import risen
from src.world.corpse_goods import corpse_remains
from src.world.risen import RisenService, rise_triggers_phase

TICK = 60
GOODS = [ItemStack(item_id="raw_meat", quantity=3), ItemStack(item_id="iron_sword", quantity=1), ItemStack(item_id="potion", quantity=2)]


class _Catalog:
    """The warmed catalog with the rise chance forced, so a test does not depend on a draw."""

    def __init__(self, real, chance):
        self._real, self._chance = real, chance

    def get_risen_profile(self, profile_id):
        return self._real.get_risen_profile(profile_id).model_copy(update={"rise_chance_per_check": self._chance})

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture
def certain(monkeypatch):
    real = risen.get_catalog()
    monkeypatch.setattr(risen, "get_catalog", lambda: _Catalog(real, 1.0))


@pytest.fixture
def never(monkeypatch):
    real = risen.get_catalog()
    monkeypatch.setattr(risen, "get_catalog", lambda: _Catalog(real, 0.0))


def _dead(entity_id=1, kind="human"):
    return V2EntityBuilder(entity_id).kind(kind).location(5.0, 5.0).combat(alive=False).build()


def _corpse(entity_id=1, decay_tick=TICK + 300, gold=7, items=None):
    return CorpseState(id=1000000 + entity_id, original_entity_id=entity_id, position=(5.0, 5.0), items=list(GOODS if items is None else items), decay_tick=decay_tick, gold=gold)


def _state(*, tick=TICK, corpses=None, entities=None):
    corpses = corpses if corpses is not None else [_corpse()]
    entities = entities or [_dead()]
    return AuthoritativeState(tick=tick, seed=42, entities={e.id: e for e in entities}, corpses={c.id: c for c in corpses}, next_entity_id=max(e.id for e in entities) + 1)


def _rise(state, update=None):
    return RisenService.process_rises(state, update or StateUpdate(), SystemCadence())


def test_r1_a_rising_consumes_its_corpse_once_and_names_it_as_the_source(certain):
    state = _state()
    update = _rise(state)
    (body,) = update.entities_add
    assert update.corpses_remove == [1000001]
    source = update.entity_spawn_sources[body.id]
    assert source == SpawnSource(SpawnKind.RISEN, source_corpse_id=1000001, original_entity_id=1)
    assert source.source_corpse_id in state.corpses
    after = ApplyPath.apply_generation(state, update, TICK + 1, TICK + 1)
    assert 1000001 not in after.corpses and body.id in after.entities
    assert not _rise(after).entities_add, "nothing is left to rise a second time"


def test_r2_the_goods_leave_exactly_coin_to_a_purse_meat_to_the_sink_every_other_stack_to_the_ground(certain):
    state = _state()
    update = _rise(state)
    purse = [g for g in update.ground_items_add_or_update if g.gold]
    items = {g.item_id: g.quantity for g in update.ground_items_add_or_update if not g.gold}
    assert [(g.id, g.gold, g.source_entity_id, g.position) for g in purse] == [(1000001, 7, 1, (5.0, 5.0))]
    assert items == {"iron_sword": 1, "potion": 2}
    meat = [e for e in update.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]
    assert [(e.subject, e.payload) for e in meat] == [("1000001", {"quantity": 3.0, "cause": "risen"})]
    assert all(g.source_entity_id == 1 and g.dropped_tick == TICK + 1 for g in update.ground_items_add_or_update)
    ids = [g.id for g in update.ground_items_add_or_update]
    assert len(ids) == len(set(ids)) and update.next_item_instance_id_set == state.next_item_instance_id + 2
    after = ApplyPath.apply_generation(state, update, TICK + 1, TICK + 1)
    assert sorted((g.item_id, g.quantity, g.gold) for g in after.ground_items.values()) == [("", 0, 7), ("iron_sword", 1, 0), ("potion", 2, 0)]


def test_the_remains_helper_is_pure_and_loses_nothing():
    corpse = _corpse()
    before = dataclasses.replace(corpse)
    remains = corpse_remains(corpse, TICK, 50)
    assert corpse == before
    assert remains.meat_left == 3.0 and remains.purse.gold == 7
    assert sorted((g.item_id, g.quantity) for g in remains.ground_items) == [("iron_sword", 1), ("potion", 2)]
    assert remains.next_item_id == 52 and corpse_remains(_corpse(gold=0, items=[]), TICK, 50).purse is None


def test_r3_the_kind_declares_a_risen_profile_and_the_dead_species_is_a_source(certain):
    body = _rise(_state()).entities_add[0]
    assert body.kind == "undead"
    assert not _rise(_state(entities=[_dead(kind="wolf")])).entities_add, "a wolf is not a source species of undead_rising"


def test_r4_the_risen_body_is_a_new_subject_and_nothing_of_the_dead_passes_on(certain):
    state = _state()
    update = _rise(state)
    (body,) = update.entities_add
    assert body.id != 1 and 1 not in update.entity_updates and state.entities[1].combat.alive is False
    assert body.identity.occupation is None and body.lifecycle.parent_a_entity_id is None and body.lifecycle.parent_b_entity_id is None
    assert body.identity.life_stage.name == "ADULT" and body.lifecycle.birth_tick == TICK
    assert body.identity.properties["faction_id"] == "undead_remnants" and body.inventory.gold == 0 and body.combat.alive


@pytest.mark.parametrize("decay_tick, rises", [(TICK + 2, True), (TICK + 1, False), (TICK, False)])
def test_a_corpse_rises_only_while_tick_plus_one_is_before_its_decay_tick(certain, decay_tick, rises):
    assert bool(_rise(_state(corpses=[_corpse(decay_tick=decay_tick)])).entities_add) is rises


def test_chance_zero_and_an_off_beat_tick_change_nothing(never):
    update = StateUpdate()
    assert _rise(_state(), update) is update
    assert RisenService.process_rises(_state(tick=TICK + 1), update, SystemCadence()) is update


def test_a_corpse_looted_on_its_rise_tick_gives_the_loot_and_no_body_purse_or_ground_items(certain):
    state = _state()
    looted = StateUpdate(corpses_remove=[1000001])
    update = _rise(state, looted)
    assert not update.entities_add and not update.ground_items_add_or_update and update.corpses_remove == [1000001]
    assert not [e for e in update.world_events_add if e.category == WorldEventCategory.MEAT_DECAYED]


def test_a_meal_shrunk_corpse_stays_a_corpse_and_does_not_rise_that_tick_but_may_at_a_later_check(certain):
    state = _state()
    smaller = dataclasses.replace(state.corpses[1000001], items=[ItemStack(item_id="raw_meat", quantity=1)])
    update = _rise(state, StateUpdate(corpses_add_or_update=[smaller]))
    assert not update.entities_add and not update.corpses_remove
    later = _state(tick=TICK + 30, corpses=[smaller])
    assert _rise(later).entities_add


def test_a_birth_and_a_rise_on_one_tick_get_distinct_ids_and_distinct_tiles(certain):
    state = _state()
    newborn = V2EntityBuilder(2).kind("human").location(5.0, 5.0).build()
    births = StateUpdate(entities_add=[newborn])
    update = _rise(state, births)
    risen_body = update.entities_add[-1]
    assert risen_body.id > newborn.id and len({e.id for e in update.entities_add}) == 2
    assert (int(risen_body.navigation.position[0]), int(risen_body.navigation.position[1])) != (5, 5), "the rise did not stack on the newborn's tile"
    after = ApplyPath.apply_generation(state, update, TICK + 1, TICK + 1)
    assert after.next_entity_id > risen_body.id


def test_the_phase_runs_the_rise_after_the_transfers_resolved(certain):
    state = _state()
    out = ResourceTransactionPhase.resolve(state, StateUpdate(), SystemCadence())
    assert len(out.entities_add) == 1


def test_a_rise_check_with_a_corpse_triggers_the_phase_and_nothing_else_does():
    cadence = SystemCadence()
    assert rise_triggers_phase("resource_transactions", _state(), cadence)
    assert not rise_triggers_phase("resource_transactions", _state(tick=TICK + 1), cadence)
    assert not rise_triggers_phase("resource_transactions", _state(corpses=[]), cadence) if False else not rise_triggers_phase("resource_transactions", AuthoritativeState(tick=TICK, seed=1), cadence)
    assert not rise_triggers_phase("world_dynamics", _state(), cadence)


def test_no_world_dynamics_code_path_calls_corpse_remains():
    for path in ("src/engine/world_dynamics.py", "src/engine/economy.py"):
        assert "corpse_remains" not in open(path).read(), path


def test_the_meat_cause_is_decay_from_decay_and_the_ledger_total_is_unchanged_by_the_cause():
    state = _state(tick=299, corpses=[_corpse(decay_tick=300)])
    (event,) = _meat_decayed_events(state)
    assert event.payload == {"quantity": 3.0, "cause": "decay"}
    RunLedger.reset_run_state()
    RunLedger.configure(True)
    decay = SimpleNamespace(category=SimpleNamespace(name="MEAT_DECAYED"), payload={"quantity": 3.0, "cause": "decay"})
    rose = SimpleNamespace(category=SimpleNamespace(name="MEAT_DECAYED"), payload={"quantity": 3.0, "cause": "risen"})
    RunLedger._count_world_events(SimpleNamespace(world_events_add=[decay, rose]))
    assert RunLedger._world_events == {"MEAT_DECAYED": 2, "meat_decayed_quantity": 6.0}
    RunLedger.reset_run_state()


def test_a_risen_spawn_source_must_name_its_corpse_and_the_body_it_was_and_no_other_kind_may():
    with pytest.raises(ValueError, match="RISEN"):
        SpawnSource(SpawnKind.RISEN, source_corpse_id=3)
    with pytest.raises(ValueError, match="RISEN"):
        SpawnSource(SpawnKind.RISEN, original_entity_id=3)
    with pytest.raises(ValueError, match="only a RISEN"):
        SpawnSource(SpawnKind.BIRTH, parent_ids=(1,), source_corpse_id=3, original_entity_id=1)


def _repo(species_edit=None, profile_edit=None, need_hunger=None, repro_on_undead=False):
    tmp = tempfile.mkdtemp()
    shutil.copytree("data/content", os.path.join(tmp, "c"))
    root = os.path.join(tmp, "c", "living")
    species = yaml.safe_load(open(os.path.join(root, "species.yaml")))
    profiles = yaml.safe_load(open(os.path.join(root, "risen_profiles.yaml")))
    needs = yaml.safe_load(open(os.path.join(root, "need_profiles.yaml")))
    undead = next(s for s in species if s["id"] == "undead")
    undead.update(species_edit or {})
    profiles[0].update(profile_edit or {})
    if need_hunger:
        next(n for n in needs if n["id"] == undead["need_profile"])["needs"]["hunger"] = need_hunger
    for name, data in (("species", species), ("risen_profiles", profiles), ("need_profiles", needs)):
        yaml.safe_dump(data, open(os.path.join(root, f"{name}.yaml"), "w"))
    return CatalogRepository(os.path.join(tmp, "c"))


@pytest.mark.parametrize("kwargs, message", [
    ({"profile_edit": {"source_species": ["no_such_species"]}}, "source species"),
    ({"profile_edit": {"risen_archetype": "no_such_archetype"}}, "not declared"),
    ({"profile_edit": {"risen_archetype": "hungry_wolf"}}, "belongs to species"),
    ({"need_hunger": "high"}, "do not eat"),
    ({"species_edit": {"risen_profile": "no_such_profile"}}, "not declared"),
])
def test_the_content_refuses_a_risen_profile_that_cannot_hold(kwargs, message):
    with pytest.raises(RisenProfileError, match=message):
        _repo(**kwargs).load_all()


def test_the_shipped_content_declares_undead_rising_from_people_shaped_corpses():
    repo = CatalogRepository()
    repo.load_all()
    profile = repo.get_risen_profile(repo.species["undead"].risen_profile)
    assert profile.risen_archetype == "undead_sentinel" and "human" in profile.source_species and "wolf" not in profile.source_species
    assert SystemCadence().rises == 30


def test_the_content_refuses_a_species_that_declares_both_origins():
    from src.content.repository import check_risen_profiles
    repo = CatalogRepository()
    repo.load_all()
    repo.species["undead"] = repo.species["undead"].model_copy(update={"reproduction_profile": "humanoid_births"})
    with pytest.raises(RisenProfileError, match="both"):
        check_risen_profiles(repo)


def test_running_the_transaction_phase_with_nothing_pending_changes_nothing_so_the_rise_trigger_alone_moves_no_state(never):
    from src.engine.economy import ResourceTransactionSystem
    state, update = _state(), StateUpdate()
    assert ResourceTransactionSystem.resolve_all(state, update) == update
    assert ResourceTransactionPhase.resolve(state, update, SystemCadence()) is not None
    assert ResourceTransactionPhase.resolve(state, update, SystemCadence()) == update, "chance 0: the whole phase is a no-op on an idle tick"
