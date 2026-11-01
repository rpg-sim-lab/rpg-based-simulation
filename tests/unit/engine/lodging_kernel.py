"""A small real-Kernel harness for the lodging tests (F3, divergence 2.155): heroes standing on the reach tiles of one inn, each holding a REST at its bed."""
from dataclasses import replace

from src.config.profiles import HardwareClass, RuntimeProfile
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, BuildingState, RegionState, TaskComponent
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

INN_ID = 20003
INN_AT = (10.0, 10.0)
REACH = ((9.0, 10.0), (10.0, 9.0), (11.0, 10.0), (10.0, 11.0))


def profile():
    return RuntimeProfile(name="lodging", hardware_class=HardwareClass.CLASS_C, max_ram_mb=512, max_cpu_percent=50, max_worker_count=0, max_queue_depth=100,
                          max_replay_buffer_kb=1024, max_observability_budget_percent=5, max_tick_budget_ms=100.0, sampling_interval_ticks=1)


def hero(eid, pos, debt=90.0, gold=50, action="REST", project=True):
    h = (V2EntityBuilder(eid).kind("hero").location(*pos).identity(faction=Faction.HERO_GUILD, properties={"species_id": "human"}).combat(hp=100, max_hp=100, alive=True, readiness=100.0)
         .lifecycle(active=True).build())
    payload = {"action": action, "target_id": INN_ID} if action else {}
    h = replace(h, biological=replace(h.biological, sleep_debt=debt), task=TaskComponent(work_kind="ENTITY_ACT", payload=payload),
                inventory=replace(h.inventory, gold=gold))
    if project:
        objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=str(INN_ID), status=ObjectiveStatus.ACTIVE)
        proj = ProjectState(id="p1", kind=GoalKind.FATIGUE, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
        h = replace(h, strategic=replace(h.strategic, projects={"p1": proj}, current_project_id="p1", current_objective_id="o1"))
    return h


def kernel(entities, beds=2, inn_gold=0, extra_buildings=None):
    region = RegionState(id="r1", name="R", kind="FOREST", bounds=(0, 0, 100, 100), hazard_level=0.0)
    from src.core.state import InventoryComponent
    inn = BuildingState(id=INN_ID, kind="inn", position=INN_AT, functional=True, beds=beds)
    buildings = {INN_ID: inn, **(extra_buildings or {})}
    state = AuthoritativeState(tick=1, seed=1, entities={e.id: e for e in entities}, regions={"r1": region}, buildings=buildings,
                               next_entity_id=max(e.id for e in entities) + 1, next_node_id=1000, terrain={(x, y): "plain" for x in range(30) for y in range(30)})
    return Kernel(profile(), state, DeterministicRNG(1))


def run(k, ticks):
    """Tick the kernel; return the per-tick history of every entity: tick -> {eid: (position, lodged_in, gold, debt, payload action)}."""
    hist = []
    for _ in range(ticks):
        k.tick_once()
        hist.append((k._state.tick, {i: (e.navigation.position, e.navigation.lodged_in, e.inventory.gold, round(e.biological.sleep_debt, 2), (e.task.payload or {}).get("action"))
                                      for i, e in k._state.entities.items()}))
    return hist
