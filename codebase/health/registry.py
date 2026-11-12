"""codebase/baselines/code_health_exceptions.jsonl: the grandfathered code-health violations.

One row per known violation of a rule at a place, found by a full scan when the registry was
seeded. The ratchet (`codebase.health.ratchet`) fails only on a violation that has no row, or
whose measured value is above its row's `ceiling`.

Unlike `registries/tag_registry.jsonl` and `registries/layer_registry.jsonl` (append-only), rows
here are DELETED when the debt is paid: `delete` removes one row, and `tighten` lowers ceilings
and deletes rows whose violation has gone. Trend history belongs to the code-health snapshot, not
to this file. CLI shape and the typed `reviewed` field follow `tools/capability_envelope_baseline.py`
(seeded rows are `reviewed: false`: bulk-recorded, never individually reviewed); that tool is
append-only and audit-only, which this one is not.

Row fields (roadmap section 6.3), all required, `symbol` and `retiring_ticket` may be null:

    file, symbol, tool, rule, value, ceiling, added_date, reviewed, retiring_ticket

Match key: `(file, symbol, tool, rule)`, never a line number. What `symbol` holds for each tool
(qualified function name, `None`, or `dup:<other file>` for a jscpd file pair) is documented in
`codebase/health/findings.py`. The file is kept sorted by that key so concurrent edits to
different rows merge cleanly.

Validation rejects: a row missing a required field or with a wrongly typed one, two rows with the
same key, and a `file` (or a jscpd `dup:` partner) that does not exist in the repository.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import date
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from codebase.health.findings import TOOL_JSCPD, Finding, Key

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_REL_PATH = Path("codebase/baselines/code_health_exceptions.jsonl")

REQUIRED_FIELDS = (
    "file", "symbol", "tool", "rule", "value", "ceiling", "added_date", "reviewed", "retiring_ticket",
)
NULLABLE_FIELDS = frozenset({"symbol", "retiring_ticket"})
DUP_PREFIX = "dup:"
MODULE_SYMBOL = "<module>"  # ast-grep's symbol for a finding outside any def or class

# Files named by TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS (four same-named class pairs). A
# duplication row that touches one carries a link to that ticket and nothing else: this tool
# never files a ticket or a finding for those pairs.
SAME_NAME_PAIRS_TICKET = "TCK-20260930-SAME-NAME-DIVERGENT-CLASS-PAIRS"
SAME_NAME_PAIR_FILES = frozenset(
    {
        "src/core/items.py",
        "src/core/registries.py",
        "src/core/recipes.py",
        "src/progression/skills.py",
        "src/engine/rpg_depth.py",
        "src/strategy/cognition_capacity.py",
        "src/strategy/capacity.py",
    }
)


class MoveRefusedError(ValueError):
    """`move_rows` would loosen the gate or has nothing to do; `reason` says why. Nothing was changed."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class RegistryError(ValueError):
    """The registry file is malformed. `problems` lists every defect found."""

    def __init__(self, problems: Sequence[str]) -> None:
        super().__init__("; ".join(problems))
        self.problems = list(problems)


@dataclass(frozen=True)
class Row:
    """One grandfathered violation."""

    file: str
    symbol: str | None
    tool: str
    rule: str
    value: int
    ceiling: int
    added_date: str
    reviewed: bool
    retiring_ticket: str | None

    @property
    def key(self) -> Key:
        """The line-independent identity shared with `Finding.key`."""
        return (self.file, self.symbol, self.tool, self.rule)


def registry_path(root: Path | str | None = None) -> Path:
    """Where the registry lives under `root` (default: this repository)."""
    return (Path(root) if root is not None else REPO_ROOT) / REGISTRY_REL_PATH


def _sort_key(row: Row) -> tuple[str, str, str, str]:
    return (row.file, row.symbol or "", row.tool, row.rule)


