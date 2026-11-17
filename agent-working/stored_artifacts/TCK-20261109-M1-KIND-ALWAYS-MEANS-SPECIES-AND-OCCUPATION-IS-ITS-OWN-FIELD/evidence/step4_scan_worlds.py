"""Step 4 scan 1: per data world, each population's role label (the classic compiler's kind today) vs its declared species.
Run from the repo root: python3 -I <this file>. Reads data/worlds/*/resolved/{world.resolved.yaml,compile_context.json}.
A population 'has a species' iff compile_context.json entities[pop_id].species_id is non-empty (the value compiler.py:757-761 copies)."""
import json, pathlib, collections, yaml
SPECIES = {s["id"] for s in yaml.safe_load(open("data/content/living/species.yaml"))}
label = collections.defaultdict(lambda: {"species": collections.Counter(), "worlds": set(), "pops": 0, "ents": 0})
nospecies = []; worlds = 0; pops = 0; unknown = []
for wd in sorted(pathlib.Path("data/worlds").iterdir()):
    r = wd / "resolved"
    if not (r / "world.resolved.yaml").exists() or not (r / "compile_context.json").exists():
        if wd.is_dir(): print("SKIP (no resolved/)", wd)
        continue
    worlds += 1
    w = yaml.safe_load(open(r / "world.resolved.yaml")); ctx = json.load(open(r / "compile_context.json"))["entities"]
    for e in w.get("entities", []):
        pops += 1
        lab = e["role"].lower(); sp = (ctx.get(e["id"]) or {}).get("species_id")
        d = label[lab]; d["species"][sp or "<none>"] += 1; d["worlds"].add(wd.name); d["pops"] += 1; d["ents"] += e["count"]
        if not sp: nospecies.append((wd.name, e["id"], lab))
        elif sp not in SPECIES: unknown.append((wd.name, e["id"], sp))
print("worlds", worlds, "populations", pops, "populations with no species", len(nospecies), "unknown species", len(unknown))
for lab, d in sorted(label.items()):
    print(f"{lab:18} pops={d['pops']:3} ents={d['ents']:4} worlds={len(d['worlds']):2} species={dict(d['species'])}")
for x in nospecies: print("NOSPECIES", x)
for x in unknown: print("UNKNOWN", x)
