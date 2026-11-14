#!/usr/bin/env python3
"""Build the website wiki's World Knowledge pages from the repository's stored data.

The wiki is a view, not a second copy: every fact page is rendered from a source file in the
repository at build time and never committed (owner rule, #715 6789779149). The sources:

- docs/world_rules/<area>/<family>.md: each rule's ID, title and quoted statement.
- registries/mechanisms.yaml and registries/system_registry.jsonl: mechanisms by layer.
- registries/mechanism_causal_edges.yaml: which mechanism feeds which.
- data/content/**.yaml: the content catalog, as stored (no filtering).
- registries/world_glossary.jsonl: world terms (the page is skipped while the file is absent or empty).

Only presentation lives here: page layout, column choice, plain labels for stored enum values.
A rule, a mechanism or a content value is never written in this file.

Usage:
    python3 website/scripts/generate_wiki.py                # write into website/wiki/world-knowledge/
    python3 website/scripts/generate_wiki.py --out DIR      # write elsewhere (tests)
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised only on a machine without PyYAML
    sys.exit("generate_wiki.py needs PyYAML (pip install pyyaml); it ships with the project's Python environment.")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = REPO_ROOT / "website" / "wiki" / "world-knowledge"
SOURCE_URL = "https://github.com/rpg-sim-lab/rpg-based-simulation/blob/main/"

# The generated folders under world-knowledge/. Only these are cleared and rewritten; the
# hand-written landing page (world-knowledge/index.md) is never touched.
GENERATED_DIRS = ("laws", "mechanisms", "catalog", "glossary")

WORLD_RULES_DIR = "docs/world_rules"
WORLD_RULES_SKIP = {"review-exports", "scenarios"}
MECHANISMS = "registries/mechanisms.yaml"
SYSTEMS = "registries/system_registry.jsonl"
CAUSAL_EDGES = "registries/mechanism_causal_edges.yaml"
CONTENT_DIR = "data/content"
WORLD_GLOSSARY = "registries/world_glossary.jsonl"

_RULE_HEADING = re.compile(r"^## ([A-Z]+-\d+[A-Za-z]?) — (.+)$")
_FAMILY_TITLE = re.compile(r"^# World Rule Family: (.+)$")

# Plain labels for the mechanism registry's own `state` vocabulary (registries/mechanisms.yaml header).
STATE_LABELS = {
    "done": "Active",
    "partial": "Partly active",
    "gated": "Built, switched off by default",
    "orphan": "Built, not connected yet",
    "gap": "Not built yet",
    "skeleton": "Placeholder only",
}
CADENCE_LABELS = {
    "per_tick": "every tick",
    "daily": "once a day",
    "slow": "over many days",
    "rare": "rarely",
}
LAYER_INTRO = {
    "entity": "What a single being does.",
    "group": "What a party, pack or crew does together.",
    "faction": "What a faction or settlement does as a whole.",
    "region": "How a region changes over time.",
    "world": "Events that touch the whole world.",
}


# ── small helpers ──────────────────────────────────────────────────────────────────────────


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def _load_yaml(rel: str) -> object:
    return yaml.safe_load(_read(rel))


def _humanize(slug: str) -> str:
    words = re.split(r"[_\-]+", slug)
    return " ".join(words).strip().capitalize()


def _cell(text: object) -> str:
    """Make a value safe inside a Markdown table cell and in CommonMark ('md') mode."""
    value = str(text).replace("\n", " ").replace("|", "\\|")
    return value.replace("<", "&lt;").replace(">", "&gt;").replace("{", "&#123;").replace("}", "&#125;")


def _text(text: str) -> str:
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("{", "&#123;").replace("}", "&#125;")


def _frontmatter(title: str, sources: Iterable[str], position: int | None = None, slug: str | None = None) -> str:
    lines = ["---", f"title: {json.dumps(title)}"]
    if position is not None:
        lines.append(f"sidebar_position: {position}")
    if slug is not None:
        lines.append(f"slug: {slug}")
    source_list = sorted(set(sources))
    lines.append("source_docs:")
    lines.extend(f"  - {src}" for src in source_list)
    if len(source_list) == 1:
        lines.append(f"custom_edit_url: {SOURCE_URL}{source_list[0]}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def _source_note(sources: Iterable[str]) -> str:
    links = ", ".join(f"[`{src}`]({SOURCE_URL}{src})" for src in sorted(set(sources)))
    return f"\n---\n\n*This page is generated from {links} each time the site is built. Change the source, not this page.*\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _category(path: Path, label: str, position: int, description: str, slug: str | None = None) -> None:
    link: dict = {"type": "generated-index", "description": description}
    if slug:
        link["slug"] = slug
    payload = {"label": label, "position": position, "link": link}
    _write(path / "_category_.json", json.dumps(payload, indent=2) + "\n")


# ── Laws of the World (docs/world_rules) ───────────────────────────────────────────────────


def parse_rule_family(text: str) -> tuple[str | None, list[dict]]:
    """Return (family title, rules); each rule is {id, title, statement} from the stored file."""
    lines = text.split("\n")
    title = None
    rules: list[dict] = []
    for index, line in enumerate(lines):
        title_match = _FAMILY_TITLE.match(line)
        if title_match and title is None:
            title = title_match.group(1).strip()
        heading = _RULE_HEADING.match(line)
        if not heading:
            continue
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        quoted: list[str] = []
        while cursor < len(lines) and lines[cursor].startswith(">"):
            quoted.append(lines[cursor][1:].strip())
            cursor += 1
        rules.append({"id": heading.group(1), "title": heading.group(2).strip(), "statement": " ".join(quoted).strip()})
    return title, rules


def build_laws(out: Path) -> int:
    """Write one page per world-rule family, grouped by area; return the page count."""
    root = REPO_ROOT / WORLD_RULES_DIR
    laws = out / "laws"
    _category(laws, "Laws of the world", 1, "The rules every world follows, grouped by area. Each page lists its rules with their short statement.", "/world-knowledge/laws")
    count = 0
    areas = sorted(p for p in root.iterdir() if p.is_dir() and p.name not in WORLD_RULES_SKIP)
    for area_position, area in enumerate(areas, start=1):
        area_dir = laws / area.name
        _category(area_dir, _humanize(area.name), area_position, f"Rule families in the {_humanize(area.name).lower()} area.", f"/world-knowledge/laws/{area.name}")
        for family_position, family_file in enumerate(sorted(area.glob("*.md")), start=1):
            rel = family_file.relative_to(REPO_ROOT).as_posix()
            family_title, rules = parse_rule_family(family_file.read_text(encoding="utf-8"))
            if not rules:
                continue
            title = family_title or _humanize(family_file.stem)
            body = [f"# {_text(title)}\n"]
            body.append(f"{len(rules)} rules. Each heading is the rule's ID and name; the quoted text is its statement.\n")
            for rule in rules:
                body.append(f"## {rule['id']} — {_text(rule['title'])}\n")
                if rule["statement"]:
                    body.append(f"> {_text(rule['statement'])}\n")
            body.append(_source_note([rel]))
            # An explicit slug: a family file named like its area folder would otherwise become the
            # area's index and collide with the area's generated-index page.
            slug = f"/world-knowledge/laws/{area.name}/{family_file.stem}"
            _write(area_dir / f"{family_file.stem}.md", _frontmatter(title, [rel], family_position, slug) + "\n".join(body))
            count += 1
    return count


# ── How the world runs (registries/mechanisms.yaml) ────────────────────────────────────────


class MechanismData:
    """The mechanism registry, the system registry and the causal edges, read once."""

    sources = (MECHANISMS, SYSTEMS, CAUSAL_EDGES)

    def __init__(self) -> None:
        registry = _load_yaml(MECHANISMS)
        self.layers: dict = registry["layers"]
        self.mechanisms: list[dict] = registry["mechanisms"]
        self.systems: dict[str, str] = {}
        for line in _read(SYSTEMS).splitlines():
            if line.strip():
                row = json.loads(line)
                self.systems[row["system"]] = row["note"]
        self.feeds: dict[str, list[str]] = {}
        for edge in (_load_yaml(CAUSAL_EDGES) or {}).get("edges") or []:
            self.feeds.setdefault(edge["producer_mechanism_id"], []).append(edge["consumer_mechanism_id"])
        self.layer_of = {m["id"]: m["layer"] for m in self.mechanisms}
        self.ordered_layers = sorted(self.layers, key=lambda name: self.layers[name]["rank"])

    def cadence(self, layer: str) -> str:
        """Plain words for how often a layer runs."""
        raw = self.layers[layer]["cadence"]
        return CADENCE_LABELS.get(raw, raw)

    def members(self, layer: str) -> list[dict]:
        """The mechanisms in one layer, by id."""
        return sorted((m for m in self.mechanisms if m["layer"] == layer), key=lambda m: m["id"])

    def link(self, mechanism_id: str, here: str) -> str:
        """A link to a mechanism's heading, on this layer page or another."""
        layer = self.layer_of.get(mechanism_id)
        label = _humanize(mechanism_id)
        if layer is None:
            return label
        target = "" if layer == here else f"./{layer}.md"
        return f"[{label}]({target}#{_anchor(mechanism_id)})"


