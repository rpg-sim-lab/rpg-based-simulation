"""The reproduction mate gate (M1): the one place births reads social state, and only the accepted-marriage record and the two directed bond sentiments."""
# Compliance IDs: WORLD-122
from __future__ import annotations

from typing import TYPE_CHECKING

from src.content.schema import SentimentThreshold
from src.core.strategic import MarriageStatus
from src.systems.social_systems.relationships import RelationshipService

if TYPE_CHECKING:
    from src.content.schema import ReproductionProfileDefinition
    from src.core.state import EntityState

_THRESHOLDS = {SentimentThreshold.FRIEND: RelationshipService.FRIEND_SENTIMENT_THRESHOLD}


def passes_mate_gate(mother: EntityState, mate: EntityState, profile: ReproductionProfileDefinition) -> bool:
    """True when the pair may conceive under the profile's declared gate.

    ``none`` reads no social state. ``bond`` passes on an ACCEPTED marriage between the two (held by either party) or when both directed
    sentiments (mother to mate, mate to mother) are at or above the profile's threshold. Role, kind and occupation are never read."""
    if profile.mate_gate == "none":
        return True
    pair = {mother.id, mate.id}
    for holder in (mother, mate):
        if any(m.status == MarriageStatus.ACCEPTED and {m.proposer_entity_id, m.target_entity_id} == pair for m in holder.strategic.marriages.values()):
            return True
    if profile.min_mutual_sentiment is None:  # the loader requires a line with `bond`; none means no bond can pass
        return False
    threshold = _THRESHOLDS[profile.min_mutual_sentiment]
    toward_mate, toward_mother = mother.social.bonds.get(mate.id), mate.social.bonds.get(mother.id)
    return toward_mate is not None and toward_mother is not None and toward_mate.sentiment >= threshold and toward_mother.sentiment >= threshold
