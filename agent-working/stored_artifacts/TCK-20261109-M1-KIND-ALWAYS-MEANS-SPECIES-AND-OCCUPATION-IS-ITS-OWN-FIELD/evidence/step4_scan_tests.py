"""Step 4 scan 4: which tests reach each fall-through label / default. Run from repo root: python3 -I <this file>.
(1) per label: files under tests/ where the label is a quoted literal anywhere (text) vs. in a kind-writer position (AST: `.kind("x")`, EntityState(kind=),
spawn_*(kind="x"), replace(.., kind="x")); (2) files that call a spawner/path that writes the label without naming it (spawn_hero / spawn_monster default /
V2EntityBuilder without .kind); (3) EntityCarryForward constructions with no kind and EntityCarryForward.from_dict dicts without 'kind'; (4) WorldCompiler().compile
calls whose context argument is absent (kind = role label with no species)."""
import ast, pathlib, re, collections
T = pathlib.Path("tests")
LABELS = ["hero","monster","world_boss","ancient_sentinel","entity","stronghold","bandit","bear","harpy","golem","goblin_warrior","orc_warrior","goblin_raider","dragonkin","actor","pressure_target","goblin","wolf"]
SPAWN = {"spawn_monster","spawn_hero","spawn_goblin","spawn_natural_creature_offspring","spawn_humanoid_offspring"}
text = {}; writer = collections.defaultdict(set); path_reach = collections.defaultdict(set)
cf_nokind = []; compile_noctx = []; compile_all = 0; fromdict = []
for p in sorted(T.rglob("*.py")):
    s = p.read_text(errors="ignore"); text[p] = s
    try: t = ast.parse(s)
    except Exception: continue
    funcs = [n for n in ast.walk(t) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    def enc(n):
        b = None
        for f in funcs:
            if f.lineno <= n.lineno <= (f.end_lineno or 0) and (b is None or f.lineno >= b.lineno): b = f
        return b
    haskind = {enc(n) for n in ast.walk(t) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "kind" and len(n.args) == 1}
    for n in ast.walk(t):
        if not isinstance(n, ast.Call): continue
        fn = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
        lits = []
        if fn == "kind" and len(n.args) == 1 and isinstance(n.args[0], ast.Constant): lits.append(n.args[0].value)
        for k in n.keywords:
            if k.arg == "kind" and isinstance(k.value, ast.Constant) and (fn in SPAWN or fn in ("EntityState","replace")): lits.append(k.value.value)
        for v in lits:
            if isinstance(v, str): writer[v.lower() if v.lower() in LABELS else v].add(str(p))
        if fn == "spawn_hero": path_reach["hero via spawn_hero()"].add(str(p))
        if fn == "spawn_monster" and not any(k.arg == "kind" for k in n.keywords): path_reach["monster via spawn_monster() default"].add(str(p))
        if fn == "V2EntityBuilder" and enc(n) not in haskind: path_reach["hero via V2EntityBuilder default (no .kind call in function)"].add(str(p))
        if fn == "EntityCarryForward" and not any(k.arg == "kind" for k in n.keywords): cf_nokind.append(f"{p}:{n.lineno}")
        if fn == "from_dict" and isinstance(n.func, ast.Attribute) and "CarryForward" in ast.unparse(n.func.value): fromdict.append(f"{p}:{n.lineno}")
        if fn == "compile" and isinstance(n.func, ast.Attribute) and "WorldCompiler" in ast.unparse(n.func.value):
            compile_all += 1
            if not any(k.arg == "context" for k in n.keywords) and len(n.args) < 4: compile_noctx.append(f"{p}:{n.lineno}")
print("tests/*.py files", len(text))
print("== (1) per label: quoted-literal files | kind-writer-position files (case-folded for the label list)")
for l in LABELS:
    q = [p for p, s in text.items() if re.search(r'["\']%s["\']' % re.escape(l), s, re.I)]
    print(f"{l:18} quoted_any={len(q):4} writer_position={len(writer.get(l,()))}")
print("== (2) path reach (files)")
for k, v in path_reach.items(): print(f"{k}: {len(v)} files")
print("== (3) EntityCarryForward( without kind=:", len(cf_nokind), cf_nokind[:20]); print("   CarryForward.from_dict call sites:", len(fromdict), fromdict[:10])
print("== (4) WorldCompiler.compile calls:", compile_all, "without context (kw or 4th positional):", len(compile_noctx), "in files", len({x.split(':')[0] for x in compile_noctx}))
for f in sorted({x.split(":")[0] for x in compile_noctx}): print("    FILE", f, sum(x.startswith(f + ":") for x in compile_noctx))
print("== writer-position files for fall-through labels")
for l in ["world_boss","ancient_sentinel","entity","stronghold","bandit","bear","harpy","golem","goblin_warrior","orc_warrior","goblin_raider","dragonkin"]:
    print(l, sorted(writer.get(l, ())))