def _anchor(mechanism_id: str) -> str:
    return mechanism_id.replace("_", "-")


def _mechanisms_overview(data: MechanismData) -> str:
    lines = ["# How the world runs\n"]
    lines.append("The world is driven by mechanisms. Each belongs to one layer, and each layer runs at its own pace.\n")
    lines.append("| Layer | Runs | Mechanisms | Active |\n|---|---|---|---|")
    for layer in data.ordered_layers:
        members = data.members(layer)
        active = sum(1 for m in members if m["state"] == "done")
        lines.append(f"| [{_humanize(layer)}](./{layer}.md) | {data.cadence(layer)} | {len(members)} | {active} |")
    lines.append("\n## Systems\n")
    lines.append("Every mechanism also belongs to one or more systems.\n")
    lines.append("| System | Covers | Mechanisms |\n|---|---|---|")
    for system, note in data.systems.items():
        count = sum(1 for m in data.mechanisms if system in (m.get("systems") or []))
        lines.append(f"| {_humanize(system)} | {_cell(note)} | {count} |")
    lines.append("\n## What the states mean\n")
    lines.append("| State | Mechanisms |\n|---|---|")
    for state, label in STATE_LABELS.items():
        lines.append(f"| {label} | {sum(1 for m in data.mechanisms if m['state'] == state)} |")
    lines.append(_source_note(data.sources))
    return "\n".join(lines)


