"""An accepted recruitment creates the contract on both sides and moves no gold (Mechanics Bible ch03 §1).

``execute_recruit`` used to issue two ``RECRUIT`` transfer intents: the payer's was never checked against its balance, so a short payer minted the
difference, and the two sides were not tied together. The payout is not a transfer until RECRUIT is wired (see
``docs/mechanics/resource_conservation_contract.md``).
"""

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractStatus
from src.engine.domain.core_actions import CoreActions

pytestmark = [pytest.mark.domain("social"), pytest.mark.domain("economy"), pytest.mark.level("unit")]


def _recruit(*, payer_gold, trust):
    recruiter = V2EntityBuilder(2).kind("HERO").location(0.0, 0.0).inventory(gold=payer_gold).build()
    target = V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).social(trust_history={2: trust}).build()
    state = AuthoritativeState(tick=5, seed=1, entities={1: target, 2: recruiter})
    return CoreActions.execute_recruit(recruiter, {"target_id": 1, "payout": 100}, 5, [(1, target)], state)


def test_an_accepted_recruitment_emits_no_resource_transfers():
    updates = _recruit(payer_gold=10, trust=0.9)
    assert set(updates) == {1, 2}
    assert all(not u.resource_transfers for u in updates.values())


def test_an_accepted_recruitment_creates_the_contract_on_both_sides():
    updates = _recruit(payer_gold=10, trust=0.9)
    for side in (1, 2):
        contracts = updates[side].strategic.contracts_add_or_update
        assert [(c.id, c.kind, c.status, c.source_id, c.target_id) for c in contracts] == [
            ("contract_recruit_2_1_5", ContractKind.RECRUITMENT, ContractStatus.ACTIVE, 2, 1)
        ]
