"""TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER, part A: ONE shared bed-refusal predicate, `service_admission.no_bed_for`.

`no_bed_for` = `finds_no_bed` (no free bed) OR (the same scope AND the subject cannot pay the bed, `payment_covers(entity, "REST")`). The scope is `finds_no_bed`'s own, by trait: a subject with the coin
trait at a functional building that declares beds. The fatigue arrival (`building_arrival`) and the first execution of a REST (`building_services.no_bed_in_reach`) both ask it, so a broke subject that
reaches the inn ends its fatigue project with the existing typed WAY_CLOSED instead of resting rough at the inn tile every strategic cadence (the K2 v6 rows: urban_political s42, inn 20003, gold 0).
"""
from dataclasses import replace

from src.core.strategic import ProjectEnd, ProjectStatus
from src.core.updates import BiologicalUpdate, EntityUpdate
from src.engine.building_services import no_bed_in_reach, with_service
from src.engine.lodging import finds_no_bed, is_lodged
from src.engine.service_admission import PaymentLaw, no_bed_for
from src.engine.service_prices import REST_PRICE_GOLD
from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel, run


def _rest_update(entity_id):
    return {entity_id: EntityUpdate(entity_id=entity_id, biological=BiologicalUpdate(rest_pressure_delta=-30.0))}


def test_the_predicate_is_finds_no_bed_or_the_purse_half_within_finds_no_beds_own_scope():
    k = kernel([hero(1, REACH[0], gold=0, action=None), hero(2, REACH[1], gold=REST_PRICE_GOLD, action=None)], beds=2)
    try:
        st = k._state
        inn = st.buildings[INN_ID]
        broke, funded = st.entities[1], st.entities[2]
        assert not finds_no_bed(st, broke, inn) and no_bed_for(st, broke, inn)                       # a bed is free, the purse half refuses
        assert not no_bed_for(st, funded, inn)                                                          # with the price: the bed
        assert no_bed_for(st, replace(funded, inventory=replace(funded.inventory, gold=REST_PRICE_GOLD - 1)), inn)                  # one coin short: refused
        assert not no_bed_for(st, broke, inn, PaymentLaw.CLAMP)                                         # under CLAMP payment never closes a bed
    finally:
        k.shutdown()


def test_a_body_without_the_coin_trait_and_a_building_without_beds_are_unchanged():
    k = kernel([hero(1, REACH[0], gold=0, action=None)], beds=2)
    try:
        st = k._state
        wolf = replace(st.entities[1], kind="wolf")                                                      # authored without keeps_coin_and_trades: finds_no_bed does not refuse it, nor does the purse half
        assert not no_bed_for(st, wolf, st.buildings[INN_ID])
        assert not no_bed_in_reach(st, wolf) and with_service(_rest_update(1), wolf, "REST", st.tick, st) == _rest_update(1)
    finally:
        k.shutdown()
    bedless = kernel([hero(1, REACH[0], gold=0, action=None)], beds=0)
    try:
        st = bedless._state
        assert not no_bed_for(st, st.entities[1], st.buildings[INN_ID]) and no_bed_in_reach(st, st.entities[1]) is None     # a building that declares no beds is main's answer
    finally:
        bedless.shutdown()


def test_the_first_execution_of_a_rest_by_a_broke_subject_is_refused_like_a_full_inn_and_ends_the_fatigue_project_way_closed():
    k = kernel([hero(1, REACH[0], gold=0, action=None)], beds=2)
    try:
        st = k._state
        broke = hero(1, REACH[0], gold=0)                                                                  # a REST at the inn with its fatigue project
        assert no_bed_in_reach(st, broke) is not None
        out = with_service(_rest_update(1), broke, "REST", st.tick, st)[1]
        assert out.navigation.failure_reason == "NO_BED_FREE" and not out.resource_transfers and out.biological is None      # no rest, no charge, no claim
        assert out.strategic.projects_add_or_update[0].ended_by == ProjectEnd.WAY_CLOSED and out.strategic.current_project_id_set == ""
    finally:
        k.shutdown()


def test_a_broke_keeps_coin_subject_arriving_at_a_lodging_inn_ends_way_closed_with_no_rest_dispatched():
    k = kernel([hero(1, REACH[0], gold=0, action=None)], beds=2)                                         # stands on the reach tile with a fatigue project and no task: the arrival decides
    try:
        history = run(k, 25)
        e = k._state.entities[1]
        project = e.strategic.projects["p1"]
        assert project.status == ProjectStatus.ABANDONED and project.ended_by == ProjectEnd.WAY_CLOSED and e.strategic.current_project_id != "p1"      # the subject re-decides (here another project), it is not left on the ended one
        assert not is_lodged(e) and e.inventory.gold == 0
        assert all(snapshot[1][1][4] != "REST" for snapshot in history)                                  # no REST was ever dispatched for the broke subject
    finally:
        k.shutdown()


def test_a_subject_with_the_price_still_gets_the_rest_and_the_bed_at_arrival():
    k = kernel([hero(1, REACH[0], gold=REST_PRICE_GOLD, action=None)], beds=2)
    try:
        run(k, 25)
        e = k._state.entities[1]
        assert is_lodged(e) and e.inventory.gold == 0 and e.strategic.projects["p1"].ended_by is None     # the bed is granted and paid; the project is not ended
    finally:
        k.shutdown()