def _mechanism_entry(data: MechanismData, mechanism: dict, layer: str) -> str:
    lines = [f"## {_humanize(mechanism['id'])} {{#{_anchor(mechanism['id'])}}}\n"]
    summary = mechanism.get("summary")
    if summary:
        lines.append(f"{_text(str(summary))}\n")
    facts = [f"- **State:** {STATE_LABELS.get(mechanism['state'], mechanism['state'])}"]
    facts.append(f"- **Systems:** {', '.join(_humanize(s) for s in mechanism.get('systems') or []) or 'none'}")
    needs = mechanism.get("depends_on") or []
    if needs:
        facts.append(f"- **Needs:** {', '.join(data.link(dep, layer) for dep in needs)}")
    fed = data.feeds.get(mechanism["id"]) or []
    if fed:
        facts.append(f"- **Feeds:** {', '.join(data.link(dep, layer) for dep in fed)}")
    lines.append("\n".join(facts) + "\n")
    return "\n".join(lines)


def build_mechanisms(out: Path) -> int:
    """Write the mechanism overview and one page per layer; return the page count."""
    data = MechanismData()
    section = out / "mechanisms"
    _category(section, "How the world runs", 2, "The mechanisms that move the world, from a single being up to the whole world.")
    _write(section / "index.md", _frontmatter("How the world runs", data.sources, 0) + _mechanisms_overview(data))
    for position, layer in enumerate(data.ordered_layers, start=1):
        body = [f"# {_humanize(layer)} layer\n", f"{LAYER_INTRO.get(layer, '')} This layer runs {data.cadence(layer)}.\n"]
        body.extend(_mechanism_entry(data, mechanism, layer) for mechanism in data.members(layer))
        body.append(_source_note(data.sources))
        page = _frontmatter(f"{_humanize(layer)} layer", data.sources, position) + "\n".join(body)
        _write(section / f"{layer}.md", page)
    return len(data.ordered_layers) + 1


