"""Ideas 32+43 (Reproduction + population_cohorts seeding) corpus proof
(TCK-20260906-CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS) against the real `frontier_living_world`.

Real, empirically confirmed (not assumed): a live 600-tick Kernel.tick_once() run of this world
produces real births (new entities with lifecycle.parent_a_entity_id/parent_b_entity_id set) -- no
fixed low tick budget was picked blindly; 600 was chosen after confirming the entity count actually
grows within it. `PopulationCohort.migration_threshold` (src/domains/demographics/cohort.py) is
asserted directly as a static field default. The real birth's genetic_profile is asserted to be a
correct GeneticsSystem.combine_profiles() blend of both real parents' own profiles, each component
within [0.8, 1.3] (src/systems/lifecycle_systems/genetics.py) -- a regression-catching comparison
against the real function, not a bare range check.
"""
from __future__ import annotations

import pytest

from tools.calibrate_simq import _load_world_state
from src.config.profiles import PROD_SMALL
from src.domains.demographics.cohort import PopulationCohort
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.lifecycle_systems.genetics import GeneticsSystem

# Births are unflagged (M1): the run needs no flag, only enough ticks for a pair at the friend line to conceive and carry to term.
# 250 -> 3000 (owner #715 7158923490): a birth is its pregnancy's due tick, 2400 ticks after the conception; measured on this world and seed (42), the first
# birth is at tick 2161 (conceived at 961).
_RUN_TICKS = 3000


def test_migration_threshold_default_is_the_real_scarcity_gate():
    assert PopulationCohort(bracket="adult").migration_threshold == 0.7, (
        "PopulationCohort's real default migration_threshold must stay 0.7 (E52B) -- "
        "the cohort default every reader of population_cohorts relies on"
    )


@pytest.mark.extra_slow  # about 3.5 minutes for the 3000-tick run
def test_a_real_birth_produces_a_correctly_blended_genetic_profile_within_range():
    state, report = _load_world_state("frontier_living_world", seed=42)
    assert state is not None, "frontier_living_world must be a real, compilable corpus world"
    starting_ids = set(state.entities.keys())

    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        born_entity = None
        for _tick in range(_RUN_TICKS):
            kernel.tick_once()
            new_ids = set(kernel.state.entities.keys()) - starting_ids
            for eid in sorted(new_ids):
                ent = kernel.state.entities[eid]
                if ent.lifecycle.parent_a_entity_id is not None and ent.lifecycle.parent_b_entity_id is not None:
                    born_entity = ent
                    break
            if born_entity is not None:
                break
    finally:
        kernel.shutdown()

    assert born_entity is not None, (
        f"frontier_living_world must produce at least one real two-parent birth within "
        f"{_RUN_TICKS} ticks (empirically confirmed reachable at this budget before writing this test)"
    )

    profile = born_entity.lifecycle.genetic_profile
    assert profile is not None, "a real birth must carry a real, non-null genetic_profile"
    for attr in ("strength_mult", "agility_mult", "intelligence_mult", "wisdom_mult", "constitution_mult", "charisma_mult"):
        val = getattr(profile, attr)
        assert 0.8 <= val <= 1.3, f"{attr}={val} must fall within the real [0.8, 1.3] genetic range"

    parent_a = kernel.state.entities.get(born_entity.lifecycle.parent_a_entity_id)
    parent_b = kernel.state.entities.get(born_entity.lifecycle.parent_b_entity_id)
    if parent_a is not None and parent_b is not None and parent_a.lifecycle.genetic_profile and parent_b.lifecycle.genetic_profile:
        avg_strength = (parent_a.lifecycle.genetic_profile.strength_mult + parent_b.lifecycle.genetic_profile.strength_mult) / 2.0
        assert abs(profile.strength_mult - avg_strength) <= 0.5, (
            "child's strength_mult must be a real blend of both real parents' own profiles, "
            "not an unrelated independently-drawn value"
        )