def _row_problems(entry: Mapping[str, object], where: str) -> list[str]:
    problems = [f"{where}: missing required field '{name}'" for name in REQUIRED_FIELDS if name not in entry]
    for name in REQUIRED_FIELDS:
        if name not in entry or (entry[name] is None and name in NULLABLE_FIELDS):
            continue
        value = entry[name]
        wrong = (
            (name in ("value", "ceiling") and (not isinstance(value, int) or isinstance(value, bool) or value < 0))
            or (name == "reviewed" and not isinstance(value, bool))
            or (name in ("file", "tool", "rule", "added_date") and not (isinstance(value, str) and value))
            or (name in NULLABLE_FIELDS and not isinstance(value, str))
        )
        if wrong:
            problems.append(f"{where}: field '{name}' has an invalid value {value!r}")
    return problems


def _existence_problems(entry: Mapping[str, object], where: str, root: Path) -> list[str]:
    paths = [entry.get("file")]
    symbol = entry.get("symbol")
    if entry.get("tool") == TOOL_JSCPD and isinstance(symbol, str) and symbol.startswith(DUP_PREFIX):
        paths.append(symbol[len(DUP_PREFIX):])
    return [
        f"{where}: file does not exist: {path}"
        for path in paths
        if isinstance(path, str) and path and not (root / path).is_file()
    ]


def validate_file(path: Path, root: Path | None = None, check_files: bool = True) -> list[str]:
    """Every problem in the registry file at `path`; empty if it is valid. A missing file is valid.

    `check_files=False` skips the "file exists" test. The ratchet uses that, so a source file that
    another change deleted shows up as a "gone" row instead of making the whole registry unusable.
    """
    root = root or REPO_ROOT
    if not path.exists():
        return []
    problems: list[str] = []
    seen: dict[Key, int] = {}
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        where = f"{path.name}:{number}"
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"{where}: not valid JSON ({exc.msg})")
            continue
        row_problems = _row_problems(entry, where)
        problems.extend(row_problems)
        if row_problems:
            continue
        if check_files:
            problems.extend(_existence_problems(entry, where, root))
        key = (entry["file"], entry["symbol"], entry["tool"], entry["rule"])
        if key in seen:
            problems.append(f"{where}: duplicate key {key!r}, first seen on line {seen[key]}")
        seen.setdefault(key, number)
    return problems


def load_rows(path: Path, root: Path | None = None, check_files: bool = True) -> list[Row]:
    """The rows in `path`, sorted by key. Raises `RegistryError` if the file is not valid."""
    problems = validate_file(path, root, check_files)
    if problems:
        raise RegistryError(problems)
    if not path.exists():
        return []
    rows = [
        Row(**{name: json.loads(line)[name] for name in REQUIRED_FIELDS})
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return sorted(rows, key=_sort_key)


def write_rows(path: Path, rows: Iterable[Row]) -> None:
    """Write `rows` sorted by key, one JSON object per line, with a stable field order."""
    ordered = sorted(rows, key=_sort_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(asdict(row), sort_keys=True) + "\n" for row in ordered), encoding="utf-8"
    )


def _retiring_ticket(finding: Finding) -> str | None:
    """Link a duplication row that touches a same-name-pair file to that ticket; nothing else."""
    if finding.tool != TOOL_JSCPD or not finding.symbol:
        return None
    touched = {finding.file, finding.symbol[len(DUP_PREFIX):]}
    return SAME_NAME_PAIRS_TICKET if touched & SAME_NAME_PAIR_FILES else None


def seed_rows(
    findings: Iterable[Finding], today: date | None = None, previous: Iterable[Row] = ()
) -> list[Row]:
    """A row for every finding, ceiling equal to its measured value.

    A new key is stamped `today` and `reviewed: false`. A key that is also in `previous` (a reseed)
    keeps its `reviewed`, `retiring_ticket` and `added_date`, so reseeding after a tool version bump
    never throws away review work; its value and ceiling are reset to the new measurement. Keys in
    `previous` that no longer have a finding are dropped.
    """
    stamp = (today or date.today()).isoformat()
    earlier = {row.key: row for row in previous}
    rows = []
    for f in findings:
        before = earlier.get(f.key)
        if before is None:
            rows.append(Row(f.file, f.symbol, f.tool, f.rule, f.value, f.value, stamp, False, _retiring_ticket(f)))
        else:
            ticket = before.retiring_ticket or _retiring_ticket(f)
            rows.append(
                Row(f.file, f.symbol, f.tool, f.rule, f.value, f.value, before.added_date, before.reviewed, ticket)
            )
    return sorted(rows, key=_sort_key)


