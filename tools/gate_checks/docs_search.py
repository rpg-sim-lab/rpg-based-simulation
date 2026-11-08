"""Search docs/ for the docs a change may leave stale (TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH).

Design source: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2),
"Owner correction (2026-11-07)" F1 and F5, and "Normative sources and precedence (R3)".

One reusable function, `search_docs_for_change`, shared by the investigator (Investigate's
`## Docs Requiring Update`), doc-updater's satellite step and `doc_staleness_check.py`'s advisory
list. It reads, never writes, and never fails a caller: errors come back in `notes`.

Output lists:
- `required`: a direct hit (changed path, public symbol or old-behaviour term) in a normative doc
  (world rules, Mechanics Bible, engine contracts, architecture contracts). It is "normative tier plus
  a direct hit", not "states the changed fact": a function cannot read meaning, so the caller confirms each.
- `candidate`: every other hit, ranked direct hit, then symbol or term, then importer, then mechanism.
- `excluded`: history and record docs that were hit, each with its class as the reason and the hits it
  kept, so an excluded doc is visible and never silently dropped.
- `comment_hits` (F5): comment and docstring lines in the changed Python files that state an invariant,
  lifecycle, concurrency or recovery behaviour. A prompt aid, not a verdict.

Every read comes from a `Source`: the working tree (`DirSource`) or a git ref (`GitRefSource`), so a
replay pinned to a SHA is repeatable. Nothing here is tuned to a known item: the rules are the classes
below and the counts that remain are reported.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import re
import subprocess
import sys
import tokenize
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml
except ImportError:  # the search still runs; only the mechanism-registry input is lost
    yaml = None

TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".html", ".txt", ".csv", ".json"}
MAX_DOC_BYTES = 1_000_000
MAX_HITS_KEPT = 5
MAX_HIT_TEXT = 160

# R3 history classes, checked first. Each is the `reason` an excluded doc carries.
EXCLUDED_PREFIXES = (("docs/archive/", "archive"), ("docs/audits/", "audit"))
EXCLUDED_FILES = {"docs/REGISTRY.yaml": "registry"}
HISTORICAL_STATUSES = {"historical", "superseded"}
REVIEW_RECORD_STEM = re.compile(r"(_review|_report|_audit)$")

# Normative tier (R3 items 1-3). `docs/engine/matrices/` is a matrix, not a contract.
NORMATIVE_PREFIXES = ("docs/world_rules/", "docs/mechanics/", "docs/engine/")
NORMATIVE_EXCLUDED_PREFIXES = ("docs/engine/matrices/",)
PARITY_PREFIX = "docs/parity_ledger/"

KIND_RANK = {"path": 0, "symbol": 1, "term": 1, "importer": 2, "mechanism": 3}

COMMENT_KEYWORDS = re.compile(
    r"\b(invariants?|must|never|always|lifecycle|concurrent|concurrency|recover|recovery|restore|restored|"
    r"ack|acks|acknowledge|acknowledged|deterministic|determinism)\b",
    re.IGNORECASE,
)
MAX_COMMENT_HITS = 60

_PUBLIC_DEF = re.compile(r"^\s*(?:async\s+def|def|class)\s+([A-Za-z][A-Za-z0-9_]*)", re.MULTILINE)


class DirSource:
    """Reads from a working tree."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def read(self, path: str) -> Optional[str]:
        target = self.root / path
        try:
            if not target.is_file() or target.stat().st_size > MAX_DOC_BYTES:
                return None
            return target.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def list_paths(self, prefixes: Sequence[str]) -> List[str]:
        out: List[str] = []
        for prefix in prefixes:
            base = self.root / prefix
            if base.is_file():
                out.append(prefix)
            elif base.is_dir():
                out.extend(p.relative_to(self.root).as_posix() for p in sorted(base.rglob("*")) if p.is_file())
        return out


