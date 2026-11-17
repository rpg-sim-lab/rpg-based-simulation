import ast,pathlib,sys
ENT={"entity","ent","prior_ent","e","self_entity","hero","hostile","target","actor","other","pair[0]","entity.interaction","a","b","s","p","c","n","v","x","d","l","current","tp","opt","opp","req","best_candidate","candidate_b","rec","cf","o","selected","u_int","new_int"}
rows=[]
for p in sorted(pathlib.Path("src").rglob("*.py")):
    src=p.read_text(); lines=src.splitlines()
    try: t=ast.parse(src)
    except Exception: continue
    for n in ast.walk(t):
        base=None
        if isinstance(n,ast.Attribute) and n.attr=="kind":
            base=ast.unparse(n.value)
            if base in ENT or base.startswith("V2EntityBuilder"): rows.append((str(p),n.lineno,base,lines[n.lineno-1].strip()))
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="getattr" and len(n.args)>=2 and isinstance(n.args[1],ast.Constant) and n.args[1].value=="kind":
            rows.append((str(p),n.lineno,"getattr("+ast.unparse(n.args[0])+")",lines[n.lineno-1].strip()))
        elif isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and n.slice.value=="kind":
            rows.append((str(p),n.lineno,"["+ast.unparse(n.value)+"]",lines[n.lineno-1].strip()))
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value=="kind":
            rows.append((str(p),n.lineno,"get("+ast.unparse(n.func.value)+")",lines[n.lineno-1].strip()))
for r in rows: print("%s:%d\t%s\t%s"%(r[0],r[1],r[2],r[3][:150]))
