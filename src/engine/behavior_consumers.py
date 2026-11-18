"""
Singleton accessors for PerceptionGate and MotivationPressureResolver.

Provides lazy-initialised module singletons for use in the tactical engine.
Configurable for tests via configure_behavior_consumers / reset_behavior_consumers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.content.common_knowledge_seed import install_warm_catalog_provider
from src.core.species import species_of
from src.engine.perception_signals import emitted_signals

_perception_gate = None
_pressure_resolver = None
_catalog = None


def configure_behavior_consumers(catalog: Any) -> None:
    """Inject a pre-loaded catalog for tests or custom environments."""
    global _catalog, _perception_gate, _pressure_resolver
    from src.world.perception.gate import PerceptionGate
    from src.world.motivation.pressure_resolver import MotivationPressureResolver
    _catalog = catalog
    _perception_gate = PerceptionGate(catalog)
    _pressure_resolver = MotivationPressureResolver(catalog)


def reset_behavior_consumers() -> None:
    """Reset singletons (for test isolation)."""
    global _catalog, _perception_gate, _pressure_resolver
    _catalog = _perception_gate = _pressure_resolver = None


def get_perception_gate():
    """Return the module-level PerceptionGate, auto-initialising if needed."""
    global _perception_gate
    if _perception_gate is None:
        _auto_init()
    return _perception_gate


def get_pressure_resolver():
    """Return the module-level MotivationPressureResolver, auto-initialising if needed."""
    global _pressure_resolver
    if _pressure_resolver is None:
        _auto_init()
    return _pressure_resolver


def get_cognition_profile_definition(profile_id: str):
    """Return the named CognitionProfileDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_cognition_profile(profile_id)


def get_kind_properties(species_id: Optional[str]) -> Tuple[Any, Any]:
    """(SpeciesDefinition, BodyModelDefinition) of a species via the warmed catalog singleton; (None, None) when undeclared."""
    catalog = _seeding_catalog()
    species = catalog.get_species(species_id) if species_id else None
    return species, (catalog.get_body_model(species.body_model) if species else None)


def get_catalog() -> Any:
    """The warmed catalog singleton (auto-initialising), for readers that need more than one definition of it."""
    return _seeding_catalog()


def get_role_definition(role_id: str):
    """Return the named RoleDefinition via the warmed catalog singleton."""
    global _catalog
    if _catalog is None:
        _auto_init()
    return _catalog.get_role(role_id)


def _auto_init() -> None:
    """Load default catalog and initialise consumers."""
    global _catalog, _perception_gate, _pressure_resolver
    from src.content.repository import CatalogRepository
    from src.world.perception.gate import PerceptionGate
    from src.world.motivation.pressure_resolver import MotivationPressureResolver
    _catalog = CatalogRepository("data/content")
    _catalog.load_all()
    _perception_gate = PerceptionGate(_catalog)
    _pressure_resolver = MotivationPressureResolver(_catalog)


def get_entity_signals(entity: Any, tick: Optional[int] = None) -> Dict[str, str]:
    """The signals `entity` gives off for perception checks (PERC-02: they follow the body; see ``src.world.perception.signals.emitted_signals``)."""
    _, body = get_kind_properties(species_of(entity))
    return emitted_signals(entity, body, tick)


def _seeding_catalog() -> Any:
    """The warmed catalog, auto-initialising if needed, for KNOW-04's seeding (``src.content.common_knowledge_seed``)."""
    if _catalog is None:
        _auto_init()
    return _catalog


install_warm_catalog_provider(_seeding_catalog)
