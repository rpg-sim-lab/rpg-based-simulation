"""The navigation experience memory's balance values (the #996 rework; design section 9): the one-record catalog family ``data/content/strategy/navigation_experience_settings.yaml``
(``NavigationExperienceSettingsDefinition``).

It is a catalog family like ``blocker_settings.yaml`` so its values are part of the catalog fingerprint, the run's identity. The values are read from the WARMED catalog (loaded once, validated by the schema:
integers >= 1), so there is no file read at tick time and no module-level state here. A catalog with no such record raises ``NavigationExperienceSettingsError`` naming the file and the keys: there is no silent default."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.content.common_knowledge_seed import warmed_catalog

NAVIGATION_EXPERIENCE_SETTINGS_FILE = "data/content/strategy/navigation_experience_settings.yaml"
NAVIGATION_EXPERIENCE_SETTINGS_ID = "navigation_experience_settings"


class NavigationExperienceSettingsError(ValueError):
    """The catalog has no valid navigation experience settings record; the message names the file."""


@dataclass(frozen=True, slots=True)
class NavigationExperienceSettings:
    """The five balance values of the navigation experience memory (data/content/strategy/navigation_experience_settings.yaml)."""
    oscillation_review_delay: int
    bodies_review_delay: int
    approach_change_radius: int
    navigation_experience_cap: int
    occupied_review_delay: int


def navigation_experience_settings(catalog: Optional[Any] = None) -> NavigationExperienceSettings:
    """The five balance values of the experience memory, from ``catalog`` (default: the warmed catalog)."""
    cat = warmed_catalog() if catalog is None else catalog
    record = getattr(cat, "navigation_experience_settings", {}).get(NAVIGATION_EXPERIENCE_SETTINGS_ID)
    if record is None:
        raise NavigationExperienceSettingsError(f"{NAVIGATION_EXPERIENCE_SETTINGS_FILE}: no record with id {NAVIGATION_EXPERIENCE_SETTINGS_ID!r}; the catalog did not load it or it failed its schema")
    return NavigationExperienceSettings(int(record.oscillation_review_delay), int(record.bodies_review_delay), int(record.approach_change_radius), int(record.navigation_experience_cap), int(record.occupied_review_delay))
