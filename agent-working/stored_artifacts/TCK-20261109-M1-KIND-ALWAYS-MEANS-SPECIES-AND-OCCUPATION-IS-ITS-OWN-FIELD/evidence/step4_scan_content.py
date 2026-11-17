"""Step 4 scan 2: content declarations. Run from repo root: python3 -I <this file>.
Reports: archetypes (id -> species), the species.yaml ids and camp_spawn_kind, populations.yaml members that name an archetype with no
species, module population_recipes with neither species_id nor a named archetype, and which labels the SPAWN_KIND_CATALOG_FACTION /
SPAWN_CADENCE / BOSS tables name that resolve via (a) none, (b) a same-id archetype, (c) a species camp_spawn_kind."""
import yaml, glob, ast, pathlib
sp = {s["id"]: s for s in yaml.safe_load(open("data/content/living/species.yaml"))}
arch = {a["id"]: a for a in yaml.safe_load(open("data/content/entities/entity_archetypes.yaml"))}
print("species ids", len(sp), sorted(sp))
print("species with camp_spawn_kind", {k: v["camp_spawn_kind"] for k, v in sp.items() if v.get("camp_spawn_kind")})
print("archetypes", len(arch), "without species:", [i for i, a in arch.items() if not a.get("species")], "species not in species.yaml:", [(i, a["species"]) for i, a in arch.items() if a.get("species") and a["species"] not in sp])
pops = yaml.safe_load(open("data/content/entities/populations.yaml"))
bad = [(p["id"], m) for p in pops for m in p["members"] if m not in arch or not arch[m].get("species")]
print("populations.yaml", len(pops), "members naming no archetype/species:", bad)
rec_no = []; rec_n = 0; mod_pop_missing = []
popids = {p["id"] for p in pops}
for f in sorted(glob.glob("data/content/world_modules/*.yaml")):
    d = yaml.safe_load(open(f))
    for r in d.get("population_recipes", []) or []:
        rec_n += 1
        if not r.get("species_id"): rec_no.append((f, r["role"]))
    for p in d.get("populations", []) or []:
        if p not in popids: mod_pop_missing.append((f, p))
print("module population_recipes", rec_n, "without species_id:", rec_no, "| module populations not in populations.yaml:", mod_pop_missing)
camp = {v["camp_spawn_kind"]: k for k, v in sp.items() if v.get("camp_spawn_kind")}
def resolve(label):
    if label in sp: return ("species-id", label)
    if label in arch and arch[label].get("species"): return ("archetype", arch[label]["species"])
    if label in camp: return ("camp_spawn_kind", camp[label])
    return None
labels = ["world_boss","ancient_sentinel","dragonkin","stronghold","hero","monster","goblin","goblin_warrior","goblin_raider","orc_warrior","bandit","bear","harpy","golem","wolf","slime","spider","troll","entity","human"]
for l in labels: print(f"{l:18}", resolve(l))