# ── Who and what is in the world (data/content) ────────────────────────────────────────────

Column = tuple[str, Callable[[dict], object]]


class Catalog:
    """Display-name lookups across content families, so a reference shows a name, not an id."""

    def __init__(self) -> None:
        self.families: dict[str, list[dict]] = {}

    def load(self, family: str) -> list[dict]:
        """The entries of one content family (cached)."""
        if family not in self.families:
            data = _load_yaml(f"{CONTENT_DIR}/{family}.yaml") or []
            self.families[family] = data if isinstance(data, list) else []
        return self.families[family]

    def name(self, family: str, entry_id: str) -> str:
        """The display name of an entry, or its humanized id."""
        for entry in self.load(family):
            if entry.get("id") == entry_id:
                return str(entry.get("display_name") or _humanize(entry_id))
        return _humanize(entry_id)

    def names(self, family: str, ids: Iterable[str] | None) -> str:
        """Display names for a list of ids, comma-joined."""
        return ", ".join(self.name(family, i) for i in ids or [])

    def thing(self, entry_id: str) -> str:
        """The display name of an item, resource or material id."""
        for family in ("world/items", "world/resources", "foundation/materials"):
            for entry in self.load(family):
                if entry.get("id") == entry_id:
                    return str(entry.get("display_name") or _humanize(entry_id))
        return _humanize(entry_id)

    def counted(self, mapping: dict | None) -> str:
        """An {id: count} mapping as "2 × Iron Ore, 1 × Wood"."""
        return ", ".join(f"{count} × {self.thing(key)}" for key, count in (mapping or {}).items())


