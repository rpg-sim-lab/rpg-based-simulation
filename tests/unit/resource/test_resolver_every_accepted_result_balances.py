"""EXCH-02 / D38 / H7: coin is never destroyed or created by the resolver (TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN).

The invariant, at the level of ONE resolver result: when ``ResourceTransactionResolver.resolve`` ACCEPTS a transfer, the coin it writes sums to zero. The terms are every gold flow a
``TransactionResult`` carries (the payer's ``inventory_update``, a ``source_debit``, a ``building_update``, a ``treasury_update``, a ``home_storage_update``), less the coin of a
ground item or corpse the result removes (the holder's coin leaves with it). There is no declared sink in law (divergence 2.109), so a refusal is the only other lawful answer.

The assertion is deliberately VARIANT-NEUTRAL: it holds whether a payer who cannot cover a priced service is refused or is charged only what it holds. What it forbids is an accepted result
that debits the payer more than it credits anyone, the sink found at tick 3182 of crowded_frontier s46 on 414fb74f7 (a TOWN_SERVICE REST priced ``gold_delta=-10, gold_cost=0`` resolved for a
payer holding 0 gold: debit 10, credit 0).

The resolver is read as the apply path reads it (`src/engine/economy.py`): the payer's purse at resolve time is the ``entity.inventory`` (or the running inventory handed in as ``inventory_override``).
A same-tick arrival (an inheritance) does not enter that purse, which is why a result must balance on its own terms and not lean on the apply-time clamp at 0.
"""
from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

from src.core.builder import V2EntityBuilder
from src.core.conservation import ResourceTransactionResolver, TransactionResult
from src.core.state import AuthoritativeState, BuildingState, CorpseState, GroundItemState, InventoryComponent
from src.core.update_models.resources import ResourceTransferIntent
from src.core.updates import EntityUpdate, StateUpdate
from src.engine.economy import ResourceTransactionSystem

PAYER_ID = 9
DEAD_ID = 12
BUILDING_ID = 20003
SERVICE_KINDS = ("TOWN_SERVICE", "TAX", "REPAIR_FEE", "SERVICE_FEE", "INFORMATION_PURCHASE")
PRICE = 10


def _gold(update) -> float:
    return float(getattr(update, "gold_delta", 0) or 0) if update is not None else 0.0


def gold_net(result: TransactionResult, state: AuthoritativeState) -> float:
    """The coin an accepted result creates (positive) or destroys (negative): every flow it writes, less the coin of the holder it removes."""
    if not result.accepted:
        return 0.0
    flows = _gold(result.inventory_update)
    flows += _gold(result.source_debit.inventory_update) if result.source_debit is not None else 0.0
    flows += _gold(result.building_update.inventory) if result.building_update is not None and result.building_update.inventory is not None else 0.0
    flows += float(result.treasury_update.gold_delta) if result.treasury_update is not None else 0.0
    flows += _gold(result.home_storage_update)
    removed = 0.0
    if result.ground_item_remove is not None:
        removed += float(state.ground_items[result.ground_item_remove].gold)
    if result.corpse_remove is not None:
        removed += float(state.corpses[result.corpse_remove].gold)
    return flows - removed


def _payer(gold: int):
    return V2EntityBuilder(PAYER_ID).kind("hero").location(1.0, 1.0).combat(alive=True, readiness=100.0).inventory(gold=gold, max_slots=16, items=[]).build()


def _state(payer, *, building_gold: int = 0, **extra) -> AuthoritativeState:
    building = BuildingState(id=BUILDING_ID, kind="inn", position=(1.0, 1.0), functional=True, inventory=InventoryComponent(items=[], gold=building_gold))
    entities = {PAYER_ID: payer, **extra.pop("entities_extra", {})}
    return AuthoritativeState(tick=3181, seed=46, entities=entities, buildings={BUILDING_ID: building}, **extra)


