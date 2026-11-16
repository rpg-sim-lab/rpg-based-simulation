# Compliance IDs: WORLD-GEN-TEST
"""WorldProceduralGenerator's resource pick does not depend on PYTHONHASHSEED.

The generator picks each resource node's type with a seeded RNG from a candidate list. That list used to be
built with ``list(set(...))``, so its order followed the process's string hash seed and the same seed and
intent gave a different world in each process (TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED).
Each case below runs the generator in a fresh subprocess per hash seed; only a real cross-process run can see this.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HASH_SEEDS = (0, 1, 2, 3)

# (seed, resource_density): small, mid and large node counts (16, 20, 30 nodes).
_INTENTS = ((12345, 0.8), (42, 1.0), (7, 1.5))

_GENERATE = """
import json, sys
from src.content.repository import CatalogRepository
from src.worldmodules.repository import WorldModuleRepository
from src.worldgeneration.generator import WorldProceduralGenerator
from src.worldgeneration.schema import GenerationIntentSpec
cat = CatalogRepository("data/content"); cat.load_all()
mod = WorldModuleRepository("data/world_modules"); mod.load_all()
out = {}
for seed, density in json.loads(sys.argv[1]):
    intent = GenerationIntentSpec(generation_id=f"gen_{seed}", seed=seed, target_world_size=(120, 120),
                                  resource_density=density, population_scale=1.2)
    spec = WorldProceduralGenerator(cat, mod).generate(intent).world_spec
    out[f"{seed}/{density}"] = [[r.id, r.resource_type, r.count, r.region] for r in spec.resources]
print("RESULT" + json.dumps(out, sort_keys=True))
"""

_CANDIDATE_ORDER = """
import json
from src.content.repository import CatalogRepository
cat = CatalogRepository("data/content"); cat.load_all()
print("RESULT" + json.dumps(list(set(r.resource_type for r in cat.resources.values()))))
"""


def _run(code: str, *args: str, hash_seed: int) -> object:
    env = {**os.environ, "PYTHONHASHSEED": str(hash_seed)}
    proc = subprocess.run([sys.executable, "-c", code, *args], cwd=_REPO_ROOT, env=env,
                          capture_output=True, text=True, timeout=300)
    assert proc.returncode == 0, proc.stderr[-2000:]
    line = next(ln for ln in proc.stdout.splitlines() if ln.startswith("RESULT"))
    return json.loads(line[len("RESULT"):])


@pytest.fixture(scope="module")
def worlds_by_hash_seed() -> dict[int, dict]:
    return {hs: _run(_GENERATE, json.dumps(_INTENTS), hash_seed=hs) for hs in _HASH_SEEDS}


def test_the_same_intent_gives_the_same_resource_types_in_every_hash_seed(worlds_by_hash_seed):
    reference = worlds_by_hash_seed[_HASH_SEEDS[0]]
    for hs in _HASH_SEEDS[1:]:
        for key, nodes in reference.items():
            other = worlds_by_hash_seed[hs][key]
            diff = [(a[0], a[1], b[1]) for a, b in zip(nodes, other) if a[1] != b[1]]
            assert not diff, f"intent {key}: PYTHONHASHSEED {hs} picks different resource types than {_HASH_SEEDS[0]}: {diff[:5]}"


def test_the_whole_generated_resource_list_is_identical_across_hash_seeds(worlds_by_hash_seed):
    reference = worlds_by_hash_seed[_HASH_SEEDS[0]]
    for hs in _HASH_SEEDS[1:]:
        assert worlds_by_hash_seed[hs] == reference, f"PYTHONHASHSEED {hs} generates a different resource list"


def test_the_candidate_set_really_has_a_hash_dependent_order_in_this_catalog():
    """Positive control: the old list(set(...)) expression gives different orders for these hash seeds,
    so a regression to it makes the two tests above fail rather than pass by chance."""
    orders = {tuple(_run(_CANDIDATE_ORDER, hash_seed=hs)) for hs in _HASH_SEEDS}
    assert len(orders) >= 2, "the catalog's resource types no longer vary in set order across hash seeds"