def _catalog_pages(cat: Catalog) -> list[dict]:
    def plain(value: object) -> str:
        return _humanize(str(value)) if value not in (None, "") else ""

    def listing(values: Iterable[object] | None) -> str:
        return ", ".join(plain(v) for v in values or [])

    return [
        {
            "slug": "creatures-and-people", "title": "Creatures and people", "family": "entities/entity_archetypes",
            "intro": "Every kind of being a world can spawn, with the species, faction and role it starts with.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Species", lambda e: cat.name("living/species", e.get("species", ""))),
                ("Faction", lambda e: cat.name("social/factions", e.get("faction", ""))),
                ("Role", lambda e: cat.name("social/roles", e.get("role", ""))),
                ("Traits", lambda e: cat.names("foundation/traits", e.get("traits"))),
            ],
        },
        {
            "slug": "groups", "title": "Groups that appear together", "family": "entities/populations",
            "intro": "Packs, parties and households that a world places together.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Members", lambda e: ", ".join(f"{n} × {cat.name('entities/entity_archetypes', k)}" for k, n in (e.get("members") or {}).items())),
                ("Usually found in", lambda e: listing(e.get("preferred_regions"))),
            ],
        },
        {
            "slug": "species", "title": "Species", "family": "living/species",
            "intro": "What each species is like before any training or role.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Intelligence", lambda e: plain(e.get("intelligence_tier"))),
                ("Power", lambda e: plain(e.get("power"))),
                ("Wits", lambda e: plain(e.get("wits"))),
                ("Natural traits", lambda e: cat.names("foundation/traits", e.get("natural_traits"))),
                ("Can take roles", lambda e: cat.names("social/roles", e.get("compatible_roles"))),
            ],
        },
        {
            "slug": "factions", "title": "Factions", "family": "social/factions",
            "intro": "The sides beings belong to, and how each side sees the others.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("About", lambda e: e.get("description", "")),
                ("Stance", lambda e: plain(e.get("alignment_bucket"))),
                ("Role in the world", lambda e: plain(e.get("influence_role"))),
                ("Common species", lambda e: cat.names("living/species", e.get("common_species"))),
            ],
            "extra": "relationships",
        },
        {
            "slug": "roles", "title": "Roles", "family": "social/roles",
            "intro": "The jobs and callings a being can hold.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Kind", lambda e: plain(e.get("role_family"))),
                ("Needs traits", lambda e: cat.names("foundation/traits", e.get("compatible_traits"))),
            ],
        },
        {
            "slug": "traits", "title": "Traits", "family": "foundation/traits",
            "intro": "Lasting qualities that shape what a being can do and how it behaves.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Meaning", lambda e: e.get("description", "")),
            ],
        },
        {
            "slug": "attributes", "title": "Attributes", "family": "foundation/attributes",
            "intro": "The core qualities every being is measured on.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Meaning", lambda e: e.get("description", "")),
            ],
        },
        {
            "slug": "biomes", "title": "Biomes", "family": "world/biomes",
            "intro": "The kinds of land a world is made of.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Danger", lambda e: e.get("danger_level", "")),
                ("Terrain", lambda e: cat.names("world/terrain", e.get("terrain_mix"))),
                ("Common materials", lambda e: cat.names("foundation/materials", e.get("common_materials"))),
                ("Usual factions", lambda e: cat.names("social/factions", e.get("default_factions"))),
            ],
        },
        {
            "slug": "terrain", "title": "Terrain", "family": "world/terrain",
            "intro": "Ground types and how they affect movement and fighting.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Movement cost", lambda e: f"×{e['move_cost_multiplier']}" if "move_cost_multiplier" in e else ""),
                ("Gives cover", lambda e: "yes" if e.get("gives_cover") else ""),
                ("High ground", lambda e: "yes" if e.get("high_ground") else ""),
            ],
        },
        {
            "slug": "ecologies", "title": "Ecologies", "family": "world/ecologies",
            "intro": "Which life, resources and factions belong together in a place.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Biomes", lambda e: cat.names("world/biomes", e.get("biomes"))),
                ("Dominant factions", lambda e: cat.names("social/factions", e.get("dominant_factions"))),
                ("Groups", lambda e: cat.names("entities/populations", e.get("populations"))),
                ("Resources", lambda e: cat.names("world/resources", e.get("resources"))),
            ],
        },
        {
            "slug": "resources", "title": "Resources", "family": "world/resources",
            "intro": "What can be gathered from the land, and where it grows.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Gives", lambda e: cat.name("foundation/materials", e.get("material", ""))),
                ("Found in", lambda e: cat.names("world/biomes", e.get("preferred_biomes"))),
                ("Regrows", lambda e: plain(e.get("regrowth_mode"))),
            ],
        },
        {
            "slug": "materials", "title": "Materials", "family": "foundation/materials",
            "intro": "The raw stuff things are made of.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Kind", lambda e: listing(e.get("categories"))),
            ],
        },
        {
            "slug": "items", "title": "Items", "family": "world/items",
            "intro": "Everything a being can carry, use, eat or trade.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Kind", lambda e: listing(e.get("categories"))),
                ("Rarity", lambda e: plain(e.get("rarity"))),
                ("Value", lambda e: e.get("base_value", "")),
                ("Made from", lambda e: cat.names("foundation/materials", e.get("materials"))),
            ],
        },
        {
            "slug": "recipes", "title": "Recipes", "family": "world/recipes",
            "intro": "What can be made, from what, and where.",
            "columns": [
                ("Makes", lambda e: cat.counted(e.get("outputs"))),
                ("From", lambda e: cat.counted(e.get("ingredients"))),
                ("Where", lambda e: cat.name("world/services", e.get("required_service", ""))),
                ("Gold", lambda e: e.get("gold_cost", "")),
            ],
        },
        {
            "slug": "buildings", "title": "Buildings", "family": "world/buildings",
            "intro": "The buildings a settlement can have and what each offers.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Offers", lambda e: cat.name("world/services", e.get("service_profile_id", ""))),
                ("Beds", lambda e: e.get("beds", "")),
                ("Hires for pay", lambda e: "yes" if e.get("hires_for_pay") else ""),
            ],
        },
        {
            "slug": "services", "title": "Services", "family": "world/services",
            "intro": "What a building can do for a visitor: sell, heal, craft.",
            "columns": [
                ("Name", lambda e: e.get("display_name") or _humanize(e["id"])),
                ("Kind", lambda e: plain(e.get("service_type"))),
                ("Sells", lambda e: ", ".join(cat.thing(i) for i in e.get("provided_items") or [])),
                ("Crafts", lambda e: ", ".join(cat.counted((cat_recipe(cat, r) or {}).get("outputs")) or _humanize(r) for r in e.get("provided_recipes") or [])),
            ],
        },
    ]


