"""The name-switch scan (tools/test_architecture/name_switch_scan.py) keeps seeing a name switch when the name is read through the occupation label (M1 step 3, rpg-designer ruling on the
ratchet: an occupation label compared to a literal in a decision path IS a name switch, decision 50). Without this, moving a compare from `kind` to `occupation` would silently blind the
retirement ratchet. A `species_of(x)` result compared to a name literal is also a name switch (decision 46).
"""
from __future__ import annotations

import pytest

from tools.test_architecture import name_switch_scan as scan

pytestmark = pytest.mark.architecture


def _names(source: str):
    return [(s.name, s.shape) for s in scan.scan_source(source, "src/world/example.py")]


def test_an_occupation_of_call_compared_to_a_literal_is_a_switch():
    assert _names("def f(e):\n    return occupation_of(e) == 'world_boss'\n") == [("'world_boss'", "compare")]


def test_a_local_assigned_from_occupation_of_then_compared_is_a_switch():
    src = "def f(e):\n    label = (occupation_of(e) or '').lower()\n    if label in ('guard', 'sentinel'):\n        return 1\n"
    assert {n for n, _ in _names(src)} == {"'guard'", "'sentinel'"}


def test_an_occupation_attribute_compared_to_a_literal_is_a_switch_on_any_receiver():
    assert _names("def f(s):\n    return s.identity.occupation == 'stronghold'\n") == [("'stronghold'", "compare")]


def test_a_compare_of_two_resolved_occupations_is_not_a_switch():
    assert _names("def f(a, b):\n    return occupation_of(a) == occupation_of(b)\n") == []


def test_a_species_of_call_compared_to_a_literal_is_a_switch():
    assert _names("def f(e):\n    return species_of(e) == 'goblin'\n") == [("'goblin'", "compare")]


def test_a_local_assigned_from_species_of_then_compared_is_a_switch():
    assert _names("def f(e):\n    sp = species_of(e)\n    return sp != 'wolf'\n") == [("'wolf'", "compare")]


def test_reading_a_content_relation_keyed_by_species_id_is_not_a_switch():
    assert _names("def f(e, table):\n    return table[species_of(e)]\n") == []


def test_a_compare_of_two_resolved_species_is_not_a_switch():
    assert _names("def f(a, b):\n    return species_of(a) == species_of(b)\n") == []