class GitRefSource:
    """Reads from a git ref, so a pinned replay never depends on the working tree."""

    def __init__(self, root: Path, ref: str):
        self.root = Path(root)
        self.ref = ref
        self._paths: Optional[List[str]] = None

    def _all_paths(self) -> List[str]:
        if self._paths is None:
            result = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", self.ref], cwd=self.root,
                capture_output=True, text=True, check=False,
            )
            self._paths = result.stdout.splitlines() if result.returncode == 0 else []
        return self._paths

    def read(self, path: str) -> Optional[str]:
        result = subprocess.run(
            ["git", "show", f"{self.ref}:{path}"], cwd=self.root, capture_output=True, check=False,
        )
        if result.returncode != 0 or len(result.stdout) > MAX_DOC_BYTES:
            return None
        return result.stdout.decode("utf-8", errors="replace")

    def list_paths(self, prefixes: Sequence[str]) -> List[str]:
        return [p for p in self._all_paths() if any(p == pre or p.startswith(pre) for pre in prefixes)]

    def read_many(self, paths: Iterable[str]) -> Dict[str, str]:
        """One `git cat-file --batch` process for the whole docs corpus (a `git show` per doc is slow)."""
        wanted = list(paths)
        proc = subprocess.run(
            ["git", "cat-file", "--batch"], cwd=self.root, capture_output=True, check=False,
            input="".join(f"{self.ref}:{p}\n" for p in wanted).encode("utf-8"),
        )
        out: Dict[str, str] = {}
        data, pos = proc.stdout, 0
        for path in wanted:
            end = data.find(b"\n", pos)
            if end < 0:
                break
            header = data[pos:end].split()
            pos = end + 1
            if len(header) == 3 and header[1] == b"blob":
                size = int(header[2])
                blob = data[pos:pos + size]
                pos += size + 1
                if size <= MAX_DOC_BYTES:
                    out[path] = blob.decode("utf-8", errors="replace")
        return out


def _corpus(source) -> Dict[str, str]:
    paths = [p for p in source.list_paths(("docs/", "README.md")) if Path(p).suffix in TEXT_SUFFIXES]
    if hasattr(source, "read_many"):
        return source.read_many(paths)
    return {p: text for p in paths if (text := source.read(p)) is not None}


def public_symbols(text: str) -> List[str]:
    """Non-underscore `def` and `class` names, nothing else."""
    return sorted(set(_PUBLIC_DEF.findall(text)))


def identifier_shaped(name: str) -> bool:
    """True for a name that cannot be an ordinary English word in prose: it has an underscore or two capitals.

    A one-word name such as `execute` or `entities` matches thousands of sentences, so it is not searched as a
    symbol. This is a rule about the shape of every name, not a list of words; the old term path (--old-term)
    still searches any word the caller names.
    """
    return "_" in name or sum(1 for ch in name if ch.isupper()) >= 2


def _frontmatter_status(text: str) -> Optional[str]:
    if not text.startswith("---"):
        return None
    block = text.split("---", 2)
    if len(block) < 3:
        return None
    match = re.search(r"^status:\s*([A-Za-z_-]+)", block[1], re.MULTILINE)
    return match.group(1).lower() if match else None


def exclusion_reason(path: str, text: str) -> Optional[str]:
    """The R3 history class of a doc, or None for a live doc."""
    if path in EXCLUDED_FILES:
        return EXCLUDED_FILES[path]
    for prefix, reason in EXCLUDED_PREFIXES:
        if path.startswith(prefix):
            return reason
    if _frontmatter_status(text) in HISTORICAL_STATUSES:
        return "historical-status"
    if path.startswith("docs/") and REVIEW_RECORD_STEM.search(Path(path).stem):
        return "review-record"
    return None


def is_normative(path: str) -> bool:
    if path.startswith(NORMATIVE_EXCLUDED_PREFIXES):
        return False
    if path.startswith(NORMATIVE_PREFIXES):
        return True
    return path.startswith("docs/architecture/") and path.endswith("_contract.md")


def _alternation(needles: Iterable[str], word: bool, flags: int = 0) -> Optional["re.Pattern[str]"]:
    items = sorted({n for n in needles if n}, key=len, reverse=True)
    if not items:
        return None
    body = "|".join(re.escape(n) for n in items)
    pattern = rf"(?<![\w]){'(?:' + body + ')'}(?![\w])" if word else rf"(?<![\w/.-])(?:{body})"
    return re.compile(pattern, flags)


def _path_needles(changed: Sequence[str]) -> List[str]:
    needles: List[str] = []
    for path in changed:
        needles.append(path)
        needles.append(Path(path).name)
        if path.endswith(".py"):
            needles.append(path[:-3].replace("/", "."))
    return needles


