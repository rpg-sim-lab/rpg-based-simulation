"""PERC-02a: a species file with ``sense_profile: null`` raises the typed SenseProfileError naming the species at catalog load, not a bare ``KeyError`` later."""
from __future__ import annotations

import shutil

import pytest

from src.content.repository import CatalogRepository
from src.core.species import SenseProfileError


def test_catalog_load_of_a_null_sense_profile_names_the_species(tmp_path):
    content = tmp_path / "content"
    shutil.copytree("data/content", content)
    species = content / "living" / "species.yaml"
    lines = species.read_text().split("\n")
    at = next(i for i, line in enumerate(lines) if line.strip() == '- id: "wolf"')
    sense = next(i for i in range(at, len(lines)) if lines[i].strip().startswith("sense_profile:"))
    lines[sense] = "  sense_profile: null"
    species.write_text("\n".join(lines))
    with pytest.raises(SenseProfileError, match="'wolf'"):
        CatalogRepository(str(content)).load_all()
