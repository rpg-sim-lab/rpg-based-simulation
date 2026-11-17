"""
PerceptionGate — data-driven entity perception gating via sense profiles.

Design constraints:
- Read-only: never mutates entity state or catalog state
- Deterministic: same inputs → same result
- Data-driven: all sense strengths come from catalog sense profiles, no species scripts
- Upstream of relation projection: gates raw detection capability only
- Senses come from the body's SPECIES only (PERC-02, derived at read: catalog.species[species_of(entity)].sense_profile); nothing is stored on the body
- A species in content always has a profile (a missing one is a typed error); a body whose species is not in content at all (test fixtures only) is
  `unprofiled`: it perceives with the baseline senses, is counted per species (`unprofiled_counts`, observability, not durable state) and logged at DEBUG
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.content.repository import CatalogRepository
from src.content.species_senses import species_sense_profile
from src.core.species import SenseProfileError, species_of  # noqa: F401  (SenseProfileError is re-exported for callers of the gate)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Level → float mapping (shared with pressure_resolver)
# ---------------------------------------------------------------------------

_LEVEL_TO_FLOAT: Dict[str, float] = {
    "very_high": 1.0,
    "high": 0.9,
    "medium_high": 0.75,
    "medium": 0.6,
    "low_medium": 0.45,
    "low": 0.3,
    "very_low": 0.1,
    "none": 0.0,
}

_PERCEPTION_THRESHOLD = 0.2

# PERC-02 touch (rpg-designer ruling 2026-11-18): every bodily kind feels a body that is next to it. It is a channel, not a score term: it needs no light, no movement and
# no profile entry, and it changes no other channel's score. `reach` (context) is the Chebyshev tile distance the caller measured; a context without `reach` gets no touch (a forgotten key never means "always perceived").
CHANNEL_TOUCH = "touch"
TOUCH_REACH = 1

# PERC-02 (owner Q2a, #715 6937049127): at night vision counts NIGHT_VISION_STEPS levels lower on this ladder unless the profile declares night_vision.
_LEVEL_LADDER = ("very_high", "high", "medium_high", "medium", "low_medium", "low", "very_low", "none")
NIGHT_VISION_STEPS = 2


def _lower_level(val: Optional[str], steps: int) -> Optional[str]:
    """The level `steps` rungs down the ladder (floor `none`); an unknown level is returned unchanged."""
    if val is None:
        return None
    key = val.lower().replace("-", "_")
    if key not in _LEVEL_LADDER:
        return val
    return _LEVEL_LADDER[min(len(_LEVEL_LADDER) - 1, _LEVEL_LADDER.index(key) + steps)]


def _level(val: Optional[str]) -> float:
    if val is None:
        return 0.0
    return _LEVEL_TO_FLOAT.get(val.lower().replace("-", "_"), 0.0)


def _add_touch(signals_used: List[str], max_score: float, reach: Optional[float]) -> float:
    """Touch (PERC-02): a body within TOUCH_REACH tiles is felt. Appends the channel and returns the confidence score: contact alone is certain (1.0),
    while a pair already perceived by a scored channel keeps that channel's score. No `reach` (the caller measured none) means no touch."""
    if reach is None or reach > TOUCH_REACH:
        return max_score
    certain = not signals_used
    signals_used.append(CHANNEL_TOUCH)
    return 1.0 if certain else max_score


# ---------------------------------------------------------------------------
# Channel mapping: sense field → target signal key
# ---------------------------------------------------------------------------

_SENSE_TO_SIGNAL: Dict[str, str] = {
    "vision": "visibility",
    "hearing": "noise",
    "smell": "scent",
    "magic_sense": "magic_signal",
    "life_sense": "life_signal",
    "vibration": "vibration",
    "social_reading": "social_signal",
}

_BASELINE_SENSE: Dict[str, str] = {
    "vision": "medium",
    "hearing": "medium",
    "smell": "low",
    "magic_sense": "none",
    "social_reading": "medium",
}


# ---------------------------------------------------------------------------
# Output model
# ---------------------------------------------------------------------------

class PerceptionResult(BaseModel):
    """Result of a single perception check."""

    model_config = ConfigDict(frozen=True)

    perceived: bool
    confidence: float = Field(ge=0.0, le=1.0)
    signals_used: List[str]
    profile_source: str  # sense profile id used, or "baseline_humanoid"


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