def _resolve(state: AuthoritativeState, payer, intent: ResourceTransferIntent) -> TransactionResult:
    return ResourceTransactionResolver.resolve(state, payer, intent, reservations={})


# --- the priced services: a bed and a meal price through gold_delta, a repair, fee or tax through gold_cost ---------------------------------------------------------------------------------

SHAPES = {
    "priced_by_gold_delta": {"gold_delta": -PRICE, "gold_cost": 0},   # bed_delta (lodging.py) and the inn meal (building_services.py)
    "priced_by_gold_cost": {"gold_delta": 0, "gold_cost": PRICE},      # a repair, fee or tax
}


@pytest.mark.parametrize("payer_gold", [0, 4, PRICE, 140])
@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("source_kind", SERVICE_KINDS)
def test_an_accepted_service_to_a_building_credits_exactly_what_it_debits(source_kind, shape, payer_gold):
    payer = _payer(payer_gold)
    state = _state(payer)
    intent = ResourceTransferIntent(source_id=BUILDING_ID, source_kind=source_kind, transfer_kind="REST", is_group_required=True, **SHAPES[shape])
    result = _resolve(state, payer, intent)
    assert gold_net(result, state) == 0.0, (result.accepted, result.inventory_update, result.building_update, result.treasury_update)


@pytest.mark.parametrize("payer_gold", [0, 4, PRICE, 140])
@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("source_kind", SERVICE_KINDS)
def test_an_accepted_service_to_a_named_treasury_credits_exactly_what_it_debits(source_kind, shape, payer_gold):
    payer = _payer(payer_gold)
    state = _state(payer)
    intent = ResourceTransferIntent(source_id=999, source_kind=source_kind, transfer_kind="FEE", treasury_faction=3, is_group_required=True, **SHAPES[shape])
    result = _resolve(state, payer, intent)
    assert gold_net(result, state) == 0.0, (result.accepted, result.inventory_update, result.building_update, result.treasury_update)


@pytest.mark.parametrize("payer_gold", [0, 4, PRICE, 140])
@pytest.mark.parametrize("shape", sorted(SHAPES))
@pytest.mark.parametrize("source_kind", SERVICE_KINDS)
def test_a_service_with_no_payee_is_never_accepted_with_a_debit(source_kind, shape, payer_gold):
    """An unnamed payee (a non-building source, no treasury): the payer is debited nothing, or the transfer is refused. Never a debit that no one receives."""
    payer = _payer(payer_gold)
    state = _state(payer)
    intent = ResourceTransferIntent(source_id=999, source_kind=source_kind, transfer_kind="FEE", is_group_required=True, **SHAPES[shape])
    result = _resolve(state, payer, intent)
    assert gold_net(result, state) == 0.0, (result.accepted, result.inventory_update, result.building_update, result.treasury_update)


def test_the_t3181_shape_a_rest_for_a_payer_holding_nothing_destroys_no_coin():
    """crowded_frontier s46 on 414fb74f7, state tick 3181: e9 holds 0 gold, a REST at building 20003 is priced gold_delta=-10, gold_cost=0, and an inheritance of 140 lands the SAME tick.
    The inheritance does not reach the purse the resolver reads, so the REST must balance on its own: whatever it does with a payer holding 0, the coin it writes sums to zero."""
    payer = _payer(0)
    dead = (V2EntityBuilder(DEAD_ID).kind("hero").location(1.0, 1.0).combat(alive=False).inventory(gold=140, items=[]).build())
    state = _state(payer, entities_extra={DEAD_ID: dead})
    rest = ResourceTransferIntent(source_id=BUILDING_ID, source_kind="TOWN_SERVICE", gold_delta=-PRICE, transfer_kind="REST", is_group_required=True)
    inherit = ResourceTransferIntent(source_id=DEAD_ID, source_kind="INHERIT", gold_delta=140, transfer_kind="INHERIT", transaction_id="inherit:12")
    rest_result = _resolve(state, payer, rest)
    inherit_result = _resolve(state, payer, inherit)
    assert inherit_result.accepted and gold_net(inherit_result, state) == 0.0
    assert gold_net(rest_result, state) == 0.0
    # the sum the apply path writes to the payer this tick: the heir receives the 140, the bed charge is whatever the REST result debits
    payer_delta = _gold(inherit_result.inventory_update) + _gold(rest_result.inventory_update)
    building_credit = _gold(rest_result.building_update.inventory) if rest_result.building_update is not None else 0.0
    assert payer_delta + building_credit == 140.0  # the 140 left the dead body and is somewhere; nothing was destroyed


