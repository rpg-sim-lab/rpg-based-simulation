"""Step 4 scan 5: callers of WorldCompiler.compile and of ResolvedEntityProfile( / WorldEntitySpawner outside tests, with/without context / species_id.
Run from repo root: python3 -I <this file>. A compile call 'has context' iff a `context=` keyword or a 4th positional argument is passed."""
import ast, pathlib
for d in ("src", "tools", "tests"):
    comp = []; prof = []
    for p in sorted(pathlib.Path(d).rglob("*.py")):
        try: t = ast.parse(p.read_text(errors="ignore"))
        except Exception: continue
        for n in ast.walk(t):
            if not isinstance(n, ast.Call): continue
            fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
            if fn == "compile" and isinstance(n.func, ast.Attribute) and "WorldCompiler" in ast.unparse(n.func.value):
                ctx = any(k.arg == "context" for k in n.keywords) or len(n.args) >= 4
                comp.append((f"{p}:{n.lineno}", ctx))
            if fn == "ResolvedEntityProfile":
                kw = {k.arg for k in n.keywords}
                prof.append((f"{p}:{n.lineno}", "species_id" in kw, "archetype_id" in kw))
    print(f"== {d}: WorldCompiler.compile calls {len(comp)}, with context {sum(c for _, c in comp)}, without {sum(not c for _, c in comp)}")
    if d != "tests":
        for loc, c in comp: print("   ", loc, "context" if c else "NO CONTEXT")
    print(f"   ResolvedEntityProfile( calls {len(prof)}: with species_id {sum(s for _, s, _ in prof)}, with archetype_id {sum(a for _, _, a in prof)}, with neither {sum((not s) and (not a) for _, s, a in prof)}")
    if d != "tests":
        for x in prof: print("   ", x)
    else:
        nei = [x for x in prof if not x[1] and not x[2]]
        print("   neither, files:", sorted({x[0].split(':')[0] for x in nei}))
