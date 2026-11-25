"""The way-round law's two numbers (F1, divergence 2.213; rpg-designer 2026-11-21): the one-record catalog family ``data/content/movement/wayround_settings.yaml`` (``WayroundSettingsDefinition``).

It is a catalog family like ``defaults.yaml`` so the values are part of the catalog fingerprint, the run's identity. They are read from the WARMED catalog (loaded once, validated by the schema: both
integers >= 1, no cross-check between them since one counts steps and the other ticks), so there is no file read at tick time and no module-level state here; ``src/engine/movement.py`` binds the
result once. A catalog with no such record raises ``WayroundSettingsError`` naming the file and the keys: there is no silent default."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from src.content.common_knowledge_seed import warmed_catalog

WAYROUND_SETTINGS_FILE = "data/content/movement/wayround_settings.yaml"
WAYROUND_SETTINGS_ID = "wayround_settings"


class WayroundSettingsError(ValueError):
    """The catalog has no valid way-round settings record; the message names the file and the keys."""


@dataclass(frozen=True, slots=True)
class WayroundSettings:
    """The two way-round numbers: ``limit`` (steps with no net progress before the real replan) and ``quiet_ticks`` (the longest gap between two events of one pursuit)."""
    limit: int
    quiet_ticks: int


def wayround_settings(catalog: Optional[Any] = None) -> WayroundSettings:
    """The way-round settings from ``catalog`` (default: the warmed catalog)."""
    cat = warmed_catalog() if catalog is None else catalog
    record = getattr(cat, "wayround_settings", {}).get(WAYROUND_SETTINGS_ID)
    if record is None:
        raise WayroundSettingsError(f"{WAYROUND_SETTINGS_FILE}: no record with id {WAYROUND_SETTINGS_ID!r} (keys 'wayround_limit', 'wayround_quiet_ticks'); the catalog did not load it or it failed its schema")
    return WayroundSettings(int(record.wayround_limit), int(record.wayround_quiet_ticks))
