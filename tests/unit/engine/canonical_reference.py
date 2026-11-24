"""The reference for the per-tick digest memo (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK).

`reference_entity_canonical_dict` is `EntityState.to_canonical_dict` AS IT WAS ON origin/main cef537d29, with the strategic and social blocks written inline, copied verbatim; the only two
changes are the removed read and write of the entity's own `_canonical_cache` (a reference must never answer from a memo). `reference_canonical_data` is `CanonicalStateHasher.to_canonical_data`
with that entity builder. Nothing here uses `CanonicalFragmentMemo`, `strategic_canonical_dict` or `social_canonical_dict`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict

from src.core.state import AuthoritativeState, EntityState
from src.engine.checkpoint import CanonicalStateHasher


def reference_entity_canonical_dict(self: EntityState) -> Dict[str, Any]:
    res = {
        "id": self.id,
        "kind": self.kind,
        "position": self.navigation.position,
        "readiness": self.combat.readiness,
        "active": self.lifecycle.active,
        "interaction": self.interaction.to_canonical_dict(),
        "identity": self.identity.to_canonical_dict(),
        "attributes": self.attributes.to_canonical_dict(),
        "aptitude": self.aptitude.to_canonical_dict(),
        "inventory": self.inventory.to_canonical_dict(),
        "equipment": {str(k): v for k, v in sorted(self.equipment.slots.items())},
        "strategic": {
            "current_project_id": self.strategic.current_project_id,
            "current_objective_id": self.strategic.current_objective_id,
            "home_region_id": self.strategic.home_region_id,
            "primary_overload_source": self.strategic.primary_overload_source,
            "last_overload_tick": self.strategic.last_overload_tick,
            # "profile" is intentionally excluded: CognitionProfile is derived from
            # entity attributes (WIS/INT/level/archetype), which are already covered
            # above -- a divergence there cannot be independent of already-detected state.
            "projects": {k: {
                "kind": v.kind,
                 "status": str(v.status),
                "active_objective_id": v.active_objective_id,
                "objectives": v.canonical_objectives(),
                **v.canonical_extra(),
            } for k, v in sorted(self.strategic.projects.items())},
            "directives": {k: asdict(v) for k, v in sorted(self.strategic.directives.items())},
            "blockers": {k: v.canonical_dict() for k, v in sorted(self.strategic.blockers.items())},
            "leads": {k: asdict(v) for k, v in sorted(self.strategic.leads.items())},
            "concerns": {k: asdict(v) for k, v in sorted(self.strategic.concerns.items())},
            "candidate_zones": {k: asdict(v) for k, v in sorted(self.strategic.candidate_zones.items())},
            "hypotheses": {k: asdict(v) for k, v in sorted(self.strategic.hypotheses.items())},
            "source_trust": {str(k): asdict(v) for k, v in sorted(self.strategic.source_trust.items())},
            "contracts": {k: {**asdict(v), "kind": str(v.kind), "status": str(v.status)}
                          for k, v in sorted(self.strategic.contracts.items())},
            "turning_points": [{**asdict(tp), "kind": str(tp.kind)} for tp in self.strategic.turning_points],
            "committed_intentions": [asdict(ci) for ci in self.strategic.committed_intentions],
            "boredom": dict(sorted(self.strategic.boredom.items())),
            "beliefs": {k: asdict(v) for k, v in sorted(self.strategic.beliefs.items())},
            "marriages": {k: asdict(v) for k, v in sorted(self.strategic.marriages.items())}
        },
        "social": {
            "trust_history": {str(k): v for k, v in sorted(self.social.trust_history.items())},
            "familiarity_history": {str(k): v for k, v in sorted(self.social.familiarity_history.items())},
            "debt_history": {str(k): v for k, v in sorted(self.social.debt_history.items())},
            "fear_history": {str(k): v for k, v in sorted(self.social.fear_history.items())},
            "grudge_history": {str(k): v for k, v in sorted(self.social.grudge_history.items())},
            "combat_loss_counts": {str(k): v for k, v in sorted(self.social.combat_loss_counts.items())},
            "salience_history": {str(k): v for k, v in sorted(self.social.salience_history.items())},
            "bonds": {str(k): asdict(v) for k, v in sorted(self.social.bonds.items())},
            "nemesis_ids": sorted(self.social.nemesis_ids),
            "place_attachment": dict(sorted(self.social.place_attachment.items())),
            "regional_reputation": dict(sorted(self.social.regional_reputation.items())),
            "betrayal_count": self.social.betrayal_count,
            "betrayal_records": [asdict(b) for b in self.social.betrayal_records],
            "public_reputation": self.social.public_reputation,
            "heroism_score": self.social.heroism_score,
            "notoriety_score": self.social.notoriety_score,
            "last_offer_tick": self.social.last_offer_tick,
            "rejection_count": {str(k): v for k, v in sorted(self.social.rejection_count.items())},
        },
        "combat": self.combat.to_canonical_dict(),
        "biological": self.biological.to_canonical_dict(),
        "lifecycle": self.lifecycle.to_canonical_dict(),
        "navigation": self.navigation.to_canonical_dict(),
        "task": {
            "work_kind": self.task.work_kind,
            "payload": dict(sorted(self.task.payload.items()))
        },
        "group_id": self.identity.group_id,
        "properties": dict(sorted(self.identity.properties.items())),
        "self_model": self.self_model.to_canonical_dict(),
        "cognition": self.cognition.to_canonical_dict(),
    }
    return res



def reference_canonical_data(state: AuthoritativeState) -> Dict[str, Any]:
    data = CanonicalStateHasher.to_canonical_data(state)
    data["entities"] = {str(eid): reference_entity_canonical_dict(state.entities[eid]) for eid in sorted(state.entities.keys())}
    return data


def reference_json(state: AuthoritativeState, pretty: bool = False) -> str:
    data = reference_canonical_data(state)
    return json.dumps(data, sort_keys=True, indent=2) if pretty else json.dumps(data, sort_keys=True, separators=(",", ":"))


def reference_digest(state: AuthoritativeState) -> str:
    return hashlib.sha256(reference_json(state).encode("utf-8")).hexdigest()
