"""Name-switch scan (TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE).

Milestone 1 retires every place where a decision reads a role, kind or faction *name*. This module finds those places mechanically, with an AST scan of ``src/``,
so the retirement ticket (TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES) starts from an inventory and the architecture test can hold the
list from growing.

A *switch* is, in code that runs while an entity's action is chosen or resolved:

* ``compare``: a role, kind or faction compared to a name: a string literal, or a ``Faction.X`` / ``EntityRole.X`` member (``==``, ``!=``, ``is``, ``in``, ``not in``,
  including a tuple, set or list of names on either side);
* ``match``: a ``case`` pattern naming a ``Faction.X`` / ``EntityRole.X`` member or a string literal;
* ``lookup``: ``TABLE[Faction.X]``, an enum member used as a subscript key;
* ``table``: a dict written in code and keyed on ``Faction.X`` / ``EntityRole.X`` members, or a dict bound to a name that says role, kind or faction and keyed on string
  names (allegiance and hostility tables are this shape).

Reading a content-declared relation keyed by id is data, not a switch, and is not found: the scan only looks at names (string literals and the two legacy enums).

"Says role, kind or faction" is a name test on the other operand: its last attribute or variable name is ``role`` or ``faction`` (optionally prefixed, or with an
``_id`` / ``_name`` suffix: ``entity_role``, ``owner_faction``), or ``kind`` on an entity-like receiver (``entity.kind``), or ``entity_kind`` / ``monster_kind``. The
operand is read through ``.name`` / ``.value``, ``.lower()``, ``a or b``, ``getattr(x, "kind", default)`` (as ``x.kind``) and a local name assigned from one of those
earlier in the same function (``kind = (getattr(entity, "kind", "") or "").lower()``; one step, no tracking across functions). The scan sees only string literals and the two legacy enums, ``EntityRole`` and ``Faction``; no other entity-kind enum exists in ``src/`` today (the ``*Kind`` enums are
item, lead, place and skill kinds), so that is a recorded limit and not a gap. The test is on spelling, so a
``kind`` that is not an entity kind (a wound kind, an objective kind) is found too: the scan reports it and the allowlist reason says so. A resolved id compared to a string literal is a switch too: ``role_id``, ``faction_id``, ``species_id``, ``archetype_id`` (and ``species`` / ``archetype``) count on any receiver.
A switch spelt some other way (``monster_type == "goblin"``) is not found; that limit is recorded in the test and the PR, not hidden. ``PROMOTED_GATING`` and
``REASONED_EXCLUSIONS`` are the two per-row rulings (a report-only row that gates, a found switch that is ruled out), kept as data.

Packages are sorted by ruling (rpg-planner, 2026-11-15): ``SCAN`` is gating (src/content_semantics, src/world and src/core included), ``REPORT_ONLY`` is reported but never fails, ``EXCLUDE`` is not looked at. Every
directory under ``src/`` must be in exactly one list, so a new package is classified before it can hide a switch.

Run ``python -m tools.test_architecture.name_switch_scan`` for the text rows, ``--json`` for the same as JSON, ``--gating-only`` to drop the report-only rows.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[2]

# Gating: code run while an entity's action is chosen or resolved. ``src/domains`` is every subpackage of it.
SCAN: Tuple[str, ...] = (
    "ai", "cognition", "strategy", "actions", "engine", "systems", "domains", "economy", "town", "quests", "progression", "entities", "content_semantics", "world", "core",
)
# Reported, never failing. Empty since rpg-planner ruled all 15 src/world rows gating (#918 6889044816); the list and its machinery stay for the next package that needs a first look.
REPORT_ONLY: Tuple[str, ...] = ()
# Not looked at: output, tooling, harness and world-declaration packages; ``content`` declares kinds by name on purpose.
EXCLUDE: Tuple[str, ...] = (
    "api", "views", "rendering", "observability", "logging", "replay", "cli", "lab", "perf", "certification", "simulation_quality", "testing", "scenarios",
    "platform", "config", "worldassembly", "worldbuilding", "worldgeneration", "worldmodules", "content",
    "runtime",  # bootstrap.py only: startup wiring (rpg-planner, 2026-11-15). If the scan ever finds a row there, report it to rpg-planner.
)

# A row in a report-only package that gates anyway: (file, symbol of the enclosing function or ``<module>[TABLE]``). rpg-planner rules the rest of the
# report-only rows one by one; a promotion that matches no switch is stale and fails, like a stale allowlist row.
PROMOTED_GATING: frozenset = frozenset()

# A switch that is found and ruled out, with the reason: (file, symbol) -> reason. Reported as ``excluded``, never gating, and a stale entry fails.
REASONED_EXCLUSIONS: Dict[Tuple[str, str], str] = {
    ("src/entities/identity_resolver.py", "<module>[_ROLE_COMPAT]"):
        "identity projection: renames a legacy enum to its string id; chooses nothing; whether the map itself goes is for the retire ticket, depending on whether EntityRole stays pure classification",
    ("src/entities/identity_resolver.py", "<module>[_FACTION_COMPAT]"):
        "identity projection: renames a legacy enum to its string id; chooses nothing; whether the map itself goes is for the retire ticket, depending on whether EntityRole stays pure classification",
}

LEGACY_ENUMS = {"EntityRole", "Faction"}
# Role and faction words count on any receiver. ``kind`` is also the word for a wound, a lead, an objective, an event: it counts only on an entity-like receiver
# (``entity.kind``, ``monster.kind``) or as ``entity_kind`` / ``monster_kind`` / ``creature_kind``; ``work_kind``, ``event_kind`` and the like are other records' kinds.
_ROLE_FACTION = re.compile(r"(?:^|_)(?:role|faction|species|archetype)(?:_id|_name)?$", re.IGNORECASE)
_ENTITY_KIND = re.compile(r"^(?:entity|monster|creature|npc)_kind(?:_id|_name)?$", re.IGNORECASE)
_KIND_WORD = re.compile(r"^kind(?:_id|_name)?$", re.IGNORECASE)
ENTITY_RECEIVERS = frozenset({"entity", "e", "ent", "monster", "creature", "npc", "mob", "target", "attacker", "defender", "victim", "actor", "other", "hero"})
_TABLE_NAME = re.compile(r"(?:^|_)(?:role|faction|species|archetype)s?(?:_id|_name)?$|(?:^|_)(?:entity|monster|creature|npc)_kind(?:_id|_name)?$", re.IGNORECASE)  # tables: a dict bound to a name that says role or faction (``_FACTION_COMPAT``, ``SPAWN_KIND_CATALOG_FACTION``) or entity kind
_COMPARE_OPS = (ast.Eq, ast.NotEq, ast.Is, ast.IsNot, ast.In, ast.NotIn)


@dataclass(frozen=True)
class Switch:
    file: str
    line: int
    symbol: str
    name: str
    shape: str  # compare | match | lookup | table
    status: str  # gating | report-only | excluded
    subject: str = ""  # what is compared (compare), or what the table is bound to (table); context for a human, not part of the allowlist key

    @property
    def key(self) -> Tuple[str, str, str]:
        return (self.file, self.symbol, self.name)


# ------------------------------------------------------------------------------------------------------------------------------ classification
def top_level_packages(root: Path = REPO) -> List[str]:
    return sorted(p.name for p in (root / "src").iterdir() if p.is_dir() and p.name != "__pycache__")


def package_problems(packages: Iterable[str], scan=SCAN, report_only=REPORT_ONLY, exclude=EXCLUDE) -> List[str]:
    """Every package is in exactly one list; no list names a package that is not there."""
    problems: List[str] = []
    present = set(packages)
    lists = {"SCAN": scan, "REPORT_ONLY": report_only, "EXCLUDE": exclude}
    for pkg in sorted(present):
        homes = [n for n, members in lists.items() if pkg in members]
        if not homes:
            problems.append(f"src/{pkg} is in no list: add it to SCAN, REPORT_ONLY or EXCLUDE in tools/test_architecture/name_switch_scan.py")
        elif len(homes) > 1:
            problems.append(f"src/{pkg} is in more than one list: {', '.join(homes)}")
    for n, members in lists.items():
        for pkg in members:
            if pkg not in present:
                problems.append(f"{n} names src/{pkg}, which is not a package any more")
    return problems


def _status(pkg: str, scan=SCAN, report_only=REPORT_ONLY) -> Optional[str]:
    if pkg in scan:
        return "gating"
    if pkg in report_only:
        return "report-only"
    return None


# ------------------------------------------------------------------------------------------------------------------------------ AST
def _enum_member(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "int" and len(node.args) == 1:
        node = node.args[0]  # int(EntityRole.X) is the same name
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in LEGACY_ENUMS:
        return f"{node.value.id}.{node.attr}"
    return None


def _str_name(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.strip() and not node.value.strip().lstrip("-").isdigit():
        return node.value
    return None


def _names_in(node: ast.AST) -> List[str]:
    """The names an operand carries: itself, or the members of a tuple, set or list of them."""
    if isinstance(node, (ast.Tuple, ast.Set, ast.List)):
        out: List[str] = []
        for elt in node.elts:
            out.extend(_names_in(elt))
        return out
    single = _enum_member(node) or _str_name(node)
    return [repr(single) if _str_name(node) else single] if single else []


def _receiver_name(receiver: ast.AST) -> Optional[str]:
    return receiver.attr if isinstance(receiver, ast.Attribute) else getattr(receiver, "id", None)


def _word_on(word: str, receiver: Optional[ast.AST]) -> Optional[str]:
    """``word`` read off ``receiver`` (None for a bare variable): role and faction words count anywhere, ``kind`` only on an entity-like receiver."""
    if _ROLE_FACTION.search(word) or _ENTITY_KIND.match(word):
        return word
    if _KIND_WORD.match(word) and receiver is not None and _receiver_name(receiver) in ENTITY_RECEIVERS:
        return word
    return None


def _subject_word(node: ast.AST, bound: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """The role, kind or faction word an operand ends in.

    Looks through ``.name`` / ``.value``, ``.lower()`` and friends, ``a or b``, ``a if c else b``, and ``getattr(x, "kind", default)`` (read as ``x.kind``). A bare
    local name counts when ``bound`` says it was assigned from such an expression earlier in the same function (``kind = (getattr(e, "kind", "") or "").lower()``).
    """
    bound = bound or {}
    while True:
        if isinstance(node, ast.Attribute) and node.attr in ("name", "value", "lower", "upper"):
            node = node.value
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("lower", "upper", "casefold", "strip"):
            node = node.func.value
        elif isinstance(node, ast.BoolOp):
            for value in node.values:
                found = _subject_word(value, bound)
                if found:
                    return found
            return None
        elif isinstance(node, ast.IfExp):
            return _subject_word(node.body, bound) or _subject_word(node.orelse, bound)
        else:
            break
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr" and len(node.args) >= 2:
        name = _str_name(node.args[1])
        return _word_on(name, node.args[0]) if name else None
    if isinstance(node, ast.Attribute):
        return _word_on(node.attr, node.value)
    if isinstance(node, ast.Name):
        return bound.get(node.id) or _word_on(node.id, None)
    return None


class _Visitor(ast.NodeVisitor):
    def __init__(self, rel: str, status: str):
        self.rel, self.status = rel, status
        self.scope: List[str] = []
        self.found: List[Switch] = []
        self.bound_stack: List[Dict[str, str]] = [{}]  # per function: local name -> the role/kind/faction word it was assigned from

    # -- scope
    def _symbol(self) -> str:
        return ".".join(self.scope) if self.scope else "<module>"

    def _push(self, name: str, node: ast.AST) -> None:
        self.scope.append(name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.bound_stack.append({})
        self._push(node.name, node)
        self.bound_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._push(node.name, node)

    def _add(self, node: ast.AST, name: str, shape: str, subject: str = "") -> None:
        symbol = self._symbol()
        if shape == "table" and subject:
            symbol = f"{symbol}[{subject}]"  # two tables in one scope are two rows: the allowlist key stays (file, symbol, name)
        self.found.append(Switch(self.rel, node.lineno, symbol, name, shape, self.status, subject))

    # -- shapes
    def visit_Compare(self, node: ast.Compare) -> None:
        operands = [node.left, *node.comparators]
        for op, left, right in zip(node.ops, operands, operands[1:]):
            if not isinstance(op, _COMPARE_OPS):
                continue
            for named, other in ((left, right), (right, left)):
                names = _names_in(named)
                if not names:
                    continue
                if any(n.startswith(("EntityRole.", "Faction.")) for n in names) or _subject_word(other, self.bound_stack[-1]):
                    for n in names:
                        self._add(node, n, "compare", ast.unparse(other)[:60])
        self.generic_visit(node)

    def visit_match_case(self, node: ast.match_case) -> None:  # type: ignore[name-defined]
        for sub in ast.walk(node.pattern):
            if isinstance(sub, ast.MatchValue):
                for n in _names_in(sub.value):
                    self._add(sub, n, "match", "")
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        member = _enum_member(node.slice)
        if member:
            self._add(node, member, "lookup")
        self.generic_visit(node)

    def _table(self, node: ast.Dict, bound_to: Optional[str]) -> None:
        for key in node.keys:
            if key is None:
                continue
            member = _enum_member(key)
            if member:
                self._add(key, member, "table", bound_to or "")
            elif bound_to and _TABLE_NAME.search(bound_to) and _str_name(key):
                self._add(key, repr(_str_name(key)), "table", bound_to)

    def _name_set(self, value: ast.AST, bound_to: Optional[str]) -> None:
        """A tuple, list or set of legacy enum members bound to a name (``_CANDIDATE_ROLES = (EntityRole.A, ...)``) is a name table that a ``role in`` reads."""
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id in ("frozenset", "set", "tuple", "list") and value.args:
            value = value.args[0]
        if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            for elt in value.elts:
                member = _enum_member(elt)
                if member:
                    self._add(elt, member, "table", bound_to or "")

    def _bind(self, target: ast.AST, value: Optional[ast.AST]) -> None:
        if isinstance(target, ast.Name) and value is not None:
            word = _subject_word(value, self.bound_stack[-1])
            if word:
                self.bound_stack[-1][target.id] = word
            else:
                self.bound_stack[-1].pop(target.id, None)

    def visit_Assign(self, node: ast.Assign) -> None:
        target0 = node.targets[0]
        if len(node.targets) == 1:
            self._bind(target0, node.value)
        self._name_set(node.value, target0.id if isinstance(target0, ast.Name) else getattr(target0, "attr", None))
        if isinstance(node.value, ast.Dict):
            target = node.targets[0]
            bound = target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
            self._table(node.value, bound)
            self._seen_dicts.add(id(node.value))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._bind(node.target, node.value)
        if node.value is not None:
            self._name_set(node.value, node.target.id if isinstance(node.target, ast.Name) else getattr(node.target, "attr", None))
        if isinstance(node.value, ast.Dict):
            target = node.target
            bound = target.id if isinstance(target, ast.Name) else getattr(target, "attr", None)
            self._table(node.value, bound)
            self._seen_dicts.add(id(node.value))
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        if id(node) not in self._seen_dicts:  # a dict not bound by an assignment: only enum-member keys count
            self._table(node, None)
        self.generic_visit(node)

    _seen_dicts: set

    def run(self, tree: ast.AST) -> List[Switch]:
        self._seen_dicts = set()
        self.visit(tree)
        return self.found


def scan_source(source: str, rel: str, status: str = "gating") -> List[Switch]:
    return _Visitor(rel, status).run(ast.parse(source))


def scan_tree(root: Path = REPO, scan: Sequence[str] = SCAN, report_only: Sequence[str] = REPORT_ONLY, promoted=PROMOTED_GATING, exclusions=REASONED_EXCLUSIONS) -> List[Switch]:
    out: List[Switch] = []
    for path in sorted((root / "src").rglob("*.py")):
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        if len(parts) < 3:
            continue
        status = _status(parts[1], scan, report_only)
        if status is None:
            continue
        for sw in scan_source(path.read_text(encoding="utf-8"), rel, status):
            if (sw.file, sw.symbol) in exclusions:
                sw = replace(sw, status="excluded")
            elif sw.status == "report-only" and (sw.file, sw.symbol) in promoted:
                sw = replace(sw, status="gating")
            out.append(sw)
    return sorted(out, key=lambda s: (s.file, s.line, s.name, s.shape))


# ------------------------------------------------------------------------------------------------------------------------------ the ratchet
def group(switches: Iterable[Switch]) -> Dict[Tuple[str, str, str], int]:
    counts: Dict[Tuple[str, str, str], int] = {}
    for s in switches:
        if s.status == "gating":
            counts[s.key] = counts.get(s.key, 0) + 1
    return counts


def check_rulings(switches: Iterable[Switch], promoted=PROMOTED_GATING, exclusions=REASONED_EXCLUSIONS) -> List[str]:
    """A promotion or an exclusion whose switch is gone is stale; an exclusion has a reason."""
    seen = {(s.file, s.symbol) for s in switches}
    problems: List[str] = []
    for key in sorted(promoted):
        if key not in seen:
            problems.append(f"stale promotion {key[0]}:{key[1]}: no switch there any more, remove it from PROMOTED_GATING")
    for key, reason in sorted(exclusions.items()):
        if key not in seen:
            problems.append(f"stale exclusion {key[0]}:{key[1]}: no switch there any more, remove it from REASONED_EXCLUSIONS")
        if not reason.strip():
            problems.append(f"exclusion {key[0]}:{key[1]} has no reason")
    return problems


def check_allowlist(switches: Iterable[Switch], allowlist: Dict[Tuple[str, str, str], int]) -> List[str]:
    """A gating switch with no row, more of them than a row counts, or a row with fewer: each is a violation."""
    problems: List[str] = []
    found = group(switches)
    for key, n in sorted(found.items()):
        file, symbol, name = key
        have = allowlist.get(key)
        if have is None:
            problems.append(f"new name switch {file}:{symbol} on {name} ({n}x): decide on a content declaration instead of a name, or see the retire ticket")
        elif n > have:
            problems.append(f"new name switch {file}:{symbol} on {name}: {n} found, the allowlist row counts {have}")
        elif n < have:
            problems.append(f"stale allowlist row {file}:{symbol} on {name}: {n} found, the row counts {have}; lower the count or remove the row")
    for key in sorted(allowlist):
        if key not in found:
            problems.append(f"stale allowlist row {key[0]}:{key[1]} on {key[2]}: no such switch any more, remove the row")
    return problems


# ------------------------------------------------------------------------------------------------------------------------------ output
def render_text(switches: Sequence[Switch]) -> str:
    lines = [f"{s.file}:{s.line}\t{s.symbol}\t{s.name}\t{s.shape}\t{s.status}\t{s.subject}" for s in switches]
    n = {k: sum(1 for s in switches if s.status == k) for k in ("gating", "report-only", "excluded")}
    lines.append(f"# {len(switches)} switches: {n['gating']} gating, {n['report-only']} report-only, {n['excluded']} excluded")
    return "\n".join(lines)


def render_json(switches: Sequence[Switch]) -> str:
    n = {k: sum(1 for s in switches if s.status == k) for k in ("gating", "report-only", "excluded")}
    return json.dumps({"counts": {"total": len(switches), "gating": n["gating"], "report_only": n["report-only"], "excluded": n["excluded"]},
                       "switches": [asdict(s) for s in switches]}, indent=2)


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text rows")
    ap.add_argument("--gating-only", action="store_true", help="drop the report-only rows")
    args = ap.parse_args(argv)
    rows = scan_tree()
    if args.gating_only:
        rows = [s for s in rows if s.status == "gating"]
    print(render_json(rows) if args.json else render_text(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
