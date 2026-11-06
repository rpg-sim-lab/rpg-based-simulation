"""
src/ai/goals/present_threat.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07

World Rule SURV-07: only a present threat to life outranks a pressing need, so a need's escalation gives way while a present
threat holds (a need never outbids combat flight or engagement). "Present threat" is AGENCY-07's own test (`present_threat_terms`:
wounded, a hostile adjacent, targeting or closing, or outmatching), over the hostiles the subject perceives, with the catalog
hostility the combat scorers use. A wound alone is not a threat here: with no hostile in view there is nothing to give way to.
A pure read of the state.

ACTING (TCK-20261023-AN-ACTING-HOSTILE-IS-AN-ACT-NOT-A-STATE, owner decision memo row 88): a hostile ACTS on a subject only by an act, never by a state.
`present_threat_to` keeps AGENCY-07's full terms (they are why flight is warranted); `acting_threat_to` is the narrower test that decides whether a hostile
holds back an escalated need: the subject perceives it AND either (a) its current task is an attack or a pursuit aimed at the subject, or (b) it took hp
from the subject by a hit within `NEED_WAKE_CADENCE` ticks. Wounded, adjacent, closing without (a) and outmatched are not acts.
NEED_YIELDS (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED, SURV-07 LAW P, shape S1): `acting_threat_to` is `tactical_threat.need_yields` over the subject's perceived hostiles: the one test every site that weighs a pressing need (`need_pull.need_is_pressing`) against another goal or act reads, so a pressing need gives way only to a hostile that ACTS on the subject. Flight keeps `present_threat_terms` (AGENCY-07), the in-place rest/eat steps keep those terms (S1). Hunt exemption: with HUNGER pressing, a hostile the subject regards as prey (`Relation.PREDATION`) does not hold the need path back from the fight with that prey (`tactical.py`, not here).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from src.ai.goals.scorers_support import perceived_hostiles
from src.engine.tactical_threat import need_yields, present_threats

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState


def present_threat_to(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when a perceived hostile makes a present threat to `entity` (AGENCY-07's terms)."""
    return bool(present_threats(entity, perceived_hostiles(entity, state)))


def acting_threat_to(entity: "EntityState", state: "AuthoritativeState") -> bool:
    """True when a perceived hostile is acting on `entity` (see the module docstring). A pure read of the state."""
    return need_yields(entity, perceived_hostiles(entity, state), state.tick)
