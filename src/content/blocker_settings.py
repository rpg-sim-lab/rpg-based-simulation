"""The blocker settings that are balance values (F2; divergence 2.220): the one-record catalog family ``data/content/strategy/blocker_settings.yaml`` (``BlockerSettingsDefinition``).

It is a catalog family like ``defaults.yaml`` so its value is part of the catalog fingerprint, the run's identity. The value is read from the WARMED catalog (loaded once, validated by the schema:
an integer >= 1), so there is no file read at tick time and no module-level state here. A catalog with no such record raises ``BlockerSettingsError`` naming the file and the key: there is no silent
default. The existing blocker constants (backoff 100 and 800, quiet spell 200, suspension TTL 200) stay in ``src/core/strategic.py``."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from src.content.common_knowledge_seed import warmed_catalog

BLOCKER_SETTINGS_FILE = "data/content/strategy/blocker_settings.yaml"
BLOCKER_SETTINGS_ID = "blocker_settings"
ACCESS_GIVEUP_LIMIT_KEY = "access_giveup_limit"


class BlockerSettingsError(ValueError):
    """The catalog has no valid blocker settings record; the message names the file and the key."""


def access_giveup_limit(catalog: Optional[Any] = None) -> int:
    """How many give-ups of one destination end the project that wanted it, from ``catalog`` (default: the warmed catalog)."""
    cat = warmed_catalog() if catalog is None else catalog
    record = getattr(cat, "blocker_settings", {}).get(BLOCKER_SETTINGS_ID)
    if record is None:
        raise BlockerSettingsError(f"{BLOCKER_SETTINGS_FILE}: no record with id {BLOCKER_SETTINGS_ID!r} (key {ACCESS_GIVEUP_LIMIT_KEY!r}); the catalog did not load it or it failed its schema")
    return int(record.access_giveup_limit)


@dataclass(frozen=True)
class ServiceRefusalSettings:
    """The refusal rule's balance values (K2 fix, STRAT-191-194): ``limit`` consecutive refusals, each within ``window`` ticks of the previous, each with a reason in ``reasons``, file one blocker of ``severity``."""
    limit: int
    window: int
    reasons: Tuple[str, ...]
    severity: float


def service_refusal_settings(catalog: Optional[Any] = None) -> ServiceRefusalSettings:
    """The service refusal settings from ``catalog`` (default: the warmed catalog); no code default: a catalog with no record raises ``BlockerSettingsError``."""
    cat = warmed_catalog() if catalog is None else catalog
    record = getattr(cat, "blocker_settings", {}).get(BLOCKER_SETTINGS_ID)
    if record is None:
        raise BlockerSettingsError(f"{BLOCKER_SETTINGS_FILE}: no record with id {BLOCKER_SETTINGS_ID!r} (service refusal keys); the catalog did not load it or it failed its schema")
    return ServiceRefusalSettings(int(record.service_refusal_limit), int(record.service_refusal_window), tuple(record.service_refusal_reasons), float(record.service_refusal_severity))
