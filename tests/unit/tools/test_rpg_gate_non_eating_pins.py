"""TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED, the testing-side pins: what the baseline and candidate tooling must still do once a kind
group is declared non-eating and R2 is scoped by ``when``. They sit beside ``test_rpg_gate_non_eating.py`` (the declaration, the child arguments, the report line) and add the
three seams it leaves open: the R2 scope is keyed on the (world, group) pair and fails closed, the candidate never carries the document's ``not_applicable`` key into the
baseline, and the omission of the food rows for the declared group is uniform across seeds (a seed that still emits one is refused, never imputed)."""
from __future__ import annotations

import copy

import pytest

from src.ai.goals.kind_group import NO_DIET
from tests.unit.tools.test_rpg_gate_candidate import SEEDS, _build, _config, _pooled_doc, _seed_doc, _write
from tools.test_architecture import rpg_gate_baseline as rgb
from tools.test_architecture import rpg_gate_candidate as cand

R2 = rgb.StopLine("R2", "O2.seeds_with_survivors", "*", min=1.0, when_row="O2.t0_population", when_min=1.0)


def _row(row_id: str, world: str, group: str, value) -> dict:
    return {"id": row_id, "class": "outcome", "scope": "pooled", "world": world, "group": group, "value": value, "floor": 1.0}


# ---- R2's scope is keyed on the (world, group) pair, and a missing or valueless scope row applies the line ---------------------------------------------------------------

def test_a_scope_row_of_another_world_does_not_scope_the_line_out():
    rows = [_row("O2.seeds_with_survivors", "crowded", "none", 0.0), _row("O2.t0_population", "frontier", "none", 0.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == ["R2"]


def test_a_scope_row_of_another_group_does_not_scope_the_line_out():
    rows = [_row("O2.seeds_with_survivors", "w", "meat", 0.0), _row("O2.t0_population", "w", "none", 0.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == ["R2"]


def test_a_scope_row_without_a_value_applies_the_line():
    rows = [_row("O2.seeds_with_survivors", "w", "meat", 0.0), _row("O2.t0_population", "w", "meat", None)]
    assert rgb.stop_lines_crossed(rows, [R2]) == ["R2"]


def test_a_start_population_exactly_at_the_scope_minimum_applies_the_line():
    rows = [_row("O2.seeds_with_survivors", "w", "meat", 0.0), _row("O2.t0_population", "w", "meat", 1.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == ["R2"]


def test_the_scope_never_hides_a_group_that_is_above_the_line():
    rows = [_row("O2.seeds_with_survivors", "w", "meat", 3.0), _row("O2.t0_population", "w", "meat", 4.0)]
    assert rgb.stop_lines_crossed(rows, [R2]) == []


# ---- the candidate ---------------------------------------------------------------------------------------------------------------------------------------------------

def _none_rows(seed: int, *, with_food: bool) -> list:
    base = [{"id": "O2.population", "class": "outcome", "scope": "run", "group": "none", "tick": 100, "value": float(seed), "k": 2.0, "floor": 1.0}]
    food = [{"id": "O1.at_risk", "class": "outcome", "scope": "run", "group": "none", "tick": 100, "value": 0.0, "k": 2.0, "floor": 1.0}]
    return base + (food if with_food else [])


def _docs(*, food_on=(), not_applicable=True) -> dict:
    docs = {}
    for seed in SEEDS:
        doc = _seed_doc(seed)
        doc["metrics"] += _none_rows(seed, with_food=seed in food_on)
        if not_applicable:
            doc["not_applicable"] = {"none": ["O1.starved", "O1.at_risk", "O4.accepted"]}
        docs[("w", seed)] = doc
    docs[("w", None)] = _pooled_doc()
    return docs


def test_the_candidate_does_not_carry_the_documents_not_applicable_key_into_the_baseline(tmp_path):
    result = _build(_write(tmp_path / "docs", _docs()), config=_config())
    assert "not_applicable" not in result and all("not_applicable" not in row for row in result["metrics"])
    assert not any(row["id"] == "O1.at_risk" and row["group"] == "none" for row in result["metrics"])
    assert any(row["id"] == "O2.population" and row["group"] == "none" for row in result["metrics"])


def test_a_declared_group_with_no_food_row_on_any_seed_builds_the_same_candidate_with_or_without_the_document_key(tmp_path):
    with_key = _build(_write(tmp_path / "a", _docs()), config=_config())
    without = _build(_write(tmp_path / "b", _docs(not_applicable=False)), config=_config())
    assert cand.dump_candidate(with_key) == cand.dump_candidate(without)


def test_a_seed_that_still_emits_the_food_row_for_the_declared_group_is_refused_not_imputed(tmp_path):
    with pytest.raises(cand.CandidateRefused, match=r"absent from seed"):
        _build(_write(tmp_path / "docs", _docs(food_on=(1,))), config=_config())


def test_a_food_row_on_every_seed_for_the_group_is_a_row_the_candidate_keeps(tmp_path):
    result = _build(_write(tmp_path / "docs", _docs(food_on=SEEDS)), config=_config())
    assert any(row["id"] == "O1.at_risk" and row["group"] == "none" for row in result["metrics"])


def test_the_candidate_inputs_are_not_mutated_by_the_build(tmp_path):
    docs = _docs()
    before = copy.deepcopy(docs)
    _build(_write(tmp_path / "docs", docs), config=_config())
    assert docs == before


def test_the_declarable_non_eating_group_is_the_engines_no_diet_group():
    assert rgb.NON_EATING_GROUPS == (NO_DIET,)
