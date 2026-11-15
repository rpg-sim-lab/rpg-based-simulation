"""Advisory check: which ``src/systems`` classes and functions does the authoritative pipeline never reach, and which tests import them without saying why
(TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS). Report only, in the style of ``marker_check.py``: the exit code is always 0.

Found case: ``fused_strategic_pass``'s pursuit regression test exercised ``StrategicRedirectionSystem.enforce``. That class is only re-exported and is not wired into
``src/engine/pipeline.py``, so the test suggested coverage of the live path that it did not give.

How the wired set is computed (from the code at run time, never from ``docs/performance/phase_inventory.md``):

* The root is ``src/engine/pipeline.py``. ``tools.perf.phase_inventory.inventory_pipeline`` (the source ``phase_inventory.py`` uses) is run on its text and its
  ``run_phase`` call count is printed, so the report shows the root was read as the refinement pipeline. All of the module's code is the root, a superset of
  ``refine()``'s own calls (helpers it calls are reached too), which errs toward "wired".
* A name counts as *used* by a module when it appears in that module's code outside import statements and ``__all__``, as a bare name or as an attribute of an
  imported module. An import that is never used, and a name listed only in ``__all__``, is a re-export and reaches nothing.
* A used name is followed through re-exports to its defining module (``from src.systems.redirection import X`` resolves to the module that defines ``X``). A defining
  module of a used symbol, and a module used as a module, is *reached*, and its own code is scanned for uses in turn. Importing a package does not reach what its
  ``__init__`` re-exports.

Each ``src/systems`` top-level public class or function is then ``wired`` (used by name from a reached module), ``dispatch-reached`` (its module is reached but no
reached code names it: it may be called through a registry, a string or ``getattr``, so it is neither wired nor unwired), or ``unwired``. An unwired symbol is listed
with how it is referenced: ``used only by src module(s) the pipeline does not reach`` (a real caller outside the pipeline, e.g. a campaign orchestrator the kernel
runs: the likeliest false positive for "never runs"), ``import-only`` (a src module imports it and never uses it), ``re-export only`` (listed in ``__all__`` or a facade
and nothing in src uses it), ``test-only`` (only tests name it) or ``unreferenced``.

A test file is flagged when it imports an unwired symbol and carries no ``pytest.mark.unwired_subject("<reason>")`` (as ``pytestmark`` or on any test in the file).
A marked file is listed as acknowledged with its reason.

Known limits: dynamic dispatch (registries, ``getattr``, strings) is invisible and gives ``dispatch-reached``; the kernel and the scheduler are not roots, so a system run
by them and not by the pipeline reads as unwired (``--also-root src/engine/kernel.py`` adds roots); a symbol used only inside its own module counts as used only if its
module is reached.

Run: ``python3 -m tools.test_architecture.unwired_subject_check [--json] [--also-root PATH ...] [--repo DIR]``. Exit status is always 0.
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
PIPELINE = "src/engine/pipeline.py"
SUBJECT_ROOT = "src/systems"
TESTS = "tests"
MARKER = "unwired_subject"


@dataclass
class Module:
    name: str
    path: Path
    is_package: bool
    tree: ast.Module
    defs: Set[str] = field(default_factory=set)  # top-level class/function names (public and private)
    imports: Dict[str, Tuple[str, Optional[str]]] = field(default_factory=dict)  # local name -> (module, attr or None)
    all_names: Set[str] = field(default_factory=set)
    uses: Set[str] = field(default_factory=set)  # local names used outside imports and __all__
    use_attrs: Set[Tuple[str, str]] = field(default_factory=set)  # (local name, attribute) used outside imports


def _module_name(root: Path, path: Path) -> Tuple[str, bool]:
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def _is_type_checking(node: ast.If) -> bool:
    t = node.test
    return (isinstance(t, ast.Name) and t.id == "TYPE_CHECKING") or (isinstance(t, ast.Attribute) and t.attr == "TYPE_CHECKING")


def _resolve_from(module: str, is_package: bool, node: ast.ImportFrom) -> Optional[str]:
    if node.level == 0:
        return node.module
    base = module.split(".") if is_package else module.split(".")[:-1]
    if node.level > 1:
        base = base[: len(base) - (node.level - 1)]
    return ".".join(base + ([node.module] if node.module else []))


class _Scan(ast.NodeVisitor):
    def __init__(self, mod: Module):
        self.mod = mod
        self._in_all = False

    def visit_If(self, node: ast.If) -> None:
        if _is_type_checking(node):
            for child in node.orelse:
                self.visit(child)
            return
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.asname:
                self.mod.imports[alias.asname] = (alias.name, None)
            else:
                top = alias.name.split(".")[0]
                self.mod.imports[top] = (top, None)
                self.mod.imports[alias.name] = (alias.name, None)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        target = _resolve_from(self.mod.name, self.mod.is_package, node)
        if target is None:
            return
        for alias in node.names:
            if alias.name != "*":
                self.mod.imports[alias.asname or alias.name] = (target, alias.name)

    def visit_Assign(self, node: ast.Assign) -> None:
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
            if isinstance(node.value, (ast.List, ast.Tuple)):
                self.mod.all_names |= {e.value for e in node.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)}
            return
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.mod.uses.add(node.id)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # a.b.c: record the dotted chain's root name and the first attribute, and the full dotted text for ``import a.b.c`` style uses
        chain: List[str] = [node.attr]
        cur: ast.AST = node.value
        while isinstance(cur, ast.Attribute):
            chain.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name) and isinstance(cur.ctx, ast.Load):
            chain.append(cur.id)
            chain.reverse()
            for i in range(1, len(chain)):  # every prefix of the dotted chain, with the attribute taken from it
                self.mod.use_attrs.add((".".join(chain[:i]), chain[i]))
            self.mod.uses.add(chain[0])
            return
        self.generic_visit(node)


def load_modules(root: Path, subtrees: Iterable[str]) -> Dict[str, Module]:
    mods: Dict[str, Module] = {}
    for sub in subtrees:
        for path in sorted((root / sub).rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError, OSError):
                continue
            name, is_pkg = _module_name(root, path)
            mod = Module(name, path, is_pkg, tree)
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    mod.defs.add(node.name)
            _Scan(mod).visit(tree)
            mods[name] = mod
    return mods


def _origin(mods: Dict[str, Module], module: str, name: str, seen: Optional[Set[Tuple[str, str]]] = None) -> Tuple[str, str]:
    """The (defining module, name) behind ``module.name``, following re-exports."""
    seen = seen if seen is not None else set()
    if (module, name) in seen or module not in mods:
        return module, name
    seen.add((module, name))
    m = mods[module]
    if name in m.defs:
        return module, name
    if name in m.imports:
        target, attr = m.imports[name]
        if attr is not None:
            return _origin(mods, target, attr, seen)
    return module, name


def _used_targets(mods: Dict[str, Module], mod: Module) -> Tuple[Set[Tuple[str, str]], Set[str]]:
    """(symbols, modules) this module's code uses: (defining module, name) pairs and module names."""
    symbols: Set[Tuple[str, str]] = set()
    modules: Set[str] = set()
    for local, (target, attr) in mod.imports.items():
        if attr is None:  # ``import a.b`` / ``import a.b as m``: used as a module when its name or a dotted chain is used
            if local in mod.uses or any(c == local for c, _a in mod.use_attrs):
                modules.add(target)
            for chain, attr_name in mod.use_attrs:
                if chain == local or chain.startswith(local + "."):
                    full = (target if chain == local else target + chain[len(local):]) + "." + attr_name
                    if full in mods:
                        modules.add(full)
                    elif target in mods:
                        symbols.add(_origin(mods, target, attr_name))
            continue
        if f"{target}.{attr}" in mods:  # ``from pkg import submodule``
            if local in mod.uses:
                modules.add(f"{target}.{attr}")
            for chain, attr_name in mod.use_attrs:
                if chain == local:
                    symbols.add(_origin(mods, f"{target}.{attr}", attr_name))
            continue
        if local in mod.uses:
            symbols.add(_origin(mods, target, attr))
    return symbols, modules


