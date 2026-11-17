from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.core.enums import EntityRole
from src.core.state import (
    LifeStage,
    EntityState,
    IdentityComponent,
    CombatComponent,
    LifecycleComponent,
    NavigationComponent,
)
from src.core.models.inventory import InventoryComponent, ItemStack
from src.core.builder import V2EntityBuilder
from src.content_semantics.personality import build_personality_for_entity, get_action_style_for_bravery
from src.entities.runtime_contract import ResolvedEntityRuntimeContract
from src.content.common_knowledge_seed import default_self_model
from src.content.species_senses import require_species_sense_profile
from src.systems.lifecycle_systems.genetics import GeneticsSystem


@dataclass(frozen=True)
class EntitySpawnContext:
    """Positional and lifecycle context for spawning a runtime entity."""

    position: tuple[float, float] = (0.0, 0.0)
    spawn_region: Optional[str] = None
    initial_alive: bool = True
    initial_active: bool = True
    current_tick: Optional[int] = None
    name_override: Optional[str] = None
    population_id: Optional[str] = None


def require_archetype_senses(contract: ResolvedEntityRuntimeContract) -> None:
    """PERC-02: an archetype body's senses are derived from its species at every perception check, so a species that is not in content or has no usable sense profile is a
    content error here (``SenseProfileError``), at build, instead of a silent baseline in the gate. The same resolver the gate calls."""
    require_species_sense_profile(contract.species_id, f"archetype {contract.archetype_id!r}")


@dataclass(frozen=True)
class NewbornBirth:
    """The birth event a newborn is built for: its two parents and where, when and under which world seed it is born."""

    mother: EntityState
    mate: EntityState
    position: tuple[float, float]
    tick: int
    seed: int
    home_region_id: Optional[str] = None


class ArchetypeEntityFactory:
    """
    Converts ResolvedEntityRuntimeContract + EntitySpawnContext into EntityState.

    This is the archetype-native construction path. Profile IDs that are not
    yet wired to active runtime behavior are preserved in identity.properties
    rather than silently dropped.
    """

    def build_entity(
        self,
        entity_id: int,
        contract: ResolvedEntityRuntimeContract,
        spawn: EntitySpawnContext,
        seed: int = 42,
    ) -> EntityState:
        # Metadata carried into properties for traceability
        properties: dict = {
            "archetype_id": contract.archetype_id,
            "faction_id": contract.faction_id,
            "role_id": contract.role_id,
        }
        if contract.profession_id is not None:
            properties["profession_id"] = contract.profession_id
        if contract.cognition_profile_id is not None:
            properties["cognition_profile_id"] = contract.cognition_profile_id
        if contract.drive_profile_id is not None:
            properties["drive_profile_id"] = contract.drive_profile_id
        if contract.need_profile_id is not None:
            properties["need_profile_id"] = contract.need_profile_id
        require_archetype_senses(contract)
        if contract.skill_profile_id is not None:
            properties["skill_profile_id"] = contract.skill_profile_id
        if spawn.spawn_region is not None:
            properties["spawn_region"] = spawn.spawn_region
        if spawn.name_override is not None:
            properties["name"] = spawn.name_override
        if spawn.current_tick is not None:
            properties["spawn_tick"] = spawn.current_tick
        if spawn.population_id is not None:
            properties["population_id"] = spawn.population_id

        # Legacy projection — use contract values if provided, else default (0)
        legacy_role_int = int(contract.legacy_role) if contract.legacy_role is not None else 0
        legacy_faction_int = int(contract.legacy_faction) if contract.legacy_faction is not None else 0

        # Build inventory items
        items = [
            ItemStack(item_id=item_id, quantity=qty)
            for item_id, qty in sorted(contract.inventory_items.items())
        ]

        # Real, per-entity, species/faction-correlated personality -- this path previously left
        # every entity at PersonalityComponent()'s own all-zero default, the same class of bug
        # already fixed once for WorldCompiler.compile()'s own path (TCK-20260619-P0-ENTITY-INIT)
        # (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY). Uses the exact same
        # DeterministicRNG/Domain.WORLD/sub_id convention as WorldCompiler.compile()'s own
        # personality seeding, and the same shared bravery-bias/ActionStyle helpers
        # (src/content_semantics/personality.py) this session's sibling combat tickets added.
        personality = build_personality_for_entity(entity_id, contract.faction_id, seed)

        builder = (
            V2EntityBuilder(entity_id)
            .kind(contract.kind)
            .location(*spawn.position)
            .identity(
                role=legacy_role_int,
                faction=legacy_faction_int,
                traits=set(contract.traits),
                properties=properties,
                personality=personality,
                occupation=contract.role_id or contract.profession_id,
            )
            .combat(
                hp=contract.hp,
                max_hp=contract.max_hp,
                atk=contract.atk,
                def_stat=contract.def_stat,
                attack_range=contract.attack_range,
                readiness=contract.readiness,
                alive=spawn.initial_alive,
                action_style=get_action_style_for_bravery(personality.bravery),
            )
            .spawn_combat_stats_are_final().replace_self_model(default_self_model())
        )

        entity = builder.build()

        # Replace inventory with populated items and gold
        if items or contract.starting_gold > 0:
            from dataclasses import replace
            inv = InventoryComponent(
                items=items,
                gold=int(contract.starting_gold),
            )
            entity = _replace_inventory(entity, inv)

        # Apply lifecycle active flag
        if not spawn.initial_active:
            entity = _replace_lifecycle(entity, active=False)

        return entity

    def build_newborn(
        self,
        entity_id: int,
        contract: ResolvedEntityRuntimeContract,
        species_traits: tuple[str, ...],
        birth: NewbornBirth,
    ) -> EntityState:
        """A newborn of `birth.mother` and `birth.mate`: the BODY of the species' newborn archetype (stats, body model,
        personality draw keyed by (world seed, newborn id)) at life stage CHILD, and nothing of its job. Role, occupation,
        equipment, inventory and job traits are not taken from the archetype: the role follows the mother (MONSTER stays
        MONSTER, anything else CITIZEN), gold is 0 and traits are the species' own declared traits (M1 births, rulings v2.2 D3).
        population_id and spawn_region are the mother's (omitted when she has none): on a newborn, spawn_region names its
        population's declared region, not where it was born, and in campaign mode a surviving newborn can receive its
        population's pending information in a later episode when no earlier roster member survives (G1 addendum A1)."""
        mother, mate = birth.mother, birth.mate
        properties = _newborn_properties(contract, mother)
        personality = build_personality_for_entity(entity_id, properties.get("faction_id"), birth.seed)
        # birth_record() combines genetics only when a parent profile is supplied; first-generation parents carry none.
        a_profile = mother.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(mother.id)
        b_profile = mate.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(mate.id)
        role = EntityRole.MONSTER if mother.identity.role == EntityRole.MONSTER else EntityRole.CITIZEN

        return (
            V2EntityBuilder(entity_id)
            .kind(contract.kind)
            .location(*birth.position)
            .identity(
                role=role, faction=mother.identity.faction, traits=set(species_traits), properties=properties,
                personality=personality, life_stage=LifeStage.CHILD, occupation=None,
            )
            .navigation(home_position=mother.navigation.home_position, leash_radius=mother.navigation.leash_radius)
            .strategic(home_region_id=birth.home_region_id)
            .combat(
                hp=contract.hp, max_hp=contract.max_hp, atk=contract.atk, def_stat=contract.def_stat,
                attack_range=contract.attack_range, readiness=contract.readiness,
                action_style=get_action_style_for_bravery(personality.bravery),
            )
            .birth_record(
                parent_a_entity_id=mother.id, parent_b_entity_id=mate.id, birth_tick=birth.tick,
                parent_a_genetic_profile=a_profile, parent_b_genetic_profile=b_profile,
                parent_a_role=mother.identity.role, parent_b_role=mate.identity.role,
                parent_a_public_reputation=mother.social.public_reputation,
                parent_b_public_reputation=mate.social.public_reputation,
            )
            .spawn_combat_stats_are_final()
            .replace_self_model(default_self_model())
            .build()
        )


