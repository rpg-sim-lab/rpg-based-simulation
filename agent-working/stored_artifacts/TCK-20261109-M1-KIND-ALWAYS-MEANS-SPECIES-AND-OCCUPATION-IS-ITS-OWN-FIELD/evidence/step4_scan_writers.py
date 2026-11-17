"""Step 4 scan 3: AST scan of every writer of EntityState.kind. Run from repo root: python3 -I <this file> [src|tests] (default src).
Reports, per file: (A) `<x>.kind(<arg>)` builder calls (V2EntityBuilder.kind), with the unparsed argument; (B) `EntityState(... kind=...)`
constructor calls; (C) `kind="<literal>"` keywords passed to spawn_* / replace calls whose target is an entity; (D) V2EntityBuilder( constructions in a
function that has no `.kind(` call (these keep the builder's own default kind "hero", src/core/builder.py:95) -- approximate: a builder
configured in a different function than it is built is not seen; (E) spawn_monster/spawn_hero/spawn_natural_creature_offspring/spawn_humanoid_offspring/spawn_goblin
call sites. Output lines: category<TAB>file:line<TAB>detail."""
import ast, pathlib, sys
root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "src")
SPAWNERS = {"spawn_monster", "spawn_hero", "spawn_goblin", "spawn_natural_creature_offspring", "spawn_humanoid_offspring"}
out = []
for p in sorted(root.rglob("*.py")):
    try: t = ast.parse(p.read_text())
    except Exception as e: print("PARSEFAIL", p, e); continue
    funcs = [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    def enclosing(n):
        best = None
        for f in funcs:
            if f.lineno <= n.lineno <= (f.end_lineno or f.lineno) and (best is None or f.lineno >= best.lineno): best = f
        return best
    kindcalls_by_func = {}
    for n in ast.walk(t):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "kind" and len(n.args) == 1 and not n.keywords:
            out.append(("A", f"{p}:{n.func.end_lineno}", ast.unparse(n.args[0]))); kindcalls_by_func.setdefault(enclosing(n), 0); kindcalls_by_func[enclosing(n)] += 1
    for n in ast.walk(t):
        if not isinstance(n, ast.Call): continue
        fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
        kws = {k.arg: ast.unparse(k.value) for k in n.keywords if k.arg}
        if fn == "EntityState" and "kind" in kws: out.append(("B", f"{p}:{n.lineno}", kws["kind"]))
        elif fn in SPAWNERS:
            out.append(("E", f"{p}:{n.lineno}", f"{fn} kind={kws.get('kind', '<default/positional>')}"))
        elif fn == "replace" and "kind" in kws and n.args and "region" not in ast.unparse(n.args[0]):
            out.append(("C", f"{p}:{n.lineno}", f"replace({ast.unparse(n.args[0])}, kind={kws['kind']})"))
        elif fn == "V2EntityBuilder":
            if enclosing(n) not in kindcalls_by_func: out.append(("D", f"{p}:{n.lineno}", "V2EntityBuilder( in a function with no .kind( call"))
for c, loc, d in out: print(f"{c}\t{loc}\t{d}")
import collections
print("COUNTS", dict(collections.Counter(c for c, _, _ in out)), "files", len({l.split(':')[0] for _, l, _ in out}))