class PerceptionGate:
    """
    Checks whether a source entity can perceive a target/event given its sense
    profile, distance, terrain context, and the target's emitted signals.

    Usage::

        gate = PerceptionGate(catalog)
        result = gate.can_perceive(source_entity, target_signals, context)
    """

    def __init__(self, catalog: CatalogRepository) -> None:
        self._catalog = catalog
        self.unprofiled_counts: Dict[str, int] = {}  # species id (or kind) -> reads by a body whose species is not in content; observability, not durable state

    def can_perceive(
        self,
        source_entity: Any,
        target_signals: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> PerceptionResult:
        """
        Determine whether source_entity detects the target.

        Args:
            source_entity: The perceiving body; its senses come from its species (``species_of``, the catalog's ``sense_profile``), nothing is stored on the body.
            target_signals: Dict or object with signal fields (visibility, noise, scent,
                            magic_signal, life_signal, vibration, social_signal).
                            All fields are optional; absent signals default to "none".
            context: Optional dict with:
                - distance (float, default 1.0): the Manhattan tile distance, the scored channels' distance term
                - terrain_modifier (float 0–1, default 1.0): environmental penalty
                - alertness (float 0–1, default 0.5): source's current alertness
                - reach (float, optional): the Chebyshev tile distance between the two bodies; a body at reach <= TOUCH_REACH is felt by touch; absent = no touch
                - night (bool, default False): it is the night half of the day; vision counts two levels lower unless the profile declares night_vision

        Returns:
            PerceptionResult with perceived, confidence, signals_used, profile_source.
        """
        ctx = context or {}
        distance: float = float(ctx.get("distance", 1.0))
        terrain_mod: float = float(ctx.get("terrain_modifier", 1.0))
        alertness: float = float(ctx.get("alertness", 0.5))

        # Clamp modifiers
        distance = max(0.0, distance)
        terrain_mod = max(0.0, min(1.0, terrain_mod))
        alertness = max(0.0, min(1.0, alertness))

        # Distance factor: linear falloff, min 0.05
        distance_factor = max(0.05, 1.0 - distance * 0.02)

        # Load sense profile
        sense_strengths, profile_source, night_vision = self._load_sense_strengths(source_entity)
        if bool(ctx.get("night", False)) and not night_vision:
            sense_strengths = dict(sense_strengths)
            sense_strengths["vision"] = _lower_level(sense_strengths.get("vision"), NIGHT_VISION_STEPS) or "none"

        # Extract target signals
        signals = _extract_signals(target_signals)

        # Evaluate each channel
        signals_used: List[str] = []
        max_score = 0.0

        for sense_field, signal_key in _SENSE_TO_SIGNAL.items():
            sense_val = sense_strengths.get(sense_field, "none")
            signal_val = signals.get(signal_key, "none")

            sense_strength = _level(sense_val)
            signal_strength = _level(signal_val)

            if sense_strength == 0.0 or signal_strength == 0.0:
                continue

            score = sense_strength * signal_strength * distance_factor * terrain_mod * (0.5 + alertness * 0.5)
            if score >= _PERCEPTION_THRESHOLD:
                signals_used.append(signal_key)
                if score > max_score:
                    max_score = score

        reach = ctx.get("reach")
        max_score = _add_touch(signals_used, max_score, None if reach is None else float(reach))
        perceived = len(signals_used) > 0
        confidence = min(1.0, max_score)

        return PerceptionResult(
            perceived=perceived,
            confidence=confidence,
            signals_used=signals_used,
            profile_source=profile_source,
        )

    def _load_sense_strengths(
        self,
        entity: Any,
    ) -> tuple[Dict[str, str], str, bool]:
        """The sense field values, the profile id used and whether it declares night vision, derived from the body's species (the one read site)."""
        species_id = species_of(entity)
        defn = species_sense_profile(self._catalog, species_id)
        if defn is None:
            self.unprofiled_counts[species_id] = self.unprofiled_counts.get(species_id, 0) + 1
            logger.debug("unprofiled body: species %r is not in content; baseline senses", species_id)
            return dict(_BASELINE_SENSE), "baseline_humanoid", False
        strengths = {
            field: getattr(defn, field)
            for field in _SENSE_TO_SIGNAL
            if getattr(defn, field, None) is not None
        }
        return strengths, defn.id, bool(defn.night_vision)


# ---------------------------------------------------------------------------
# Signal extraction helper
# ---------------------------------------------------------------------------

def _extract_signals(target: Any) -> Dict[str, str]:
    """Extract signal fields from a dict or attribute-bearing object."""
    signal_keys = set(_SENSE_TO_SIGNAL.values())
    if isinstance(target, dict):
        return {k: v for k, v in target.items() if k in signal_keys}
    result: Dict[str, str] = {}
    for key in signal_keys:
        val = getattr(target, key, None)
        if val is not None:
            result[key] = val
    return result