def _newborn_properties(contract: ResolvedEntityRuntimeContract, mother: EntityState) -> dict:
    """Species, the mother's faction and population keys (a key is omitted when she has none, never written as None) and the body's profile ids; no job ids."""
    properties: dict = {"species_id": contract.species_id}
    for key in ("faction_id", "population_id", "spawn_region"):
        inherited = mother.identity.properties.get(key)
        if inherited is not None:
            properties[key] = inherited
    for key, value in (
        ("need_profile_id", contract.need_profile_id),
        ("sense_profile_id", contract.sense_profile_id),
        ("cognition_profile_id", contract.cognition_profile_id),
        ("drive_profile_id", contract.drive_profile_id),
    ):
        if value is not None:
            properties[key] = value
    return properties


def _replace_inventory(entity: EntityState, inv: InventoryComponent) -> EntityState:
    """Return a new EntityState with inventory replaced."""
    return EntityState(
        id=entity.id,
        kind=entity.kind,
        interaction=entity.interaction,
        identity=entity.identity,
        attributes=entity.attributes,
        inventory=inv,
        strategic=entity.strategic,
        social=entity.social,
        biological=entity.biological,
        lifecycle=entity.lifecycle,
        aptitude=entity.aptitude,
        combat=entity.combat,
        equipment=entity.equipment,
        navigation=entity.navigation,
        task=entity.task,
        stamina=entity.stamina,
        self_model=entity.self_model,
        cognition=entity.cognition,
    )


def _replace_lifecycle(entity: EntityState, *, active: bool) -> EntityState:
    """Return a new EntityState with lifecycle.active replaced."""
    from dataclasses import replace as dc_replace
    lc = dc_replace(entity.lifecycle, active=active)
    return EntityState(
        id=entity.id,
        kind=entity.kind,
        interaction=entity.interaction,
        identity=entity.identity,
        attributes=entity.attributes,
        inventory=entity.inventory,
        strategic=entity.strategic,
        social=entity.social,
        biological=entity.biological,
        lifecycle=lc,
        aptitude=entity.aptitude,
        combat=entity.combat,
        equipment=entity.equipment,
        navigation=entity.navigation,
        task=entity.task,
        stamina=entity.stamina,
        self_model=entity.self_model,
        cognition=entity.cognition,
    )