def reach(mods: Dict[str, Module], roots: Iterable[str]) -> Tuple[Set[str], Set[Tuple[str, str]]]:
    """(reached modules, used symbols) from the roots, by the use rules in the module docstring."""
    reached: Set[str] = set()
    used: Set[Tuple[str, str]] = set()
    queue = [r for r in roots if r in mods]
    while queue:
        name = queue.pop()
        if name in reached:
            continue
        reached.add(name)
        symbols, modules = _used_targets(mods, mods[name])
        used |= symbols
        for target in [m for m, _n in symbols] + sorted(modules):
            if target in mods and target not in reached:
                queue.append(target)
    return reached, used


def _subject_symbols(mods: Dict[str, Module]) -> List[Tuple[str, str, int, str]]:
    out = []
    for name, mod in sorted(mods.items()):
        if not (name == "src.systems" or name.startswith("src.systems.")):
            continue
        for node in mod.tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                out.append((name, node.name, node.lineno, "class" if isinstance(node, ast.ClassDef) else "function"))
    return out


def _references(mods: Dict[str, Module], tests: Dict[str, Module]) -> Dict[Tuple[str, str], Dict[str, Set[str]]]:
    """For each (defining module, name): who names it, by kind, across src (``reexport``, ``import``) and tests (``test``)."""
    refs: Dict[Tuple[str, str], Dict[str, Set[str]]] = {}

    def add(key: Tuple[str, str], kind: str, who: str) -> None:
        refs.setdefault(key, {}).setdefault(kind, set()).add(who)

    for name, mod in mods.items():
        symbols, _modules = _used_targets(mods, mod)
        for local, (target, attr) in mod.imports.items():
            if attr is None or f"{target}.{attr}" in mods:
                continue
            key = _origin(mods, target, attr)
            if key[0] == name:
                continue
            kind = "reexport" if local in mod.all_names else "use" if key in symbols else "import"
            add(key, kind, name)
    for name, mod in tests.items():
        for local, (target, attr) in mod.imports.items():
            if attr is None or f"{target}.{attr}" in mods:
                continue
            add(_origin(mods, target, attr), "test", name)
        symbols, _modules = _used_targets(mods | tests, mod)
        for key in symbols:
            add(key, "test", name)
    return refs