# --- the other gold-carrying source kinds -----------------------------------------------------------------------------------------------------------------------------------------------------

def test_an_inheritance_balances():
    payer = _payer(0)
    dead = (V2EntityBuilder(DEAD_ID).kind("hero").location(1.0, 1.0).combat(alive=False).inventory(gold=140, items=[]).build())
    state = _state(payer, entities_extra={DEAD_ID: dead})
    result = _resolve(state, payer, ResourceTransferIntent(source_id=DEAD_ID, source_kind="INHERIT", gold_delta=140, transfer_kind="INHERIT", transaction_id="inherit:12"))
    assert result.accepted and gold_net(result, state) == 0.0


def test_looting_a_corpse_or_a_ground_purse_balances():
    payer = _payer(0)
    corpse = CorpseState(id=7, original_entity_id=50, position=(1.0, 1.0), items=[], decay_tick=500, gold=33)
    ground = GroundItemState(id=8, item_id="", quantity=0, position=(1.0, 1.0), gold=21)
    state = _state(payer, corpses={7: corpse}, ground_items={8: ground})
    for kind, sid in (("CORPSE", 7), ("GROUND_ITEM", 8)):
        result = _resolve(state, payer, ResourceTransferIntent(source_id=sid, source_kind=kind))
        assert result.accepted and gold_net(result, state) == 0.0, kind


@pytest.mark.parametrize("payer_gold", [0, 4, 50])
def test_a_shop_purchase_balances(payer_gold):
    payer = _payer(payer_gold)
    state = _state(payer)
    result = _resolve(state, payer, ResourceTransferIntent(source_id=BUILDING_ID, source_kind="SHOP_BUY", gold_cost=5))
    assert gold_net(result, state) == 0.0


# --- through the economy phase: the running purse, several charges in one tick, and an arrival the resolver does not see ---------------------------------------------------------------------

def _coin_written(refined: StateUpdate) -> tuple[float, float]:
    """(the coin written to entities, the coin credited to buildings) by a resolved update: every entity's inventory gold_delta (a source debit lands in its entity's too) and every building's."""
    entities = sum(_gold(eu.inventory) for eu in refined.entity_updates.values())
    buildings = sum(_gold(bu.inventory) for bu in refined.building_updates.values())
    return entities, buildings


def _charge(kind: str, price: int, transfer_kind: str) -> ResourceTransferIntent:
    return ResourceTransferIntent(source_id=BUILDING_ID, source_kind=kind, gold_delta=-price, transfer_kind=transfer_kind, is_group_required=True)


def test_two_charges_that_exceed_the_purse_debit_exactly_what_the_building_receives_and_no_clamp_cut_is_needed():
    """A payer holding 12 is charged a bed (10) and a meal (5) in one tick. The running purse sees the first charge before the second, so the debits sum to what the purse held
    (12), the building receives 12, and the apply-time clamp at 0 has nothing to cut: the payer's purse plus its summed debit never goes below zero."""
    payer = _payer(12)
    state = _state(payer)
    update = StateUpdate(entity_updates={PAYER_ID: EntityUpdate(entity_id=PAYER_ID, resource_transfers=[_charge("TOWN_SERVICE", 10, "REST"), _charge("TOWN_SERVICE", 5, "EAT")])})
    refined = ResourceTransactionSystem.resolve_all(state, update)
    entity_coin, building_coin = _coin_written(refined)
    assert entity_coin + building_coin == 0.0, (entity_coin, building_coin)
    assert building_coin == 12.0
    assert payer.inventory.gold + _gold(refined.entity_updates[PAYER_ID].inventory) >= 0  # the clamp at 0 cuts nothing


