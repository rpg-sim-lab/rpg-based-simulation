"""Step 4 scan 6: every kind writer in src/certification, src/perf, src/testing with its enclosing function and the faction/role the same builder chain sets.
Run from repo root: python3 -I <this file>. Line = the line of the `.kind(` token."""
import ast, pathlib
for d in ("src/certification", "src/perf", "src/testing"):
    for p in sorted(pathlib.Path(d).rglob("*.py")):
        t = ast.parse(p.read_text()); funcs = [n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)]
        def enc(n):
            b = None
            for f in funcs:
                if f.lineno <= n.lineno <= f.end_lineno and (b is None or f.lineno >= b.lineno): b = f
            return b.name if b else "<module>"
        for n in ast.walk(t):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("kind", "spawn_hero", "spawn_monster") and (n.func.attr != "kind" or len(n.args) == 1):
                chain = []; cur = n
                # climb to the outermost call of the chain by position: collect sibling identity() kwargs sharing the chain root
                root = n.func.value
                while isinstance(root, ast.Call) and isinstance(root.func, ast.Attribute): root = root.func.value
                ids = {}
                for m in ast.walk(t):
                    if isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and m.func.attr == "identity":
                        r = m.func.value
                        while isinstance(r, ast.Call) and isinstance(r.func, ast.Attribute): r = r.func.value
                        if r is root:
                            for k in m.keywords:
                                if k.arg in ("faction", "role"): ids[k.arg] = ast.unparse(k.value)
                arg = ast.unparse(n.args[0]) if n.func.attr == "kind" else f"{n.func.attr}() default"
                print(f"{p}:{n.func.end_lineno}\t{arg}\t{enc(n)}\t{ids}")
