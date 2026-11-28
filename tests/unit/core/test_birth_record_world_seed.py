# Compliance IDs: WORLD-122
"""V2EntityBuilder.birth_record(world_seed=...): the genetics combination seed gains the world seed only when one is given (rulings Q19)."""
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.systems.lifecycle_systems.genetics import GeneticsSystem

A, B = GeneticsSystem.generate_profile_from_seed(11), GeneticsSystem.generate_profile_from_seed(22)


def _combined(**extra):
    child = V2EntityBuilder(900).birth_record(
        parent_a_entity_id=1, parent_b_entity_id=2, birth_tick=300, parent_a_genetic_profile=A, parent_b_genetic_profile=B,
        parent_a_role=EntityRole.CITIZEN, parent_b_role=EntityRole.CITIZEN, **extra,
    ).build()
    return child.lifecycle.genetic_profile


def test_without_a_world_seed_the_combination_seed_is_the_original_expression():
    expected = GeneticsSystem.combine_profiles(A, B, combat_lean=False, seed=1 * 1_000_003 + 2 * 97 + 300)
    assert _combined() == expected == _combined(world_seed=None)


def test_two_world_seeds_give_different_combined_profiles_for_the_same_parents_and_tick():
    assert _combined(world_seed=42) != _combined(world_seed=43)
    assert _combined(world_seed=42) == _combined(world_seed=42)


def test_a_parentless_birth_record_is_unchanged_by_the_new_parameter():
    child = V2EntityBuilder(900).birth_record(parent_a_entity_id=None, parent_b_entity_id=None, birth_tick=5).build()
    assert child.lifecycle.genetic_profile is None and child.lifecycle.birth_tick == 5


def test_the_births_path_hands_both_parent_profiles_so_the_builders_id_only_fallback_never_fires(monkeypatch):
    from src.core import builder
    from src.world import births

    calls = []

    class _Spy:
        generate_profile_from_seed = staticmethod(lambda seed: calls.append(seed))
        combine_profiles = staticmethod(GeneticsSystem.combine_profiles)

    monkeypatch.setattr(builder, "GeneticsSystem", _Spy)
    real = births.get_catalog()

    class _Certain:
        def get_reproduction_profile(self, profile_id):
            return real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 1.0, "mate_gate": "none", "min_mutual_sentiment": None})

        def __getattr__(self, name):
            return getattr(real, name)

    monkeypatch.setattr(births, "get_catalog", lambda: _Certain())
    from src.core.state import AuthoritativeState
    from src.systems.world_systems.generator import EntityGenerator

    parents = {i: V2EntityBuilder(i).kind("human").location(5.0, 5.0).build() for i in (1, 2)}
    state = AuthoritativeState(tick=30, seed=42, entities=parents, next_entity_id=3)
    generator = EntityGenerator(state.seed + state.tick)
    generator._last_id = 2
    from src.engine.apply import ApplyPath
    conceived = ApplyPath.apply_generation(state, births.BirthService.process_births(state, generator), 31, 31)
    due = max(e.lifecycle.pregnancy.due_tick for e in conceived.entities.values() if e.lifecycle.pregnancy)
    at_term = AuthoritativeState(tick=due, seed=42, entities=conceived.entities, next_entity_id=conceived.next_entity_id)
    generator = EntityGenerator(at_term.seed + at_term.tick)
    generator._last_id = conceived.next_entity_id - 1
    update = births.BirthService.process_births(at_term, generator)
    assert len(update.entities_add) == 1 and calls == []