def test_a_same_tick_inheritance_cannot_hide_a_charge_the_building_never_receives():
    """The t3181 shape through the economy phase: e9 holds 0, a REST is priced -10, and an inheritance of 140 from a dead body lands in the same tick. The 140 is the body's coin, moved: the total coin
    written to entities and buildings is zero, so the payer ends with the body's whole purse minus exactly what the building received."""
    payer = _payer(0)
    dead = (V2EntityBuilder(DEAD_ID).kind("hero").location(1.0, 1.0).combat(alive=False).inventory(gold=140, items=[]).build())
    state = _state(payer, entities_extra={DEAD_ID: dead})
    inherit = ResourceTransferIntent(source_id=DEAD_ID, source_kind="INHERIT", gold_delta=140, transfer_kind="INHERIT", transaction_id="inherit:12")
    update = StateUpdate(entity_updates={PAYER_ID: EntityUpdate(entity_id=PAYER_ID, resource_transfers=[_charge("TOWN_SERVICE", PRICE, "REST"), inherit])})
    refined = ResourceTransactionSystem.resolve_all(state, update)
    entity_coin, building_coin = _coin_written(refined)
    assert entity_coin + building_coin == 0.0, (entity_coin, building_coin)
    assert payer.inventory.gold + _gold(refined.entity_updates[PAYER_ID].inventory) == 140 - building_coin


# --- a service that would PAY the payer is no payout: the entity delta of a service is never positive (the price-0 mint) -------------------------------------------------------------------

@pytest.mark.parametrize("source_kind", SERVICE_KINDS)
def test_a_service_whose_gold_delta_exceeds_its_cost_pays_the_payer_nothing(source_kind):
    payer = _payer(50)
    state = _state(payer)
    intent = ResourceTransferIntent(source_id=BUILDING_ID, source_kind=source_kind, gold_delta=5, gold_cost=0, transfer_kind="REST", is_group_required=True)
    result = _resolve(state, payer, intent)
    assert result.accepted
    assert _gold(result.inventory_update) == 0.0 and result.building_update is None and gold_net(result, state) == 0.0


# --- the remaining gold-carrying kinds, and the guard that every kind is classified ---------------------------------------------------------------------------------------------------------

SIBLING_TICKET = "TCK-20261119-RECRUIT-CHEST-AND-CRAFTING-COSTS-DEBIT-THE-PAYER-WITH-NO-PAYEE"
# Kinds that still debit the payer with no payee (the sibling ticket fixes them). The test ASSERTS each is still unbalanced: when the sibling fixes one, this assertion fails and forces the set edit.
KNOWN_UNBALANCED = {"RECRUIT": {"gold_cost": 5}, "CHEST": {"gold_cost": 5}, "CRAFTING": {"gold_cost": 5}}
BALANCED_KINDS = set(SERVICE_KINDS) | {"INHERIT", "CORPSE", "GROUND_ITEM", "SHOP_BUY", "SHOP_SELL", "WAGE"}
NO_COIN_KINDS = {"NODE", "CARRIED_FOOD", "CORPSE_FOOD", "HOME_STORAGE"}   # no gold branch in the resolver
REWARD_KINDS = {"COMBAT", "QUEST"}   # a reward's coin is funded by a treasury or minted by decision (divergence 2.98): not asserted here


def test_a_shop_sale_balances():
    payer = _payer(0)
    state = _state(payer, building_gold=100)
    result = _resolve(state, payer, ResourceTransferIntent(source_id=BUILDING_ID, source_kind="SHOP_SELL", gold_delta=20))
    assert result.accepted and gold_net(result, state) == 0.0


