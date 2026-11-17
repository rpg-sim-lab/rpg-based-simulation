"""TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, commit 1: the general typed project end.

`end_record` is the one writer of ``ended_by``: it sets the terminal status and the typed end together, once. ``supersede_record`` is a thin call of it and returns what it always did.
Nothing writes THREAT_CLEARED yet, so no run's state hash moves; the value serializes, hashes and exports like SUPERSEDED_BY_TARGET.
"""
from __future__ import annotations

import pickle
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import (
    GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectEnd, ProjectState, ProjectStatus, end_record, supersede_record,
)
from src.engine.checkpoint import CanonicalStateHasher
from src.systems.strategic_systems.cognition_export import CognitionGraphExporter


def _project(status=ProjectStatus.ACTIVE) -> ProjectState:
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target="town_center", status=ObjectiveStatus.ACTIVE)
    return ProjectState(id="proj_combat_retreat_5", kind=GoalKind.COMBAT_RETREAT, status=status, objectives=[objective], active_objective_id="o1")


def _entity(project: ProjectState):
    entity = V2EntityBuilder(1).kind("hero").location(0.0, 0.0).build()
    return replace(entity, strategic=replace(entity.strategic, projects={project.id: project}))


def test_end_record_sets_the_status_and_the_typed_end_together():
    ended = end_record(_project(), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)
    assert (ended.status, ended.ended_by) == (ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)
    assert ended.objectives == _project().objectives and ended.id == _project().id


def test_end_record_never_rewrites_an_end_already_set():
    ended = end_record(_project(), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED)
    with pytest.raises(ValueError):
        end_record(ended, ProjectStatus.ABANDONED, ProjectEnd.SUPERSEDED_BY_TARGET)


def test_supersede_record_is_end_record_with_abandoned_and_superseded_by_target():
    assert supersede_record(_project()) == end_record(_project(), ProjectStatus.ABANDONED, ProjectEnd.SUPERSEDED_BY_TARGET)


def test_the_enum_keeps_its_existing_value_and_adds_threat_cleared():
    assert {e.value for e in ProjectEnd} == {"SUPERSEDED_BY_TARGET", "THREAT_CLEARED", "WAY_CLOSED"}  # WAY_CLOSED: F3, lodging


def test_threat_cleared_is_omitted_from_the_canonical_dict_until_set_and_changes_the_hash_only_then():
    plain, ended = _entity(_project()), _entity(end_record(_project(), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED))
    assert "ended_by" not in plain.to_canonical_dict()["strategic"]["projects"]["proj_combat_retreat_5"]
    assert ended.to_canonical_dict()["strategic"]["projects"]["proj_combat_retreat_5"]["ended_by"] == "THREAT_CLEARED"
    assert CanonicalStateHasher.get_hash(AuthoritativeState(tick=1, seed=1, entities={1: plain})) != CanonicalStateHasher.get_hash(AuthoritativeState(tick=1, seed=1, entities={1: ended}))


def test_threat_cleared_round_trips_through_the_checkpoint_blob():
    state = AuthoritativeState(tick=1, seed=1, entities={1: _entity(end_record(_project(), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED))})
    restored = pickle.loads(pickle.dumps(state, protocol=pickle.HIGHEST_PROTOCOL))
    assert restored.entities[1].strategic.projects["proj_combat_retreat_5"].ended_by == ProjectEnd.THREAT_CLEARED
    assert CanonicalStateHasher.get_hash(restored) == CanonicalStateHasher.get_hash(state)


def test_the_cognition_export_copies_the_end_and_omits_it_while_unset():
    def project_node(entity):
        return next(n for n in CognitionGraphExporter.export(entity).nodes if n.kind == "project")
    assert "ended_by" not in project_node(_entity(_project())).attributes
    assert project_node(_entity(end_record(_project(), ProjectStatus.COMPLETED, ProjectEnd.THREAT_CLEARED))).attributes["ended_by"] == "THREAT_CLEARED"
