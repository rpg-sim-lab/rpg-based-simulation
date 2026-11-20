"""``species_builder`` (PERC-02a): the checked start of a body build for the campaign rebuild and the scenario runner.

It sets the species as the body's kind (the one V2EntityBuilder(...).kind(...) write on those paths) and refuses a species in content with no usable sense profile, naming the site."""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.core.species import SenseProfileError
from src.entities.checked_builder import species_builder


@pytest.fixture()
def broken_wolf():
    """The warmed catalog with `wolf` (in content) declaring a sense profile that does not exist."""
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    repo = CatalogRepository("data/content")
    repo.load_all()
    repo.species["wolf"] = repo.species["wolf"].model_copy(update={"sense_profile": "nope"})
    configure_behavior_consumers(repo)
    try:
        yield
    finally:
        reset_behavior_consumers()


def test_species_builder_sets_the_kind_of_a_profiled_species():
    body = species_builder(7, "human", "test site").build()
    assert body.id == 7 and body.kind == "human"


def test_species_builder_refuses_an_in_content_species_with_no_usable_profile_naming_the_site(broken_wolf):
    with pytest.raises(SenseProfileError, match="test site 7"):
        species_builder(7, "wolf", "test site 7")


def test_species_builder_lets_an_unknown_kind_through_as_a_fixture():
    assert species_builder(8, "no_such_species_xyz", "test site").build().kind == "no_such_species_xyz"
