"""The perception gate's calibration (PERC 3a; TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT): the one-record catalog family
``data/content/perception/perception_settings.yaml`` (``PerceptionSettingsDefinition``).

It is a catalog family like ``navigation_experience_settings.yaml`` so its values are part of the catalog fingerprint, the run's identity. The values are read from the WARMED catalog (loaded once,
shape-validated by the schema), so there is no file read at tick time and no module-level state here. A catalog with no such record raises ``PerceptionSettingsError`` naming the file: there is no code
default (a value that moves a run belongs in data). The ladder-dependent checks are ``src.world.perception.gate.validate_perception_settings``.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Optional

from src.content.common_knowledge_seed import warmed_catalog

PERCEPTION_SETTINGS_FILE = "data/content/perception/perception_settings.yaml"
PERCEPTION_SETTINGS_ID = "perception_settings"


class PerceptionSettingsError(ValueError):
    """The catalog has no valid perception settings record, or a value fails a load check; the message names the file."""


@dataclass(frozen=True, slots=True)
class PerceptionSettings:
    """The gate's calibration (data/content/perception/perception_settings.yaml)."""
    perception_threshold: float
    distance_falloff_per_tile: float
    distance_factor_min: float
    night_vision_steps: int
    size_visibility: Mapping[str, str]

    @property
    def undeclared_visibility(self) -> str:
        """A body with no declared size gives off the medium entry of the size map (one value, not a second one)."""
        return self.size_visibility["medium"]


def perception_settings(catalog: Optional[Any] = None) -> PerceptionSettings:
    """The gate's calibration from ``catalog`` (default: the warmed catalog)."""
    cat = warmed_catalog() if catalog is None else catalog
    record = getattr(cat, "perception_settings", {}).get(PERCEPTION_SETTINGS_ID)
    if record is None:
        raise PerceptionSettingsError(f"{PERCEPTION_SETTINGS_FILE}: no record with id {PERCEPTION_SETTINGS_ID!r}; the catalog did not load it or it failed its schema")
    return PerceptionSettings(
        float(record.perception_threshold), float(record.distance_falloff_per_tile), float(record.distance_factor_min), int(record.night_vision_steps),
        MappingProxyType(dict(record.size_visibility)),
    )