def test_a_wage_balances():
    payer = _payer(0)
    state = _state(payer, building_gold=100)
    result = _resolve(state, payer, ResourceTransferIntent(source_id=BUILDING_ID, source_kind="WAGE", gold_delta=8))
    assert result.accepted and gold_net(result, state) == 0.0


@pytest.mark.parametrize("source_kind", sorted(KNOWN_UNBALANCED))
def test_the_known_unbalanced_kinds_are_still_unbalanced_until_their_sibling_ticket_lands(source_kind):
    """ASSERTS the sink so a fix (the sibling ticket named by SIBLING_TICKET) fails here and forces removing the kind from KNOWN_UNBALANCED."""
    payer = _payer(50)
    state = _state(payer)
    result = _resolve(state, payer, ResourceTransferIntent(source_id=BUILDING_ID, source_kind=source_kind, **KNOWN_UNBALANCED[source_kind]))
    assert result.accepted
    assert gold_net(result, state) < 0.0, f"{source_kind} now balances: remove it from KNOWN_UNBALANCED ({SIBLING_TICKET})"


def _handled_source_kinds() -> set[str]:
    source = textwrap.dedent(inspect.getsource(ResourceTransactionResolver.resolve))
    kinds: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Attribute) and node.left.attr == "source_kind":
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(comparator.value, str):
                    kinds.add(comparator.value)
                elif isinstance(comparator, ast.Tuple):
                    kinds.update(el.value for el in comparator.elts if isinstance(el, ast.Constant) and isinstance(el.value, str))
    return kinds


def test_every_source_kind_the_resolver_handles_is_classified_here():
    handled = _handled_source_kinds()
    classified = BALANCED_KINDS | set(KNOWN_UNBALANCED) | NO_COIN_KINDS | REWARD_KINDS
    assert handled, "source-kind scan found nothing; the guard itself is broken"
    assert handled - classified == set(), "a source kind the resolver handles has no balance classification (balanced, known-unbalanced, coin-free or reward)"
    assert classified - handled == set(), "a classified source kind the resolver no longer handles"


# --- a service with no payee is counted (observability, not durable state) ---------------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("source_id,faction,expect_missing", [(999, None, True), (999, 3, False), (BUILDING_ID, None, False)])
def test_only_a_priced_service_that_names_no_payee_sets_payee_missing(source_id, faction, expect_missing):
    payer = _payer(50)
    state = _state(payer)
    intent = ResourceTransferIntent(source_id=source_id, source_kind="TAX", gold_delta=-PRICE, transfer_kind="TAX", treasury_faction=faction)
    result = _resolve(state, payer, intent)
    assert result.accepted and result.payee_missing is expect_missing
    assert gold_net(result, state) == 0.0


def test_a_broke_payer_at_a_building_is_not_a_missing_payee():
    payer = _payer(0)
    state = _state(payer)
    result = _resolve(state, payer, _charge("TOWN_SERVICE", PRICE, "REST"))
    assert result.accepted and result.payee_missing is False and _gold(result.inventory_update) == 0.0


def test_a_free_unnamed_service_is_not_counted():
    """Price 0: nothing was due, so no payee is missing."""
    payer = _payer(50)
    state = _state(payer)
    result = _resolve(state, payer, ResourceTransferIntent(source_id=999, source_kind="SERVICE_FEE", gold_delta=0, gold_cost=0, transfer_kind="FEE"))
    assert result.accepted and result.payee_missing is False


def _fee(group_id=None):
    return ResourceTransferIntent(source_id=999, source_kind="TAX", gold_delta=-PRICE, transfer_kind="TAX", group_id=group_id)


@pytest.fixture
def counts():
    from src.core.conservation import PayeeMissingCounts

    PayeeMissingCounts.reset()
    yield PayeeMissingCounts
    PayeeMissingCounts.reset()