def _importers_regex(changed_py: Sequence[str], source) -> List[str]:
    importers: set = set()
    src_files = [p for p in source.list_paths(("src/",)) if p.endswith(".py")]
    patterns = []
    for path in changed_py:
        dotted = path[:-3].replace("/", ".")
        parent, _, leaf = dotted.rpartition(".")
        patterns.append((path, re.compile(
            rf"^\s*(?:from\s+{re.escape(dotted)}\s+import|import\s+{re.escape(dotted)}\b"
            rf"|from\s+{re.escape(parent)}\s+import\s+[^\n#]*\b{re.escape(leaf)}\b)", re.MULTILINE)))
    for candidate in src_files:
        text = source.read(candidate)
        if text is None:
            continue
        for changed_path, pattern in patterns:
            if candidate != changed_path and pattern.search(text):
                importers.add(candidate)
    return sorted(importers)


def _importers_graph(changed: Sequence[str], graph_path: Path) -> List[str]:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    file_of = {n["id"]: n.get("source_file") for n in graph.get("nodes", [])}
    changed_set = set(changed)
    found: set = set()
    for link in graph.get("links", []):
        if link.get("relation") not in ("imports", "imports_from"):
            continue
        target_file, source_file = file_of.get(link.get("target")), file_of.get(link.get("source"))
        if target_file in changed_set and source_file and source_file != target_file and source_file.startswith("src/"):
            found.add(source_file)
    return sorted(found)


def _mechanism_needles(changed: Sequence[str], source) -> Tuple[List[str], List[str]]:
    """(mechanism ids, class names) of entries whose `implemented_by` cites a changed path."""
    text = source.read("registries/mechanisms.yaml")
    if text is None or yaml is None:
        return [], []
    data = yaml.safe_load(text) or {}
    changed_set = set(changed)
    ids: List[str] = []
    names: List[str] = []
    for entry in data.get("mechanisms") or []:
        for item in entry.get("implemented_by") or []:
            if not isinstance(item, str):
                continue
            path, _, name = item.partition("::")
            if path in changed_set:
                ids.append(str(entry.get("id")))
                if name:
                    names.append(name.split(".")[0])
    return sorted(set(ids)), sorted(set(names))


def comment_hits(path: str, text: str) -> List[dict]:
    """F5: comment and docstring lines that state an invariant, lifecycle, concurrency or recovery rule."""
    lines = text.splitlines()
    wanted: Dict[int, str] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                wanted[tok.start[0]] = tok.string
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    for line_no in range(first.lineno, (first.end_lineno or first.lineno) + 1):
                        wanted[line_no] = lines[line_no - 1]
    except (SyntaxError, tokenize.TokenError, IndentationError):
        return []
    hits = [
        {"path": path, "line": n, "text": t.strip()[:MAX_HIT_TEXT]}
        for n, t in sorted(wanted.items()) if COMMENT_KEYWORDS.search(t)
    ]
    return hits


def _scan(text: str, patterns: Dict[str, "re.Pattern[str]"]) -> Tuple[List[dict], set]:
    hits: List[dict] = []
    kinds: set = set()
    for number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in patterns.items():
            if pattern.search(line):
                kinds.add(kind)
                if len(hits) < MAX_HITS_KEPT:
                    hits.append({"kind": kind, "line": number, "text": line.strip()[:MAX_HIT_TEXT]})
                break
    return hits, kinds


