#!/usr/bin/env python3
"""Project numbers from one tool: counts of the repository at a git ref, and the generated page that states them.

Every count is read from git objects at the ref (`ls-tree`, `cat-file --batch`, `log --first-parent`), never from the working
tree, never over the network, and never by importing repository code. The page states each count with its counting rule, so a
doc or a review cites the page instead of re-deriving a number (TCK-20261108-PROJECT-FACTS-PAGE-GENERATED, plan
`agent-working/lead/docs_as_review_source_plan.md` P2).

    python3 tools/project_stats.py                 # print the page for HEAD
    python3 tools/project_stats.py --ref <sha>     # print the page for another ref
    python3 tools/project_stats.py --write         # write docs/architecture/project_facts.md for the ref
    python3 tools/project_stats.py --check         # exit 1 when the committed page is not what the tool produces at the page's own ref

`--check` regenerates at the ref named in the page's header and compares bytes, so the page goes stale when the tool or its
rules change or someone edits it by hand, not each time the code grows. When HEAD has moved past the page's ref it prints one
note; that is not a failure. Two runs at one ref are byte-identical: there are no timestamps and the order is fixed.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PAGE_REL = Path("docs/architecture/project_facts.md")
TOOL_REL = "tools/project_stats.py"
HEADER_RE = re.compile(r"Generated from commit `([0-9a-f]{40})` by `tools/project_stats.py`")
TICKET_FOLDERS = ("todos", "inprogress", "done")
METRIC_KINDS = ("Counter", "Gauge", "Histogram", "Summary", "Info")
METRIC_CONSTRUCTORS = {*METRIC_KINDS, *(f"{k}MetricFamily" for k in METRIC_KINDS)}
METRIC_NAME = re.compile(r"[a-zA-Z_:][a-zA-Z0-9_:]*$")
PR_SUBJECT = re.compile(r"\(#(\d+)\)$")


class StatsError(Exception):
    """The ref or a counted file could not be read."""


@dataclass(frozen=True)
class Fact:
    label: str
    value: str
    rule: str


@dataclass(frozen=True)
class Section:
    title: str
    facts: tuple[Fact, ...]


class Repo:
    """Read-only view of one commit: file list, blobs and first-parent history."""

    def __init__(self, root: Path, ref: str) -> None:
        self.root = root
        self.sha = self._git("rev-parse", "--verify", f"{ref}^{{commit}}").decode().strip()
        listing = self._git("ls-tree", "-r", "-z", "--name-only", self.sha)
        self.paths = sorted(p for p in listing.decode("utf-8").split("\0") if p)
        self._blobs: dict[str, bytes] = {}

    def _git(self, *args: str, stdin: bytes | None = None) -> bytes:
        done = subprocess.run(["git", *args], cwd=self.root, input=stdin, capture_output=True, check=False)
        if done.returncode != 0:
            raise StatsError(f"git {' '.join(args)}: {done.stderr.decode(errors='replace').strip()}")
        return done.stdout

    def load(self, paths: list[str]) -> None:
        """Read many blobs in one `cat-file --batch` call."""
        wanted = [p for p in paths if p not in self._blobs]
        if not wanted:
            return
        out = self._git("cat-file", "--batch", stdin="".join(f"{self.sha}:{p}\n" for p in wanted).encode("utf-8"))
        pos = 0
        for path in wanted:
            end = out.index(b"\n", pos)
            header = out[pos:end].split()
            if len(header) != 3 or header[1] != b"blob":
                raise StatsError(f"{path}: not a blob at {self.sha}")
            size = int(header[2])
            self._blobs[path] = out[end + 1 : end + 1 + size]
            pos = end + 1 + size + 1

    def read(self, path: str) -> bytes:
        self.load([path])
        return self._blobs[path]

    def text(self, path: str) -> str:
        return self.read(path).decode("utf-8", errors="replace")

    def under(self, prefix: str, suffix: str = "") -> list[str]:
        return [p for p in self.paths if p.startswith(prefix) and p.endswith(suffix)]

    def first_parent_log(self) -> list[tuple[str, str]]:
        """(commit date YYYY-MM-DD, subject) newest first, first-parent only."""
        out = self._git("log", "--first-parent", "--format=%cs%x09%s", self.sha).decode("utf-8")
        return [tuple(line.split("\t", 1)) for line in out.splitlines() if "\t" in line]  # type: ignore[misc]


def _lines(blob: bytes) -> int:
    return blob.count(b"\n") + (1 if blob and not blob.endswith(b"\n") else 0)


def code_facts(repo: Repo) -> Section:
    src = repo.under("src/", ".py")
    repo.load(src)
    tests = [p for p in repo.under("tests/", ".py") if Path(p).name.startswith("test_")]
    repo.load(tests)
    functions = unparsable = 0
    for path in tests:
        try:
            tree = ast.parse(repo.read(path))
        except SyntaxError:
            unparsable += 1
            continue
        functions += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_") for n in ast.walk(tree))
    return Section("Code and tests", (
        Fact("src modules", str(len(src)), "every `*.py` file under `src/` at the ref (a module is one file, `__init__.py` included)"),
        Fact("src lines", str(sum(_lines(repo.read(p)) for p in src)), "physical lines of those files, blank lines and comments included"),
        Fact("test files", str(len(tests)), "every file named `test_*.py` under `tests/`"),
        Fact("static test functions", str(functions),
             f"every `def test_*` found by `ast` in those files, methods and nested functions included; a parametrized test counts once, not per case; {unparsable} file(s) did not parse and are not counted"),
    ))


def ticket_facts(repo: Repo) -> Section:
    facts = []
    for folder in TICKET_FOLDERS:
        n = sum(Path(p).name.startswith("TCK-") for p in repo.under(f"agent-working/tickets/{folder}/", ".md"))
        facts.append(Fact(f"tickets in {folder}/", str(n), f"files named `TCK-*.md` anywhere under `agent-working/tickets/{folder}/` (epic folders included; SEQUENCE.md and INDEX.md are not tickets)"))
    prs = [(d, s) for d, s in repo.first_parent_log() if PR_SUBJECT.search(s)]
    span = f"{prs[-1][0]} to {prs[0][0]}" if prs else "none"
    facts.append(Fact("merged PRs", f"{len(prs)} (first merge {prs[-1][0] if prs else '-'}, last {prs[0][0] if prs else '-'})",
                      f"first-parent commits at the ref whose subject ends `(#N)` (squash merges); the dates are commit dates of the first and last such commit ({span}); a PR merged by another method is not counted"))
    return Section("Tickets and pull requests", tuple(facts))


def process_facts(repo: Repo) -> Section:
    roles = yaml.safe_load(repo.text("registries/session_roles.yaml")).get("roles", [])
    agents = [Path(p).name for p in repo.under(".claude/agents/", ".md")]
    skills = {p.split("/")[2] for p in repo.under(".claude/skills/") if p.endswith("/SKILL.md")}
    hooks = json.loads(repo.text(".claude/settings.json")).get("hooks", {})
    per_event = {event: sum(len(group.get("hooks", [])) for group in groups) for event, groups in sorted(hooks.items())}
    return Section("Agents and process", (
        Fact("session roles", str(len(roles)), "entries of `roles:` in `registries/session_roles.yaml`"),
        Fact("session role cards", str(sum(a.startswith("session-") for a in agents)), "`.claude/agents/session-*.md` files (generated)"),
        Fact("subagents", str(sum(not a.startswith("session-") for a in agents)), "other `.claude/agents/*.md` files"),
        Fact("skills", str(len(skills)), "directories under `.claude/skills/` that hold a `SKILL.md`"),
        Fact("hooks", f"{sum(per_event.values())} in {len(per_event)} events",
             "command entries under `hooks` in `.claude/settings.json`: " + ", ".join(f"{k} {v}" for k, v in per_event.items())),
    ))


def parity_facts(repo: Repo) -> Section:
    files = [p for p in repo.under("docs/parity_ledger/", ".yaml")]
    repo.load(files)
    status: Counter[str] = Counter()
    priority: Counter[str] = Counter()
    both: Counter[tuple[str, str]] = Counter()
    total = 0
    for path in files:
        data = yaml.safe_load(repo.read(path))
        entries = data if isinstance(data, list) else []
        total += len(entries)
        for e in entries:
            s, pr = str(e.get("status")), str(e.get("priority"))
            status[s] += 1
            priority[pr] += 1
            both[(s, pr)] += 1
    rule = "items of the top-level list in each `docs/parity_ledger/*.yaml` file (`schema.json` and `README.md` are not ledgers); one item is one entry"
    cells = ", ".join(f"{s}/{p} {n}" for (s, p), n in sorted(both.items()))
    return Section("Parity ledger", (
        Fact("ledger files", str(len(files)), "`docs/parity_ledger/*.yaml`"),
        Fact("entries", str(total), rule),
        Fact("entries by status", ", ".join(f"{k} {v}" for k, v in sorted(status.items())), "the `status` of each entry"),
        Fact("entries by priority", ", ".join(f"{k} {v}" for k, v in sorted(priority.items())), "the `priority` of each entry"),
        Fact("entries by status/priority", cells, "the pair `status/priority` of each entry"),
    ))


def contract_facts(repo: Repo) -> Section:
    toml = tomllib.loads(repo.text("codebase/structure/importlinter.toml"))
    contracts = toml.get("tool", {}).get("importlinter", {}).get("contracts", [])
    edges = [ln for ln in repo.text("codebase/structure/import_layers_baseline.txt").splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    return Section("Import contracts", (
        Fact("import contracts", str(len(contracts)), "entries of `tool.importlinter.contracts` in `codebase/structure/importlinter.toml`"),
        Fact("baseline edges", str(len(edges)), "non-blank, non-comment lines of `codebase/structure/import_layers_baseline.txt`; each is one accepted layer violation"),
    ))


def _metric_names(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        ctor = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        if ctor not in METRIC_CONSTRUCTORS:
            continue
        named = len(node.args) + sum(k.arg in {"name", "documentation"} for k in node.keywords)
        arg = node.args[0] if node.args else next((k.value for k in node.keywords if k.arg == "name"), None)
        # a Prometheus constructor takes (name, documentation); `collections.Counter(iterable)` takes one argument and is not counted
        if named >= 2 and isinstance(arg, ast.Constant) and isinstance(arg.value, str) and METRIC_NAME.match(arg.value):
            names.add(arg.value)
    return names


def observability_facts(repo: Repo) -> Section:
    src = repo.under("src/", ".py")
    repo.load(src)
    names: set[str] = set()
    for path in src:
        text = repo.text(path)
        if "prometheus_client" not in text:
            continue
        try:
            names |= _metric_names(ast.parse(text))
        except SyntaxError:
            continue
    rule_files = [p for p in repo.under("docker/grafana/provisioning/alerting/", ".yaml") if Path(p).name.startswith("rules-")]
    repo.load(rule_files)
    per_file = {Path(p).name: sum(len(g.get("rules", [])) for g in (yaml.safe_load(repo.read(p)) or {}).get("groups", [])) for p in rule_files}
    return Section("Observability", (
        Fact("metric families", str(len(names)),
             "distinct literal names (first argument) of `prometheus_client` constructor calls with a name and a documentation argument: `Counter`, `Gauge`, `Histogram`, `Summary`, `Info` and their `*MetricFamily` forms, found by `ast` in the `src/` files that mention `prometheus_client`; a name built at run time is not counted"),
        Fact("alert rules", f"{sum(per_file.values())}",
             "`groups[].rules[]` entries of `docker/grafana/provisioning/alerting/rules-*.yaml`: " + ", ".join(f"{k} {v}" for k, v in sorted(per_file.items()))),
    ))


SECTIONS: tuple[Callable[[Repo], Section], ...] = (
    code_facts, ticket_facts, process_facts, parity_facts, contract_facts, observability_facts,
)


def render(repo: Repo) -> str:
    out = [
        "---", "status: active", "layer: architecture", "authority: P2", "audience: agent", "tags: [architecture, documentation]", "---", "",
        "# Project facts", "",
        f"Generated from commit `{repo.sha}` by `tools/project_stats.py`. Do not edit by hand: a hand edit fails `--check`.",
        "Regenerate with:", "", "```", "python3 tools/project_stats.py --write", "python3 tools/project_stats.py --check", "```", "",
        "Counts are as of that commit, read from git objects, not from a working tree. Cite this page instead of re-deriving a number; "
        "the counting rule beside each count says what it includes, so a different number from a different method is a different rule, not a conflict.", "",
    ]
    for build in SECTIONS:
        section = build(repo)
        out += [f"## {section.title}", "", "| What | Count | Counting rule |", "|---|---|---|"]
        out += [f"| {f.label} | {f.value} | {f.rule} |" for f in section.facts]
        out.append("")
    return "\n".join(out)


def check(root: Path, page: Path) -> tuple[int, list[str]]:
    """(exit code, lines to print)."""
    if not page.is_file():
        return 1, [f"project_stats: {page} does not exist; run `python3 tools/project_stats.py --write`"]
    committed = page.read_text(encoding="utf-8")
    found = HEADER_RE.search(committed)
    if not found:
        return 1, [f"project_stats: {page} has no `Generated from commit ... by tools/project_stats.py` header"]
    try:
        fresh = render(Repo(root, found.group(1)))
    except StatsError as exc:
        return 1, [f"project_stats: cannot regenerate at the page's ref {found.group(1)[:9]}: {exc}"]
    if fresh != committed:
        a, b = fresh.splitlines(), committed.splitlines()
        line = next((i for i, (x, y) in enumerate(zip(a, b), 1) if x != y), min(len(a), len(b)) + 1)
        return 1, [f"project_stats: {page} differs from the tool's output at {found.group(1)[:9]} (first difference at line {line}); "
                   "regenerate with `python3 tools/project_stats.py --write`, never edit the page by hand"]
    lines = [f"project_stats: {page} matches the tool at {found.group(1)[:9]}"]
    try:
        head = Repo(root, "HEAD").sha
        if head != found.group(1):
            behind = subprocess.run(["git", "rev-list", "--count", f"{found.group(1)}..{head}"], cwd=root, capture_output=True, text=True, check=False).stdout.strip()
            lines.append(f"note: HEAD is {behind or 'some'} commit(s) past the page's ref; counts are as of the page's ref (not a failure)")
    except StatsError:
        pass
    return 0, lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--ref", default="HEAD", help="git ref to count (default HEAD)")
    parser.add_argument("--write", action="store_true", help=f"write {PAGE_REL} for the ref")
    parser.add_argument("--check", action="store_true", help="exit 1 when the committed page differs from the tool's output at the page's own ref")
    args = parser.parse_args(argv)
    page = args.root / PAGE_REL
    if args.check:
        code, lines = check(args.root, page)
        print("\n".join(lines), file=sys.stderr if code else sys.stdout)
        return code
    try:
        text = render(Repo(args.root, args.ref))
    except StatsError as exc:
        print(f"project_stats: {exc}", file=sys.stderr)
        return 2
    if args.write:
        page.parent.mkdir(parents=True, exist_ok=True)
        page.write_text(text, encoding="utf-8")
        print(f"wrote {PAGE_REL}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
