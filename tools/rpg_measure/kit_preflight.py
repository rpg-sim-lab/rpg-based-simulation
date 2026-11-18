"""Preflight for a measurement kit (spy, probe, runner, summarizer): prove it on BOTH frozen trees before its run (TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-...).

Stdlib only, like ``env_digest.py``. Usage::

    python tools/rpg_measure/kit_preflight.py <manifest.json> --tree <A> --tree <B> [--ticks 10] [--python <interp>] [--out table.md]

Exit 0 only when every check passed. The output is a PASS/FAIL table with the input shas, to paste into the S9 packet with the evidence label ``executed``.

Manifest (hand-written JSON; kit files are resolved relative to the manifest's directory)::

    {"kit": "name", "version": 1,
     "files": [{"path": "probe.py", "sha256": "..."}, {"path": "run.sh", "sha256": "...", "role": "runner"}],
     "processes": [{
        "name": "probe",
        "entry": ["{python}", "-I", "{file:probe.py}", "{world}", "{seed}", "{ticks}", "{out}"],
        "env": {"PYTHONHASHSEED": "0"},
        "heavy": true,
        "import_files": ["probe.py"],
        "fixture": {"world": "frontier_living_world", "seed": 42, "ticks": 10},
        "output": {"fields": [{"path": "rows[*].failure_reason", "may_be_constant": false, "defaults": [null, 0, "", false]}]},
        "guards": {"ok_regex": "PROBE OK", "bad_regex": "TRACEBACK", "error_log_regex": "optional"},
        "hooks": [{"name": "perception_wrap", "count_path": "hooks.perception_wrap"}],
        "wraps": [{"target": "src.engine.gate:PerceptionGate.can_perceive", "wrapper": "probe.py:spy"}]}]}

Checks: (a) every kit file exists at its sha256; (f) every ``*.py`` a runner or shell file names is a manifest file; (h) every heavy kit python file matches the shared gate's
heavy-word pattern (``RPG_HEAVY_WORDS`` in ``busy_gate.sh``), else other lanes' gates cannot see the job. Per tree and process: (b) each import file loads under
``python -I`` with cwd = the tree; (g) each declared wrapper's signature matches its target's; (c) the fixture run (at most ``--ticks`` ticks) exits 0; (d) every recorded
field is present and not a constant None/default across all entities and ticks unless declared ``may_be_constant``; (e) the ok guard hit, the bad guard not, ERROR+ log lines 0,
every claimed hook hit at least once.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

HERE = Path(__file__).resolve().parent
DEFAULT_PYTHON = "/mnt/data/venv-sync2/bin/python"
DEFAULT_BUSY_GATE = "/mnt/data2/rpg-measure/lib/busy_gate.sh"
DEFAULT_DEFAULTS: List[Any] = [None, "", 0, False, [], {}]
DEFAULT_ERROR_LOG_REGEX = r"(?m)^\s*(?:ERROR|CRITICAL)\b|\[(?:ERROR|CRITICAL)\]|:(?:ERROR|CRITICAL):"
TIMEOUT_SECONDS = 600

PASS, FAIL = "PASS", "FAIL"
Row = Tuple[str, str, str, str]  # (check, scope, status, detail)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---- (a) files -----------------------------------------------------------------------------------------------------------------------------

def check_files(manifest: dict, base: Path) -> List[Row]:
    rows: List[Row] = []
    for entry in manifest.get("files", []):
        path = base / entry["path"]
        if not path.is_file():
            rows.append(("a files", entry["path"], FAIL, "missing"))
            continue
        got = sha256_of(path)
        ok = got == entry["sha256"]
        rows.append(("a files", entry["path"], PASS if ok else FAIL, f"sha256 {got[:16]}" + ("" if ok else f" != manifest {entry['sha256'][:16]}")))
    return rows


# ---- (f) runner references -----------------------------------------------------------------------------------------------------------------

_PY_TOKEN = re.compile(r"[\w./${}\-]*\.py\b")


def check_runner_references(manifest: dict, base: Path) -> List[Row]:
    named = {Path(f["path"]).name for f in manifest.get("files", [])}
    rows: List[Row] = []
    for entry in manifest.get("files", []):
        if entry.get("role") != "runner" and not entry["path"].endswith(".sh"):
            continue
        path = base / entry["path"]
        if not path.is_file():
            continue
        text = "\n".join(line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#"))
        invoked = sorted({Path(tok).name for tok in _PY_TOKEN.findall(text)})
        missing = [name for name in invoked if name not in named]
        detail = f"names {len(invoked)} python file(s)" + (f"; NOT in the manifest (no sha): {missing}" if missing else "")
        rows.append(("f runner refs", entry["path"], FAIL if missing else PASS, detail))
    return rows


# ---- (h) gate visibility -------------------------------------------------------------------------------------------------------------------

def heavy_words(busy_gate: Optional[str], explicit: Optional[str]) -> Optional[str]:
    if explicit:
        return explicit
    path = Path(busy_gate or DEFAULT_BUSY_GATE)
    if not path.is_file():
        return None
    found = re.search(r"RPG_HEAVY_WORDS='([^']*)'", path.read_text(encoding="utf-8"))
    return found.group(1) if found else None


def check_gate_visibility(manifest: dict, words: Optional[str]) -> List[Row]:
    if words is None:
        return [("h gate visibility", "-", FAIL, "RPG_HEAVY_WORDS could not be read (busy_gate.sh missing or has no pattern); pass --heavy-words")]
    pattern = re.compile(words)
    rows: List[Row] = []
    for proc in manifest.get("processes", []):
        if not proc.get("heavy", True):
            continue
        files = sorted({m for token in proc["entry"] for m in re.findall(r"\{file:([^}]+)\}", token) if ".py" in m})
        for name in files:
            seen = bool(pattern.search(Path(name).name))
            rows.append(("h gate visibility", f"{proc['name']}: {Path(name).name}", PASS if seen else FAIL,
                         "matches the shared gate's heavy words" if seen else f"name matches none of {words}: other lanes' gates cannot see this job"))
    return rows


# ---- field paths (d) -----------------------------------------------------------------------------------------------------------------------

_TOKEN = re.compile(r"([^.\[\]]+)|\[(\*|\d+)\]")


def collect(doc: Any, path: str) -> Tuple[List[Any], bool]:
    """Every value at ``path`` (``a.b[*].c``, ``[*]`` over a list or a dict's values, ``[0]`` an index) and whether the path resolved everywhere it was walked."""
    nodes = [doc]
    resolved = True
    for key, idx in _TOKEN.findall(path):
        nxt: List[Any] = []
        for node in nodes:
            if key:
                if isinstance(node, dict) and key in node:
                    nxt.append(node[key])
                else:
                    resolved = False
            elif idx == "*":
                if isinstance(node, list):
                    nxt.extend(node)
                elif isinstance(node, dict):
                    nxt.extend(node.values())
                else:
                    resolved = False
            else:
                if isinstance(node, list) and int(idx) < len(node):
                    nxt.append(node[int(idx)])
                else:
                    resolved = False
        nodes = nxt
    return nodes, resolved


def check_fields(proc: dict, doc: Any, scope: str) -> List[Row]:
    rows: List[Row] = []
    for field in proc.get("output", {}).get("fields", []):
        path = field["path"]
        values, resolved = collect(doc, path)
        if not values or not resolved:
            rows.append(("d field liveness", f"{scope} {path}", FAIL, "absent from the output" if not values else "absent on some rows"))
            continue
        distinct = {json.dumps(v, sort_keys=True) for v in values}
        defaults = {json.dumps(v, sort_keys=True) for v in field.get("defaults", DEFAULT_DEFAULTS)}
        constant = len(distinct) == 1
        if constant and next(iter(distinct)) in defaults and not field.get("may_be_constant"):
            rows.append(("d field liveness", f"{scope} {path}", FAIL, f"constant {next(iter(distinct))} over {len(values)} value(s): the field is dead (wrong source?)"))
        elif field.get("may_be_constant"):
            rows.append(("d field liveness", f"{scope} {path}", PASS, f"DECLARED may_be_constant; {len(distinct)} distinct over {len(values)} value(s)"))
        else:
            rows.append(("d field liveness", f"{scope} {path}", PASS, f"{len(distinct)} distinct over {len(values)} value(s)"))
    return rows


# ---- running a child -----------------------------------------------------------------------------------------------------------------------

def child_env(tree: Path, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(tree)  # exactly as the runs do; `-I` then ignores it, which is the point of check (b)
    env.update({k: str(v) for k, v in (extra or {}).items()})
    return env


def run(cmd: Sequence[str], tree: Path, env: Dict[str, str]) -> subprocess.CompletedProcess:
    return subprocess.run(list(cmd), cwd=str(tree), env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)


def substitute(token: str, ctx: Dict[str, Any], base: Path) -> str:
    token = re.sub(r"\{file:([^}]+)\}", lambda m: str((base / m.group(1)).resolve()), token)
    token = re.sub(r"\{out_of:([^}]+)\}", lambda m: str(Path(ctx["outdir"]) / f"{m.group(1)}.out"), token)
    return re.sub(r"\{(python|tree|world|seed|ticks|out)\}", lambda m: str(ctx[m.group(1)]), token)


# A kit script is usually a script, not a module: its argv parsing and its run sit at the top level. So check (b) executes only its top-level statements up to and including
# the last top-level import (the `sys.path` fix and every import), under the run's flags, and stops before the script would read argv or tick anything.
_IMPORT_SNIPPET = ("import ast, sys\n"
                   "src = open(sys.argv[1], encoding='utf-8').read()\n"
                   "tree = ast.parse(src)\n"
                   "last = max((i for i, n in enumerate(tree.body) if isinstance(n, (ast.Import, ast.ImportFrom))), default=-1)\n"
                   "tree.body = tree.body[:last + 1]\n"
                   "exec(compile(tree, sys.argv[1], 'exec'), {'__name__': '_kit_import_check', '__file__': sys.argv[1]})\n")


def check_imports(proc: dict, tree: Path, python: str, base: Path, scope: str) -> List[Row]:
    rows: List[Row] = []
    for name in proc.get("import_files", []):
        done = run([python, "-I", "-c", _IMPORT_SNIPPET, str((base / name).resolve())], tree, child_env(tree))
        tail = (done.stderr.strip().splitlines() or [""])[-1][:160]
        rows.append(("b import", f"{scope} {name}", PASS if done.returncode == 0 else FAIL, "imports under -I, cwd = the tree" if done.returncode == 0 else f"rc={done.returncode}: {tail}"))
    return rows


# ---- (g) wrapper signatures ----------------------------------------------------------------------------------------------------------------

_SIGNATURE_SNIPPET = r'''
import importlib, importlib.util, inspect, json, sys
tree, target = sys.argv[1:3]
sys.path.insert(0, tree)
def params(obj):
    return [[p.name, p.kind.name] for p in inspect.signature(obj).parameters.values()]
module_name, qual = target.split(":")
obj = importlib.import_module(module_name)
for part in qual.split("."):
    obj = getattr(obj, part)
print(json.dumps({"target": params(obj)}))
'''


def signature_problems(target: List[List[str]], wrapper: List[List[str]]) -> List[str]:
    """Names the parameters of ``target`` the wrapper would not accept. A leading ``self``/``cls`` is ignored on both sides; ``*args`` takes the positional ones and
    ``**kwargs`` the keyword ones, but only a parameter the wrapper names itself is matched by name and kind."""
    def strip(params: List[List[str]]) -> List[List[str]]:
        return params[1:] if params and params[0][0] in ("self", "cls") else params

    tgt, wrp = strip(target), strip(wrapper)
    wrapper_kinds = {name: kind for name, kind in wrp}
    has_args = any(kind == "VAR_POSITIONAL" for _, kind in wrp)
    has_kwargs = any(kind == "VAR_KEYWORD" for _, kind in wrp)
    problems: List[str] = []
    for name, kind in tgt:
        if kind in ("VAR_POSITIONAL", "VAR_KEYWORD"):
            continue
        if name in wrapper_kinds:
            wk = wrapper_kinds[name]
            positional_ok = {"POSITIONAL_ONLY": {"POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD"}, "POSITIONAL_OR_KEYWORD": {"POSITIONAL_OR_KEYWORD"}, "KEYWORD_ONLY": {"POSITIONAL_OR_KEYWORD", "KEYWORD_ONLY"}}
            if wk not in positional_ok[kind]:
                problems.append(f"{name}: target {kind}, wrapper {wk}")
        elif kind == "POSITIONAL_ONLY" and has_args:
            continue
        elif kind != "POSITIONAL_ONLY" and has_kwargs and (kind == "KEYWORD_ONLY" or has_args):
            continue
        else:
            problems.append(f"{name}: not accepted by the wrapper (wrapper takes {[n for n, _ in wrp]})")
    return problems


def wrapper_params(path: Path, name: str) -> List[List[str]]:
    """The parameters of the top-level ``def name`` in a kit script, read from its source (a script cannot be imported without running it)."""
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            a = node.args
            out = [[x.arg, "POSITIONAL_ONLY"] for x in a.posonlyargs] + [[x.arg, "POSITIONAL_OR_KEYWORD"] for x in a.args]
            if a.vararg:
                out.append([a.vararg.arg, "VAR_POSITIONAL"])
            out += [[x.arg, "KEYWORD_ONLY"] for x in a.kwonlyargs]
            if a.kwarg:
                out.append([a.kwarg.arg, "VAR_KEYWORD"])
            return out
    raise LookupError(f"no top-level def {name!r} in {path.name}")


def check_wraps(proc: dict, tree: Path, python: str, base: Path, scope: str) -> List[Row]:
    rows: List[Row] = []
    for wrap in proc.get("wraps", []):
        wfile, wattr = wrap["wrapper"].split(":")
        label = f"{scope} {wrap['target']} <- {wrap['wrapper']}"
        done = run([python, "-I", "-c", _SIGNATURE_SNIPPET, str(tree), wrap["target"]], tree, child_env(tree))
        if done.returncode != 0:
            rows.append(("g wrapper signature", label, FAIL, f"could not import the target: {(done.stderr.strip().splitlines() or [''])[-1][:160]}"))
            continue
        try:
            wrapper = wrapper_params(base / wfile, wattr)
        except (LookupError, SyntaxError, OSError) as err:
            rows.append(("g wrapper signature", label, FAIL, f"could not read the wrapper: {err}"))
            continue
        problems = signature_problems(json.loads(done.stdout.strip().splitlines()[-1])["target"], wrapper)
        rows.append(("g wrapper signature", label, FAIL if problems else PASS, "; ".join(problems) if problems else "every target parameter is matched"))
    return rows


# ---- (c) (d) (e) the fixture run ------------------------------------------------------------------------------------------------------------

def check_fixture_run(proc: dict, tree: Path, python: str, base: Path, ticks_cap: int, scope: str, outdir: Path) -> List[Row]:
    fixture = proc.get("fixture", {})
    out = outdir / f"{proc['name']}.out"
    ctx = {"python": python, "tree": tree, "world": fixture.get("world", ""), "seed": fixture.get("seed", 42), "ticks": min(int(fixture.get("ticks", ticks_cap)), ticks_cap), "out": out, "outdir": outdir}
    cmd = [substitute(token, ctx, base) for token in proc["entry"]]
    load_before, started = os.getloadavg()[0], time.monotonic()
    try:
        done = run(cmd, tree, child_env(tree, proc.get("env")))
    except subprocess.TimeoutExpired:
        return [("c fixture run", scope, FAIL, f"timed out after {TIMEOUT_SECONDS}s")]
    wall = time.monotonic() - started
    rows: List[Row] = [("c fixture run", scope, PASS if done.returncode == 0 else FAIL,
                        f"rc=0, {ctx['ticks']} tick(s)" if done.returncode == 0 else f"rc={done.returncode}: {(done.stderr.strip().splitlines() or [''])[-1][:160]}")]
    # Perf (informational, always PASS): wall time and the 1-minute loadavg before/after this process, so a later perf read does not come from file mtimes.
    rows.append(("i perf", scope, PASS, f"wall {wall:.2f}s, loadavg1 {load_before:.2f} -> {os.getloadavg()[0]:.2f}"))
    text = done.stdout + "\n" + done.stderr
    doc: Any = None
    if out.is_file():
        try:
            text_out = out.read_text(encoding="utf-8")
            doc = [json.loads(line) for line in text_out.splitlines() if line.strip()] if proc.get("output", {}).get("format") == "jsonl" else json.loads(text_out)
        except ValueError as err:
            rows.append(("d field liveness", scope, FAIL, f"output is not JSON: {err}"))
    elif proc.get("output", {}).get("fields") or any("count_path" in h for h in proc.get("hooks", [])):
        rows.append(("d field liveness", scope, FAIL, "the entry wrote no output file"))
    if doc is not None:
        rows.extend(check_fields(proc, doc, scope))
    guards = proc.get("guards", {})
    if guards.get("ok_regex"):
        hit = re.search(guards["ok_regex"], text) is not None
        rows.append(("e guards", f"{scope} ok line", PASS if hit else FAIL, "present" if hit else f"{guards['ok_regex']!r} not found"))
    if guards.get("bad_regex"):
        hit = re.search(guards["bad_regex"], text) is not None
        rows.append(("e guards", f"{scope} bad line", FAIL if hit else PASS, f"{guards['bad_regex']!r} found" if hit else "absent"))
    errors = len(re.findall(guards.get("error_log_regex", DEFAULT_ERROR_LOG_REGEX), text))
    rows.append(("e guards", f"{scope} ERROR+ log lines", FAIL if errors else PASS, str(errors)))
    for hook in proc.get("hooks", []):
        if "stdout_regex" in hook:
            hits = len(re.findall(hook["stdout_regex"], text))
            rows.append(("e guards", f"{scope} hook {hook['name']}", PASS if hits >= 1 else FAIL, f"hit {hits} time(s)"))
            continue
        values, resolved = collect(doc, hook["count_path"]) if doc is not None else ([], False)
        count = sum(v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool))
        rows.append(("e guards", f"{scope} hook {hook['name']}", PASS if count >= 1 else FAIL, f"hit {count} time(s)" if values else "count not in the output"))
    return rows


# ---- driver --------------------------------------------------------------------------------------------------------------------------------

def env_digest_of(python: str) -> str:
    snippet = ("import importlib.util, sys\nspec = importlib.util.spec_from_file_location('_env_digest', sys.argv[1])\nmod = importlib.util.module_from_spec(spec)\n"
               "sys.modules['_env_digest'] = mod\nspec.loader.exec_module(mod)\nprint(mod.installed_dists_digest())\n")
    try:
        done = subprocess.run([python, "-I", "-c", snippet, str(HERE / "env_digest.py")], capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as err:
        return f"unreadable ({err})"
    return done.stdout.strip() if done.returncode == 0 else f"unreadable (rc={done.returncode})"


def preflight(manifest_path: Path, trees: Sequence[Path], python: str, ticks: int, busy_gate: Optional[str] = None, words: Optional[str] = None) -> Tuple[List[Row], Dict[str, str]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    base = manifest_path.resolve().parent
    rows: List[Row] = []
    rows += check_files(manifest, base)
    rows += check_runner_references(manifest, base)
    rows += check_gate_visibility(manifest, heavy_words(busy_gate, words))
    for tree in trees:
        outdir = Path(tempfile.mkdtemp(prefix="kit_preflight_"))
        for proc in manifest.get("processes", []):
            scope = f"{proc['name']}@{tree.name}"
            rows += check_imports(proc, tree, python, base, scope)
            rows += check_wraps(proc, tree, python, base, scope)
            rows += check_fixture_run(proc, tree, python, base, ticks, scope, outdir)
        shutil.rmtree(outdir, ignore_errors=True)
    inputs = {"kit": f"{manifest.get('kit')} v{manifest.get('version')}", "manifest sha256": sha256_of(manifest_path), "preflight sha256": sha256_of(Path(__file__).resolve()),
              "interpreter": python, "env digest": env_digest_of(python), "ticks cap": str(ticks)}
    for entry in manifest.get("files", []):
        path = base / entry["path"]
        inputs[f"file {entry['path']}"] = sha256_of(path) if path.is_file() else "MISSING"
    for tree in trees:
        inputs[f"tree {tree.name}"] = str(tree)
    return rows, inputs


def render(rows: Sequence[Row], inputs: Dict[str, str]) -> str:
    verdict = PASS if all(status == PASS for _, _, status, _ in rows) else FAIL
    lines = [f"KIT PREFLIGHT {verdict} (evidence label: executed)", "", "| input | value |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in inputs.items()]
    lines += ["", "| check | scope | result | detail |", "|---|---|---|---|"]
    lines += [f"| {c} | {s} | {st} | {d.replace('|', '/')} |" for c, s, st, d in rows]
    lines.append(f"\n{sum(1 for r in rows if r[2] == FAIL)} FAIL of {len(rows)} check(s).")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("manifest")
    parser.add_argument("--tree", action="append", required=True, help="a frozen tree (repeat for each arm)")
    parser.add_argument("--ticks", type=int, default=10)
    parser.add_argument("--python", default=DEFAULT_PYTHON)
    parser.add_argument("--busy-gate", default=None)
    parser.add_argument("--heavy-words", default=None)
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    rows, inputs = preflight(Path(args.manifest), [Path(t).resolve() for t in args.tree], args.python, args.ticks, args.busy_gate, args.heavy_words)
    text = render(rows, inputs)
    print(text)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    return 0 if all(status == PASS for _, _, status, _ in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
