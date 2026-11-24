"""F2 (divergence 2.220): a give-up record's anchor is in the state digest. An IN-TYPE change of the anchor (x, y) -> (x + 1, y) or (x, y + 1) moves `CanonicalStateHasher.get_hash`; the same anchor gives the same hash.

Why this file exists: tests/architecture/test_state_digest_covers_every_field.py perturbs a tuple by APPENDING an element ((1, 1) -> (1, 1, 1)), which no `Tuple[int, int]` can hold, and `GiveUpRecord.to_canonical` (lossless for the declared type) writes the two coordinates; the probe therefore reads the anchor as unhashed. This test pins what is true for the declared type."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.state import AuthoritativeState
from src.engine.checkpoint import CanonicalStateHasher


def _hash(anchor, tick=7):
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).build()
    e = replace(e, navigation=replace(e.navigation, giveup_records=(GiveUpRecord(anchor, tick),)))
    return CanonicalStateHasher.get_hash(AuthoritativeState(entities={1: e}, tick=3, seed=1))


def test_an_in_type_change_of_either_anchor_coordinate_moves_the_digest():
    base = _hash((4, 5))
    assert _hash((5, 5)) != base  # x + 1
    assert _hash((4, 6)) != base  # y + 1


def test_the_same_anchor_gives_the_same_digest_and_the_tick_is_hashed_too():
    assert _hash((4, 5)) == _hash((4, 5))
    assert _hash((4, 5), tick=8) != _hash((4, 5), tick=7)


def test_a_state_with_no_record_hashes_differently_from_one_holding_a_record():
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).build()
    empty = CanonicalStateHasher.get_hash(AuthoritativeState(entities={1: e}, tick=3, seed=1))
    assert empty != _hash((4, 5))
