"""The per-survivor rebuild of a campaign episode's initial state.

Each carry-forward record that is alive becomes a body again: the species is checked for a usable sense profile (PERC-02a), the identity, personality, equipment, combat and
navigation fields are rebuilt, and the body is placed on a legal tile. The step was moved out of ``CampaignOrchestrator._build_initial_state`` unchanged."""
from __future__ import annotations

from dataclasses import replace as dc_replace
from typing import Any, Dict

from src.core.models.inventory import EquipSlot
from src.core.species import SpeciesNotDeclaredError
from src.core.state import EntityState, PersonalityComponent
from src.core.updates import SocialUpdate
from src.domains.campaigns.survivor_placement import resolve_survivor_position
from src.engine.rpg_depth import SkillScalingService
from src.entities.checked_builder import species_builder
from src.systems.social_systems.relationships import RelationshipService


def _base_body(eid: int, cf: Any) -> EntityState:
    """The body a carry-forward record rebuilds into: species checked, identity, personality, progression and attributes from the record."""
    # M1 step 4: an empty carried kind is a record serialized before the field existed. There is no species to rebuild it with,
    # so it is refused (it used to become the literal "entity").
    if not cf.kind:
        raise SpeciesNotDeclaredError(f"carry-forward record of entity {eid} has an empty kind (a pre-field record); it cannot be rebuilt")
    #
    # Identity fields (role/faction/properties/traits/personality/evolution_level/
    # evolution_points) are built via V2EntityBuilder's own identity-construction method
    # below, NOT a raw dataclass replacement call on the identity component directly --
    # tests/architecture/test_role_set_identity_patch_only_guard.py and
    # test_faction_mutation_write_paths.py statically enforce that role and faction may
    # only be mutated through the authoritative IdentityPatch's own apply step (live
    # tick-time mutation) OR V2EntityBuilder's own initial-construction seeding (pre-tick,
    # not a live mutation) -- the same allowlisted exemption ArchetypeEntityFactory's own
    # build_entity() already relies on for a real spawn. This IS initial-episode
    # construction, so the builder path is the correct one, not a bypass of the same rule
    # real spawns already follow.
    base = (
        species_builder(eid, cf.kind, f"campaign episode body {eid}")
        .identity(
            role=cf.role,
            faction=cf.faction,
            evolution_level=cf.level,
            evolution_points=cf.xp,
            properties=dict(cf.properties),
            traits=set(cf.traits),
            personality=PersonalityComponent(
                greed=cf.personality.get("greed", 0.0),
                bravery=cf.personality.get("bravery", 0.0),
                sociability=cf.personality.get("sociability", 0.0),
                industry=cf.personality.get("industry", 0.0),
            ),
            # Earned progression, unconditional -- same reasoning as role/faction/
            # traits/personality above (TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-
            # PROGRESSION-NOT-CARRIED-FORWARD). Empty/default cf values (pre-existing
            # carry-forward records) fall back to V2EntityBuilder's own component
            # defaults, matching the precedent this whole block already established.
            unspent_ap=cf.unspent_ap,
            learned_skills=set(cf.learned_skills),
            active_breakthroughs=set(cf.active_breakthroughs),
            class_id=cf.class_id,
            veterancy_points=cf.veterancy_points,
            veterancy_rank=cf.veterancy_rank,
            known_recipes=set(cf.known_recipes),
            occupation=cf.occupation,
        )
        .attributes(
            strength=cf.attributes.get("strength"),
            agility=cf.attributes.get("agility"),
            vitality=cf.attributes.get("vitality"),
            endurance=cf.attributes.get("endurance"),
            intelligence=cf.attributes.get("intelligence"),
            spirit=cf.attributes.get("spirit"),
            wisdom=cf.attributes.get("wisdom"),
            perception=cf.attributes.get("perception"),
            charisma=cf.attributes.get("charisma"),
        )
        .build()
    )
    return base


