"""``perturb`` keeps a fixed-arity tuple's length (TCK-20261122-STATE-DIGEST-PROBE-PERTURBS-FIXED-ARITY-TUPLES-IN-PLACE).

``to_canonical`` writes only the declared positions of ``Tuple[int, int]``, so appending an element is out of type and made a hashed field read as unhashed.
"""
from __future__ import annotations

from typing import Optional, Tuple

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
