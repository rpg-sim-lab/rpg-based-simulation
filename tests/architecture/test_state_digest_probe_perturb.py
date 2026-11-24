"""``perturb`` keeps a fixed-arity tuple's length (TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE).

``to_canonical`` writes only the declared positions of ``Tuple[int, int]``, so appending an element is out of type and made a hashed field read as unhashed.
"""
from __future__ import annotations

import enum
from typing import FrozenSet, Optional, Set, Tuple

import pytest

from tests.architecture import state_digest_probe as probe


def test_a_fixed_arity_tuple_keeps_its_length_and_differs_in_one_element():
    new, inserted = probe.perturb((4, 5), Tuple[int, int])
    assert len(new) == 2 and sum(a != b for a, b in zip(new, (4, 5))) == 1 and inserted is None


def test_a_fixed_arity_tuple_uses_each_positions_own_hint():
    new, _ = probe.perturb((4, "a"), Tuple[int, str])
    assert isinstance(new[0], int) and isinstance(new[1], str) and new != (4, "a")


def test_an_optional_fixed_arity_tuple_is_still_fixed_arity():
    new, _ = probe.perturb((4, 5), Optional[Tuple[int, int]])
    assert len(new) == 2 and new != (4, 5)


def test_a_variadic_tuple_still_grows_by_one():
    new, _ = probe.perturb((1, 2), Tuple[int, ...])
    assert len(new) == 3 and new[:2] == (1, 2)


def test_a_bare_tuple_still_grows_by_one():
    new, _ = probe.perturb((1, 2), tuple)
    assert len(new) == 3 and new[:2] == (1, 2)


def test_a_hint_of_another_length_is_not_taken_for_fixed_arity():
    new, _ = probe.perturb((1, 2, 3), Tuple[int, int])
    assert len(new) == 4


def test_a_fixed_arity_tuple_with_no_changeable_position_raises_cannot(monkeypatch):
    def refuse(value, hint):
        raise probe.Cannot("no")

    monkeypatch.setattr(probe, "perturb", refuse)
    with pytest.raises(probe.Cannot):
        probe._perturb_fixed_arity((1, 2), Tuple[int, int])


class _Kind(enum.Enum):
    A = 1
    B = 2
    C = 3


class _Lone(enum.Enum):
    ONLY = 1


def test_a_frozenset_of_enum_already_holding_the_first_member_changes():
    value = frozenset({_Kind.A})
    new, inserted = probe.perturb(value, FrozenSet[_Kind])
    assert new != value and isinstance(new, frozenset) and _Kind.A in new and len(new) == 2 and inserted is None  # enum members are not records, so nothing to probe


def test_a_set_holding_every_enum_member_but_the_first_still_changes():
    value = {_Kind.B, _Kind.C}
    new, _ = probe.perturb(value, Set[_Kind])
    assert new != value and isinstance(new, set)


def test_a_single_member_enum_set_changes_by_removal():
    value = frozenset({_Lone.ONLY})
    new, inserted = probe.perturb(value, FrozenSet[_Lone])
    assert new == frozenset() and inserted is None


def test_an_empty_set_grows_by_one():
    new, _ = probe.perturb(frozenset(), FrozenSet[int])
    assert len(new) == 1


def test_an_ordinary_non_colliding_set_keeps_its_union_behaviour():
    new, _ = probe.perturb({5, 6}, Set[int])
    assert new == {1, 5, 6}


def test_a_set_whose_synthesized_element_collides_gets_a_different_element():
    new, _ = probe.perturb({1, 5}, Set[int])  # synthesize(int) is 1, already held
    assert new != {1, 5} and 1 in new and len(new) == 3


def test_a_full_set_with_no_new_member_loses_one_deterministically():
    value = frozenset(_Kind)
    first, _ = probe.perturb(value, FrozenSet[_Kind])
    again, _ = probe.perturb(value, FrozenSet[_Kind])
    assert first == again and len(first) == 2 and first < value