def _carried_equipment(base: EntityState, cf: Any) -> Any:
    """The body's equipment with the carried slots and durability."""
    # Apply carried equipment (convert string keys back to EquipSlot enum).
    raw_slots = cf.equipment.get("slots", {})
    raw_dur = cf.equipment.get("durability", {})
    slots_enum = {
        EquipSlot[k]: v
        for k, v in raw_slots.items()
        if k in EquipSlot.__members__
    }
    durability_enum = {
        EquipSlot[k]: v
        for k, v in raw_dur.items()
        if k in EquipSlot.__members__
    }
    equipment = dc_replace(
        base.equipment,
        slots=slots_enum,
        durability=durability_enum,
    )
    return equipment


def _recomputed_combat(base: EntityState, equipment: Any) -> Any:
    """The combat component recomputed from the carried attributes, equipment, skills, class and breakthroughs."""
    # TCK-20260911-CAMPAIGN-SURVIVOR-EARNED-PROGRESSION-NOT-CARRIED-FORWARD: recompute
    # combat stats from the survivor's real carried attributes/equipment/skills/class/
    # breakthroughs, the same function the live tick-time stats_dirty path uses
    # (src/engine/apply.py) -- reconstruction has no prior-tick state to diff against, so
    # that path never fires here on its own. wounds/scars stay at V2EntityBuilder's own
    # fresh defaults (survivors are narratively recovered between episodes -- a deliberate
    # divergence, not carried), so hp is set to the newly-derived max_hp (full health),
    # not the bare CombatComponent default.
    derived_stats = SkillScalingService.get_effective_stats(
        base.attributes,
        equipment,
        wounds=base.combat.wounds,
        scars=base.combat.scars,
        learned_skills=base.identity.learned_skills,
        traits=base.identity.traits,
        current_role=base.combat.tactical_role,
        active_breakthroughs=base.identity.active_breakthroughs,
        class_id=base.identity.class_id,
    )
    combat = dc_replace(
        base.combat,
        max_hp=derived_stats["max_hp"],
        hp=derived_stats["max_hp"],
        atk=derived_stats["atk"],
        def_stat=derived_stats["def_stat"],
        evasion=derived_stats["evasion"],
        readiness_speed=derived_stats.get("readiness_speed", base.combat.readiness_speed),
        move_cost=derived_stats.get("move_cost", base.combat.move_cost),
        range=derived_stats.get("range", base.combat.range),
        tactical_role=derived_stats.get("tactical_role", base.combat.tactical_role),
    )
    return combat


def rebuild_survivors(
    alive_carry_forwards: Dict[int, Any],
    compiled_regions: Any,
    world_spec: Any,
    entities: Dict[int, EntityState],
    reconstruction_ctx: Any,
) -> None:
    """Rebuild every alive carry-forward as a body in `entities` (mutated in place, as each survivor is placed)."""
    for eid, cf in alive_carry_forwards.items():
        base = _base_body(eid, cf)
        equipment = _carried_equipment(base, cf)
        combat = _recomputed_combat(base, equipment)

        # Apply carried reputation.
        social = RelationshipService.process_update(
            base.social, SocialUpdate(reputation_set=cf.reputation)
        )

        # Resolve a real position BEFORE inserting into `entities` -- resolve_survivor_
        # position()'s own occupancy check reads reconstruction_ctx.entities (the same dict
        # this loop is building), so only already-placed survivors are visible when this
        # one is resolved, never later/unresolved ones sitting at a shared default.
        resolved_pos = resolve_survivor_position(
            eid,
            cf.last_position,
            reconstruction_ctx,
            world_spec.topology.width,
            world_spec.topology.height,
            compiled_regions,
        )
        navigation = dc_replace(base.navigation, position=resolved_pos)

        entities[eid] = dc_replace(
            base,
            equipment=equipment,
            social=social,
            navigation=navigation,
            combat=combat,
        )