def search_docs_for_change(
    changed_files: Sequence[str],
    docs_source,
    head_source=None,
    base_source=None,
    old_terms: Sequence[str] = (),
    graph_path: Optional[Path] = None,
) -> dict:
    """Search the docs corpus for docs that a change to `changed_files` may leave stale.

    `docs_source` supplies the docs tree; `head_source` the changed files after the change (for public
    symbols and comments), defaulting to `docs_source`; `base_source`, when given, the files before it, so
    a public symbol present at base and absent at head becomes an old-behaviour term.
    """
    head_source = head_source or docs_source
    notes: List[str] = []
    changed = sorted(set(changed_files))
    changed_py = [p for p in changed if p.endswith(".py")]

    symbols: set = set()
    removed: set = set()
    comments: List[dict] = []
    for path in changed_py:
        head_text = head_source.read(path)
        head_syms = set(public_symbols(head_text)) if head_text is not None else set()
        symbols |= head_syms
        if head_text is not None:
            comments.extend(comment_hits(path, head_text))
        if base_source is not None:
            base_text = base_source.read(path)
            if base_text is not None:
                removed |= set(public_symbols(base_text)) - head_syms
    terms = sorted({t for t in old_terms if t})
    if base_source is None:
        notes.append("old-behaviour terms: --old-term only (no base to diff public symbols against)")
    else:
        notes.append(f"old-behaviour terms: --old-term plus {len(removed)} public symbol(s) at base and absent at head")

    if graph_path is not None:
        try:
            importers = _importers_graph(changed, graph_path)
            notes.append(f"importers: graph {graph_path.name} ({len(importers)} file(s))")
        except (OSError, ValueError, KeyError) as exc:
            importers = _importers_regex(changed_py, head_source)
            notes.append(f"importers: regex scan of src/ (graph unavailable: {type(exc).__name__}) ({len(importers)} file(s))")
    else:
        importers = _importers_regex(changed_py, head_source)
        notes.append(f"importers: regex scan of src/ at the head source ({len(importers)} file(s))")
    mech_ids, mech_names = _mechanism_needles(changed, head_source)
    notes.append(f"mechanisms: {len(mech_ids)} entr(y/ies) cite a changed path")

    searched_symbols = {s for s in symbols if identifier_shaped(s)}
    searched_removed = {s for s in removed if identifier_shaped(s)}
    notes.append(
        f"public symbols searched: {len(searched_symbols)} of {len(symbols)} "
        "(one-word names are not searched; see identifier_shaped)"
    )
    patterns: Dict[str, "re.Pattern[str]"] = {}
    for kind, pattern in (
        ("path", _alternation(_path_needles(changed), word=False)),
        ("symbol", _alternation(searched_symbols, word=True)),
        ("term", _alternation(set(terms) | searched_removed, word=True, flags=re.IGNORECASE)),
        ("importer", _alternation(_path_needles(importers), word=False)),
        ("mechanism", _alternation(set(mech_ids) | set(mech_names), word=True)),
    ):
        if pattern is not None:
            patterns[kind] = pattern

    required: List[dict] = []
    candidate: List[dict] = []
    excluded: List[dict] = []
    corpus = _corpus(docs_source)
    notes.append(f"docs searched: {len(corpus)} file(s) under docs/ and README.md")
    for path, text in sorted(corpus.items()):
        hits, kinds = _scan(text, patterns)
        if not hits:
            continue
        item = {"path": path, "kinds": sorted(kinds, key=KIND_RANK.get), "hits": hits}
        reason = exclusion_reason(path, text)
        if reason:
            item["reason"] = reason
            excluded.append(item)
        elif is_normative(path) and kinds & {"path", "symbol", "term"}:
            item["reason"] = "normative doc with a direct hit; confirm it states the changed fact"
            required.append(item)
        else:
            if path.startswith(PARITY_PREFIX):
                item["owner"] = "parity-updater"
            candidate.append(item)
    candidate.sort(key=lambda i: (min(KIND_RANK[k] for k in i["kinds"]), i["path"]))
    return {
        "changed_files": changed,
        "required": required,
        "candidate": candidate,
        "excluded": excluded,
        "comment_hits": comments[:MAX_COMMENT_HITS],
        "notes": notes + [
            "required means normative tier plus a direct hit; the caller confirms each entry",
            "the paths given are the changed paths known at this point; run again on the real diff at the gate",
        ],
    }


def _graph_for(root: Path) -> Optional[Path]:
    """The local graphify graph, only when it was built at this worktree's HEAD."""
    graph = root / "graphify-out" / "graph.json"
    if not graph.is_file():
        return None
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    try:
        built = json.loads(graph.read_text(encoding="utf-8")).get("built_at_commit")
    except (OSError, ValueError):
        return None
    return graph if head.returncode == 0 and built == head.stdout.strip() else None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--changed-file", action="append", default=[], metavar="PATH")
    parser.add_argument("--old-term", action="append", default=[], metavar="TERM")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--docs-ref", help="git ref whose docs tree is searched (default: the working tree)")
    parser.add_argument("--head-ref", help="git ref holding the changed files after the change")
    parser.add_argument("--base-ref", help="git ref holding the changed files before it")
    args = parser.parse_args(argv)
    root = Path(args.repo_root).resolve()

    def source(ref: Optional[str]):
        return GitRefSource(root, ref) if ref else DirSource(root)

    docs_source = source(args.docs_ref)
    head_source = source(args.head_ref) if (args.head_ref or args.docs_ref) else docs_source
    base_source = GitRefSource(root, args.base_ref) if args.base_ref else None
    pinned = bool(args.docs_ref or args.head_ref)
    graph = None if pinned else _graph_for(root)
    result = search_docs_for_change(
        args.changed_file, docs_source, head_source, base_source, args.old_term, graph,
    )
    print("MARKER:" + json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