def delete_row(rows: Sequence[Row], key: Key) -> list[Row]:
    """`rows` without the row at `key`. Raises `KeyError` if there is no such row."""
    remaining = [row for row in rows if row.key != key]
    if len(remaining) == len(rows):
        raise KeyError(key)
    return remaining


def tighten(rows: Sequence[Row], findings: Iterable[Finding]) -> tuple[list[Row], list[str]]:
    """Lower each row's value and ceiling to the current measurement; delete rows whose violation is gone.

    A finding with no row, or above its ceiling, is left alone: tightening never loosens.
    """
    current = {finding.key: finding for finding in findings}
    kept: list[Row] = []
    changes: list[str] = []
    for row in rows:
        finding = current.get(row.key)
        if finding is None:
            changes.append(f"deleted {row.key}: violation is gone")
        elif finding.value < row.ceiling:
            changes.append(f"lowered {row.key}: {row.ceiling} -> {finding.value}")
            kept.append(Row(**{**asdict(row), "value": finding.value, "ceiling": finding.value}))
        else:
            kept.append(row)
    return sorted(kept, key=_sort_key), changes


def movable_symbol(symbol: str | None, tool: str) -> bool:
    """True if `symbol` names one definition that can move between files.

    File-level rows (symbol `None`), ast-grep's `<module>` and a jscpd file pair are not definitions.
    """
    return symbol is not None and symbol != MODULE_SYMBOL and tool != TOOL_JSCPD


def move_rows(
    rows: Sequence[Row], findings: Iterable[Finding], old_file: str, new_file: str, symbol: str | None = None
) -> tuple[list[Row], list[str]]:
    """Re-key rows of `old_file` to `new_file`, changing `file` and nothing else. Raises `MoveRefusedError` and changes nothing if:

    - `old_file` is `new_file`, or no row would move;
    - a row to move has a current finding at its old key (the code is still there) or none at the new key (it did not move);
    - a moved finding is above its row's ceiling (a move never loosens the gate);
    - `new_file` already has a row with the moved key.

    Without `symbol`, rows that did not move stay where they are. With `symbol`, every row of that symbol must move.
    """
    if old_file == new_file:
        raise MoveRefusedError("OLD_FILE and NEW_FILE are the same file")
    current = {finding.key: finding for finding in findings}
    existing = {row.key for row in rows}
    candidates = [
        row for row in rows
        if row.file == old_file and movable_symbol(row.symbol, row.tool) and (symbol is None or row.symbol == symbol)
    ]
    moving: list[Row] = []
    for row in candidates:
        problem = _move_problem(row, new_file, current, existing)
        if problem is None:
            moving.append(row)
        elif symbol is not None:
            raise MoveRefusedError(f"{symbol} cannot be moved: {problem}")
    if not moving:
        raise MoveRefusedError(f"no row of {old_file} has moved to {new_file}" + (f" for symbol {symbol}" if symbol else ""))
    changes = []
    moved = {row.key for row in moving}
    for row in moving:
        finding = current[(new_file, *row.key[1:])]
        if finding.value > row.ceiling:
            raise MoveRefusedError(f"{row.key[1:]} is {finding.value} in {new_file}, above its ceiling {row.ceiling}")
        changes.append(f"moved {row.symbol} [{row.tool} {row.rule}] {old_file} -> {new_file}, ceiling {row.ceiling} kept")
    kept = [row for row in rows if row.key not in moved]
    return sorted(kept + [replace(row, file=new_file) for row in moving], key=_sort_key), changes


def _move_problem(row: Row, new_file: str, current: Mapping[Key, Finding], existing: set[Key]) -> str | None:
    """Why `row` has not moved to `new_file`, or None if it has. Raises `MoveRefusedError` if `new_file` has a row for it.

    A ceiling breach is checked by the caller.
    """
    target = (new_file, *row.key[1:])
    if row.key in current:
        return f"{row.file} still has a [{row.tool} {row.rule}] finding for it"
    if target not in current:
        return f"{new_file} has no [{row.tool} {row.rule}] finding for it"
    if target in existing:
        raise MoveRefusedError(f"{new_file} already has a row for {row.symbol} [{row.tool} {row.rule}]")
    return None
