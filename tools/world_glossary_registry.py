#!/usr/bin/env python3
"""
Manage the append-only world-term glossary (registries/world_glossary.jsonl).

Built for TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY. The website wiki (generated from stored repo
data; `website/scripts/generate_wiki.py` reads the `term`, `description` and `source` fields, so
those names are stable) needs a plain description of each world term (tick, region, lead,
faction, calamity, ...) and a pointer to the law that term summarises.

How this differs from `tools/glossary_registry.py` (the agent-ops dashboard glossary), and why the
two never merge:
- The dashboard glossary is served whole as dashboard tooltips (`src/api/agent_ops_dashboard/
  ingest.py`), so a world term in it would leak into the agent-ops UI.
- It is one case-sensitive namespace keyed by term, and world terms such as the kernel phases
  Resolution and Collection, or the word "phase", sit beside its 40 workflow phase names.
- A world term must point at the law it summarises, and the dashboard rows have no such field.

Row fields: `term` (exact display string, case-sensitive, unique), `description` (one or two plain
sentences, no formula), `source` (repo path to an authoritative doc under `docs/mechanics/`,
`docs/engine/` or `docs/core/`, with an optional `#anchor`), `added` (ISO date).

Ownership: this tool belongs to agent-working. The rows are rpg content; rpg-planner writes or
reviews the descriptions. The file may be empty or absent, and the wiki renders nothing then.

Usage:
  python3 tools/world_glossary_registry.py add <term> --description "..." --source docs/mechanics/<file>.md[#anchor]
  python3 tools/world_glossary_registry.py list
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_REL_PATH = Path("registries/world_glossary.jsonl")

#: The only doc trees a `source` may point into: the authoritative laws, so the wiki points at the law.
SOURCE_ROOTS = ("docs/mechanics/", "docs/engine/", "docs/core/")


def registry_path(root: Path | str | None = None) -> Path:
    base = Path(root) if root is not None else _DEFAULT_ROOT
    return base / _REGISTRY_REL_PATH


def load_registry(root: Path | str | None = None) -> dict:
    """Return {term: row} for every row. Empty dict if the file is absent or empty.

    Raises ValueError on a duplicate term (the file must hold each term exactly once).
    """
    path = registry_path(root)
    if not path.exists():
        return {}
    registry: dict = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        term = row["term"]
        if term in registry:
            raise ValueError(
                f"{path}: duplicate registration for term {term!r} at line {lineno}; each term must appear exactly once"
            )
        registry[term] = row
    return registry


def source_problem(source: str, root: Path | str | None = None) -> str | None:
    """None when `source` is `<path>[#anchor]` under an allowed doc root and the file exists; else the reason."""
    base = Path(root) if root is not None else _DEFAULT_ROOT
    rel = source.split("#", 1)[0]
    if not rel.startswith(SOURCE_ROOTS):
        return f"source {rel!r} must be under one of {list(SOURCE_ROOTS)}"
    if ".." in Path(rel).parts:
        return f"source {rel!r} must not contain '..'"
    if not (base / rel).is_file():
        return f"source path {rel!r} does not exist"
    return None


def add_term(term: str, description: str, source: str, root: Path | str | None = None) -> dict:
    """Append one row and return it. Raises ValueError (writing nothing) for a blank term or
    description, a bad or missing `source`, or an already-registered term."""
    if not term.strip():
        raise ValueError("term must not be blank")
    if term != term.strip():
        raise ValueError(f"term {term!r} must not have leading or trailing whitespace")
    if not description.strip():
        raise ValueError(f"cannot register {term!r}: description must not be blank")
    problem = source_problem(source, root)
    if problem:
        raise ValueError(f"cannot register {term!r}: {problem}")
    registry = load_registry(root)
    if term in registry:
        raise ValueError(
            f"{term!r} is already registered (added {registry[term].get('added')}); terms cannot be re-added or changed"
        )
    row = {
        "term": term,
        "description": description,
        "source": source,
        "added": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Manage the append-only world-term glossary (registries/world_glossary.jsonl).")
    sub = parser.add_subparsers(dest="command", required=True)
    add_p = sub.add_parser("add", help="Register a new world term (append-only)")
    add_p.add_argument("term")
    add_p.add_argument("--description", required=True, help="One or two plain sentences, no formula")
    add_p.add_argument("--source", required=True, help="docs/mechanics|engine|core/<file>.md[#anchor]")
    add_p.add_argument("--root", default=None)
    list_p = sub.add_parser("list", help="Print all registered world terms")
    list_p.add_argument("--root", default=None)
    args = parser.parse_args(argv)

    if args.command == "add":
        try:
            row = add_term(args.term, args.description, args.source, root=args.root)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"Registered term {row['term']!r} -> {row['source']} ({row['added']}).")
        return 0
    try:
        registry = load_registry(args.root)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for term in sorted(registry):
        row = registry[term]
        print(f"{term:<24} {row['source']}  {row.get('description', '')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
