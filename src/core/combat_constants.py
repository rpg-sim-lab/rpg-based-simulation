"""
src/core/combat_constants.py
───────────────────────────────────────────────────────────────────────────────
Cross-layer combat-mechanics constants.

Neutral base-layer home for constants that both an engine/domains module and an observability
module need to reference without pointing gameplay logic at a telemetry module (or vice versa) --
same rationale and precedent as src/core/social_constants.py. src/core/ is already imported freely
by both layers.
"""
from __future__ import annotations

# hp/max_hp ratio below which an entity's survival counts as "near death" -- used by
# src.observability.event_extractor/event_shapers (near_death_survival event detection) and
# src.domains.combat_engagement.power (Sec 13.5a's WON_EASY/NEAR_DEATH combat-learning outcome
# classification, TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER) to keep both paths consistent
# with a single source of truth, rather than two independently-drifting near-death cutoffs.
NEAR_DEATH_HP_RATIO: float = 0.2

# outcome_kind values that are a terminal combat result for the defender (combat damage alone took it
# to <= 0 HP). A later same-tick writer (world dynamics' hazard drain) must not
# overwrite one of these in `CombatUpdate.outcome_kind`. The learning layer's
# `_DEFEATED_OUTCOME_KINDS` is this same set, derived from it so the two cannot drift.
TERMINAL_COMBAT_OUTCOME_KINDS = ("KILL", "DEFEAT")

# Perception radius an entity-targeted objective is held to: the radius CombatEngageScorer chooses its target within (get_neighbor_view radius) and the radius the
# threat reads (`perceived_hostiles`) use. A foundation constant so the objective lifecycle (systems) and the goal scorers (ai) share it without importing each other.
ENTITY_TARGET_PERCEPTION_RADIUS = 10.0

# A COMBAT_RETREAT project ends THREAT_CLEARED (divergence 2.156, STRAT-295) when `present_threat_to` is false AND the subject has reached the retreat's destination (within
# RETREAT_ARRIVAL_RADIUS, Manhattan: the same "arrived" line a detour's reach-location objective uses) OR the threat has stayed absent for CLEAR_TICKS consecutive ticks
# (`ProjectState.cleared_since`; a returning threat restarts the window, a suspension restarts it on resume).
CLEAR_TICKS: int = 200
RETREAT_ARRIVAL_RADIUS: float = 1.0