def cat_recipe(cat: Catalog, recipe_id: str) -> dict | None:
    """The recipe entry with this id, if any."""
    for entry in cat.load("world/recipes"):
        if entry.get("id") == recipe_id:
            return entry
    return None


def _relationship_table(cat: Catalog) -> list[str]:
    rows = cat.load("social/faction_relationships")
    lines = ["\n## How factions see each other\n", "| Faction | Towards | Relationship | Feelings |", "|---|---|---|---|"]
    for row in rows:
        axes = ", ".join(f"{_humanize(k).lower()}: {_humanize(str(v)).lower()}" for k, v in (row.get("axes") or {}).items())
        lines.append(
            f"| {_cell(cat.name('social/factions', row.get('source_faction', '')))} "
            f"| {_cell(cat.name('social/factions', row.get('target_faction', '')))} "
            f"| {_cell(_humanize(row.get('relationship_model', '')))} | {_cell(axes)} |"
        )
    return lines


def build_catalog(out: Path) -> int:
    """Write one table page per content family; return the page count."""
    cat = Catalog()
    section = out / "catalog"
    _category(section, "Who and what is in the world", 3, "The content a world is built from, as stored in the content catalog.", "/world-knowledge/catalog")
    pages = _catalog_pages(cat)
    for position, page in enumerate(pages, start=1):
        rel = f"{CONTENT_DIR}/{page['family']}.yaml"
        sources = [rel]
        entries = cat.load(page["family"])
        columns: list[Column] = page["columns"]
        body = [f"# {page['title']}\n", f"{page['intro']} {len(entries)} entries.\n"]
        body.append("| " + " | ".join(header for header, _ in columns) + " |")
        body.append("|" + "---|" * len(columns))
        for entry in entries:
            body.append("| " + " | ".join(_cell(getter(entry)) for _, getter in columns) + " |")
        if page.get("extra") == "relationships":
            body.extend(_relationship_table(cat))
            sources.append(f"{CONTENT_DIR}/social/faction_relationships.yaml")
        body.append(_source_note(sources))
        _write(section / f"{page['slug']}.md", _frontmatter(page["title"], sources, position) + "\n".join(body))
    return len(pages)


# ── Glossary (registries/world_glossary.jsonl) ─────────────────────────────────────────────


def build_glossary(out: Path) -> int:
    """Write the Glossary page from the world glossary registry; 0 while it is absent or empty."""
    path = REPO_ROOT / WORLD_GLOSSARY
    if not path.exists():
        return 0
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        return 0
    section = out / "glossary"
    body = ["# Glossary\n", "The terms used across this wiki. Each one links to the law it comes from.\n"]
    body.append("| Term | Meaning | Defined in |\n|---|---|---|")
    for row in sorted(rows, key=lambda r: str(r["term"]).lower()):
        source = str(row.get("source") or "")
        where = f"[`{source}`]({SOURCE_URL}{source})" if source else ""
        body.append(f"| {_cell(row['term'])} | {_cell(row.get('description', ''))} | {where} |")
    body.append(_source_note([WORLD_GLOSSARY]))
    _write(section / "index.md", _frontmatter("Glossary", [WORLD_GLOSSARY], 4) + "\n".join(body))
    return 1


# ── entry point ────────────────────────────────────────────────────────────────────────────


def generate(out: Path) -> dict[str, int]:
    """Clear the generated folders under `out` and write every section; return page counts."""
    for name in GENERATED_DIRS:
        target = out / name
        if target.exists():
            shutil.rmtree(target)
    return {"laws": build_laws(out), "mechanisms": build_mechanisms(out), "catalog": build_catalog(out), "glossary": build_glossary(out)}


def main(argv: list[str] | None = None) -> int:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default: website/wiki/world-knowledge)")
    args = parser.parse_args(argv)
    counts = generate(args.out)
    print("generate_wiki: " + ", ".join(f"{count} {name} pages" for name, count in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