def _resolve_all(intents, payer_gold=50):
    payer = _payer(payer_gold)
    state = _state(payer)
    return state, ResourceTransactionSystem.resolve_all(state, StateUpdate(entity_updates={PAYER_ID: EntityUpdate(entity_id=PAYER_ID, resource_transfers=list(intents))}))


def test_the_economy_phase_counts_each_committed_no_payee_fee_once_and_the_ledger_tally_carries_it(counts):
    from src.observability.run_ledger import RunLedger

    RunLedger.reset_run_state()
    RunLedger.configure(True)
    try:
        state, refined = _resolve_all([_fee()])
        entity_coin, building_coin = _coin_written(refined)
        assert entity_coin + building_coin == 0.0
        assert counts.counts() == {"TAX|TAX": 1}
        assert RunLedger.tally_event().payload["payee_missing"] == {"TAX|TAX": 1}
    finally:
        RunLedger.reset_run_state()
    assert counts.counts() == {}  # the run ledger resets it at run start


def test_the_same_fee_with_a_building_source_is_not_counted(counts):
    _resolve_all([ResourceTransferIntent(source_id=BUILDING_ID, source_kind="TAX", gold_delta=-PRICE, transfer_kind="TAX")])
    assert counts.counts() == {}


def test_a_no_payee_fee_in_a_group_that_rolls_back_is_not_counted_but_a_committed_group_is(counts):
    """The count is the COMMIT path only: the trial resolve of a group runs `_note_effects` with no intent, so a group that rolls back (here, a crafting cost the payer cannot meet) leaves
    the counts at zero, and the same fee in a group that commits is counted once."""
    failing = ResourceTransferIntent(source_id=BUILDING_ID, source_kind="CRAFTING", gold_cost=10_000, transfer_kind="CRAFT", group_id="G1")
    _, rolled_back = _resolve_all([_fee("G1"), failing])
    assert counts.counts() == {}
    assert not any(r.accepted for r in rolled_back.entity_updates[PAYER_ID].intent_results)
    _resolve_all([_fee("G2")])
    assert counts.counts() == {"TAX|TAX": 1}


def test_the_count_never_reaches_the_state_the_hash_reads(monkeypatch, counts):
    """Nothing in the simulation reads the counts: the refined update (what the apply path turns into the next state) is identical with the noter real or replaced by a no-op."""
    from src.core.conservation import PayeeMissingCounts

    _, with_counter = _resolve_all([_fee()])
    monkeypatch.setattr(PayeeMissingCounts, "note", classmethod(lambda cls, source_kind, transfer_kind: None))
    _, without_counter = _resolve_all([_fee()])
    assert with_counter == without_counter


def test_only_the_economy_commit_path_writes_the_counts_and_only_the_run_ledger_reads_or_resets_them():
    from pathlib import Path

    root = Path(__file__).resolve().parents[3] / "src"
    users = {}
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "PayeeMissingCounts" in text:
            users[path.relative_to(root).as_posix()] = text
    assert set(users) == {"core/conservation.py", "engine/economy.py", "observability/run_ledger.py"}, sorted(users)
    economy, ledger = users["engine/economy.py"], users["observability/run_ledger.py"]
    assert "PayeeMissingCounts.note(" in economy and "PayeeMissingCounts.counts(" not in economy and "PayeeMissingCounts.reset(" not in economy
    assert "PayeeMissingCounts.counts(" in ledger and "PayeeMissingCounts.reset(" in ledger and "PayeeMissingCounts.note(" not in ledger
    # conservation.py holds only the class definition: no resolver branch may read or write the counter (a future branch reading it would make resolution depend on observability state)
    conservation = users["core/conservation.py"]
    assert "PayeeMissingCounts.counts(" not in conservation and "PayeeMissingCounts.note(" not in conservation and "PayeeMissingCounts.reset(" not in conservation
    assert conservation.count("PayeeMissingCounts") == 1 and "class PayeeMissingCounts:" in conservation
