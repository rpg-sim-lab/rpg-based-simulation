# Compliance IDs: SOC-280
"""add_rejection_counts: the one sum rule shared by the apply and the SocialUpdate merge."""
from src.core.social_counts import add_rejection_counts


def test_empty_base_and_empty_increment():
    assert add_rejection_counts({}, {}) == {}


def test_empty_increment_keeps_every_base_count():
    assert add_rejection_counts({10: 3, 11: 1}, {}) == {10: 3, 11: 1}


def test_empty_base_takes_the_increment():
    assert add_rejection_counts({}, {10: 1}) == {10: 1}


def test_disjoint_keys_sit_side_by_side():
    assert add_rejection_counts({10: 3}, {12: 1}) == {10: 3, 12: 1}


def test_overlapping_keys_add():
    assert add_rejection_counts({10: 3, 11: 1}, {10: 2}) == {10: 5, 11: 1}


def test_the_base_and_the_increment_are_not_mutated():
    base, inc = {10: 3}, {10: 1, 12: 1}
    out = add_rejection_counts(base, inc)
    assert out == {10: 4, 12: 1} and base == {10: 3} and inc == {10: 1, 12: 1}