def _marker_reasons(mod: Module) -> List[str]:
    reasons: List[str] = []
    for node in ast.walk(mod.tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr == MARKER:
                arg = node.args[0] if node.args else None
                reasons.append(arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else "")
    return reasons


def analyse(repo: Path = REPO, also_roots: Iterable[str] = ()) -> Dict[str, Any]:
    from tools.perf.phase_inventory import inventory_pipeline

    pipeline_path = repo / PIPELINE
    pipeline_text = pipeline_path.read_text(encoding="utf-8") if pipeline_path.exists() else ""
    inventory = inventory_pipeline(pipeline_text) if pipeline_text else {"found": False, "run_phase_calls": []}
    mods = load_modules(repo, ["src"])
    tests = load_modules(repo, [TESTS]) if (repo / TESTS).is_dir() else {}
    root_names = [_module_name(repo, repo / PIPELINE)[0]] + [_module_name(repo, repo / r)[0] for r in also_roots]
    reached, used = reach(mods, root_names)
    refs = _references(mods, tests)
    unwired: List[Dict[str, Any]] = []
    dispatch: List[Dict[str, Any]] = []
    wired = 0
    unwired_keys: Set[Tuple[str, str]] = set()
    for module, name, line, kind in _subject_symbols(mods):
        key = (module, name)
        if key in used:
            wired += 1
            continue
        row = {"symbol": f"{module}.{name}", "file": str(mods[module].path.relative_to(repo)), "line": line, "kind": kind}
        if module in reached:
            dispatch.append(row)
            continue
        by_kind = refs.get(key, {})
        if "use" in by_kind:
            how = "used only by src module(s) the pipeline does not reach"
        elif "import" in by_kind:
            how = "import-only (imported, never used)"
        elif "reexport" in by_kind:
            how = "re-export only"
        elif "test" in by_kind:
            how = "test-only"
        else:
            how = "unreferenced"
        unwired.append({**row, "referenced": how, "src_importers": sorted(by_kind.get("use", set()) | by_kind.get("import", set()) | by_kind.get("reexport", set())), "tests": sorted(by_kind.get("test", set()))})
        unwired_keys.add(key)
    flagged: List[Dict[str, Any]] = []
    acknowledged: List[Dict[str, Any]] = []
    for tname, tmod in sorted(tests.items()):
        hit = sorted(f"{m}.{n}" for (m, n) in unwired_keys if tname in refs.get((m, n), {}).get("test", set()))
        if not hit:
            continue
        rel = str(tmod.path.relative_to(repo))
        reasons = _marker_reasons(tmod)
        if reasons:
            acknowledged.append({"file": rel, "unwired": hit, "reasons": reasons})
        else:
            flagged.append({"file": rel, "unwired": hit})
    return {
        "pipeline": {"path": PIPELINE, "found": bool(inventory.get("found")), "run_phase_calls": len(inventory.get("run_phase_calls", []))},
        "roots": root_names,
        "counts": {"subject_symbols": wired + len(dispatch) + len(unwired), "wired": wired, "dispatch_reached": len(dispatch), "unwired": len(unwired),
                   "flagged_tests": len(flagged), "acknowledged_tests": len(acknowledged)},
        "unwired": unwired, "dispatch_reached": dispatch, "flagged_tests": flagged, "acknowledged_tests": acknowledged,
    }


def render(report: Dict[str, Any]) -> str:
    c = report["counts"]
    lines = [
        f"# unwired-subject check (advisory): root {report['pipeline']['path']} ({report['pipeline']['run_phase_calls']} run_phase calls read), roots {report['roots']}",
        f"# {c['subject_symbols']} src/systems public symbols: {c['wired']} wired, {c['dispatch_reached']} dispatch-reached, {c['unwired']} unwired; {c['flagged_tests']} test file(s) flagged, {c['acknowledged_tests']} acknowledged",
        "", "## unwired src/systems symbols",
    ]
    lines += [f"{r['symbol']} ({r['kind']}, {r['file']}:{r['line']}): {r['referenced']}{' [' + ', '.join(r['src_importers']) + ']' if r['src_importers'] else ''}; tests: {len(r['tests'])}" for r in report["unwired"]] or ["(none)"]
    lines += ["", "## tests that import an unwired symbol without pytest.mark.unwired_subject"]
    lines += [f"{t['file']}: {', '.join(t['unwired'])}" for t in report["flagged_tests"]] or ["(none)"]
    lines += ["", "## acknowledged (marked) tests"]
    lines += [f"{t['file']}: {', '.join(t['unwired'])} -- {'; '.join(t['reasons'])}" for t in report["acknowledged_tests"]] or ["(none)"]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--also-root", action="append", default=[], metavar="PATH", help="a further root module path (e.g. src/engine/kernel.py)")
    ap.add_argument("--repo", type=Path, default=REPO)
    args = ap.parse_args(argv)
    report = analyse(args.repo, args.also_root)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render(report))
    return 0  # advisory: findings are printed, never enforced


if __name__ == "__main__":
    sys.exit(main())
