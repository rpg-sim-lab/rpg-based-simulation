import ast,sys,collections,pathlib
root=pathlib.Path("src"); c=collections.Counter(); hits=[]
for p in root.rglob("*.py"):
    try: t=ast.parse(p.read_text())
    except Exception as e: print("PARSEFAIL",p,e); continue
    for n in ast.walk(t):
        if isinstance(n,ast.Attribute) and n.attr=="kind":
            b=ast.unparse(n.value); c[b]+=1; hits.append((str(p),n.lineno,b))
for b,k in c.most_common(): print(k,b)
