"""A slotted dataclass unpickles positionally (a zip of its fields and the saved tuple, no __init__), so a checkpoint written by an older build
only loads right while every field it had is still in the same place. New fields must be appended; a field inserted or reordered mid-class hands
the old value of the next field to the wrong slot, silently. This pins the order of the fields that exist today; later fields are appended after them.

To add a field: append it to the class (after the last one) and append its name to the pinned tuple only if you want it pinned too; the check below
passes for any suffix. A failure here means a field was inserted or moved.
"""
import dataclasses

import pytest

from src.core.group_record import GroupRecord
from src.core.state import AuthoritativeState

GROUP_RECORD_FIELDS = (
    "id", "leader_id", "member_ids", "anchor", "shared_target_id", "contract_id", "cohesion_radius", "last_updated_tick", "roles",
    "str_apt", "int_apt", "agi_apt", "vit_apt", "end_apt", "formation_tick", "escort_target_id", "grievance_log", "reward_pool",
    "last_leadership_check_tick", "dissolution_tick", "composition_score", "_canonical_cache", "contract_holder_id", "dissolution_reason",
    "dissolution_contract_status",
)

AUTHORITATIVE_STATE_FIELDS = (
    "tick", "seed", "world_time", "MAX_PROCESSED_IDS", "MAX_TRACE_SIZE", "entities", "resource_nodes", "ground_items", "corpses", "owed",
    "chests", "buildings", "camps", "regions", "places", "local_scars", "item_instances", "_readonly_cache", "_readonly_entities_cache",
    "_spatial_grid_cache", "_region_list_cache", "_occupancy_map_cache", "occupancy_snapshot", "movement_cache", "route_plans",
    "world_indexes", "semantic_entity_indexes", "_index_hits", "_index_misses", "transient_claims", "_node_map_cache", "_active_nodes_grid",
    "_corpse_map_cache", "_ground_item_map_cache", "_building_map_cache", "_region_index_cache", "_building_region_map_cache",
    "_regions_global_bounds", "_has_hostiles_or_dead_cache", "_has_contracts_cache", "_apply_time_dirty_set", "groups", "terrain",
    "global_resources", "home_storage", "town_center", "movement_count", "maturity", "last_calamity_tick", "grief_drained_tick",
    "blocked_tiles", "town_tiles", "building_tiles", "town_entity_ids", "rng_checkpoint", "transaction_trace", "rejection_registry",
    "pressure_signals", "_opt_profile", "_force_full_scan", "pending_information_responses", "pending_self_model_information_events",
    "information_source_profiles", "feature_flags", "region_loyalty_pressure", "region_culture_states", "entity_legend_facts",
    "entity_belief_institutions", "event_fidelity", "recent_world_events", "quest_registry", "information_providers", "factions", "clans",
    "current_mode", "processed_transaction_ids", "next_node_id", "next_entity_id", "next_item_instance_id", "next_group_id",
)


@pytest.mark.parametrize("cls,pinned", [(GroupRecord, GROUP_RECORD_FIELDS), (AuthoritativeState, AUTHORITATIVE_STATE_FIELDS)])
def test_existing_fields_keep_their_place_and_new_fields_come_last(cls, pinned):
    names = tuple(f.name for f in dataclasses.fields(cls))
    assert names[: len(pinned)] == pinned, f"{cls.__name__}: a field was inserted or moved; append new fields at the end"


def test_the_binding_fields_and_the_group_counter_are_last_today():
    assert tuple(f.name for f in dataclasses.fields(GroupRecord))[-3:] == ("contract_holder_id", "dissolution_reason", "dissolution_contract_status")
    assert dataclasses.fields(AuthoritativeState)[-1].name == "next_group_id"
