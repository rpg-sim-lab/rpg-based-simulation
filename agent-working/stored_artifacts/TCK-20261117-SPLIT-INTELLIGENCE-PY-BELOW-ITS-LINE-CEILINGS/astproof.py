import ast,subprocess,sys
d='src/systems/strategic_systems/'
old=ast.parse(subprocess.check_output(['git','show','origin/main:'+d+'intelligence.py'],text=True))
new_i=ast.parse(open(d+'intelligence.py').read()); new_b=ast.parse(open(d+'blocker_lifecycle.py').read())
cls=[n for n in old.body if isinstance(n,ast.ClassDef) and n.name=='StrategicIntelligenceSystem'][0]
def strip(fn):
    fn=ast.parse(ast.unparse(fn)).body[0]
    body=list(fn.body)
    if body and isinstance(body[0],ast.Expr) and isinstance(getattr(body[0],'value',None),ast.Constant) and isinstance(body[0].value.value,str): body=body[1:]
    fn.body=body; fn.decorator_list=[]
    return fn
def dump(fn,drop_imports=False):
    fn=strip(fn)
    if fn.name=='resolve_blockers':
        # the ONE documented deviation: the dead-end `cadence = cadence or SystemCadence()` line runs in the class delegate (systems may not import engine)
        assert ast.unparse(fn.body[0])=='cadence = cadence or SystemCadence()' or fn.body[0].__class__.__name__!='Assign' or ast.unparse(fn.body[0])!='cadence = cadence or SystemCadence()'
        if ast.unparse(fn.body[0])=='cadence = cadence or SystemCadence()': fn.body=fn.body[1:]
        for a in fn.args.args:
            if a.arg=='cadence': a.annotation=None
    if drop_imports:
        fn.body=[s for s in fn.body if not isinstance(s,(ast.Import,ast.ImportFrom))]
    return ast.dump(fn)
ok=True
for n in ('infer_blockers','generate_crafting_blockers','resolve_blockers'):
    o=[m for m in cls.body if isinstance(m,ast.FunctionDef) and m.name==n][0]
    nb=[m for m in new_b.body if isinstance(m,ast.FunctionDef) and m.name==n][0]
    same=dump(o,True)==dump(nb,True)
    # signature
    def _sig(f):
        f=ast.parse(ast.unparse(f)).body[0]
        for a in f.args.args:
            if a.arg=='cadence': a.annotation=None
        return ast.dump(f.args)
    sig=_sig(o)==_sig(nb) and ast.dump(o.returns)==ast.dump(nb.returns)
    print(n,'body_equal(ignoring docstring and hoisted imports)=',same,'signature_equal=',sig)
    ok&=same and sig
# every other class member + module-level unchanged
ncls=[n for n in new_i.body if isinstance(n,ast.ClassDef) and n.name=='StrategicIntelligenceSystem'][0]
moved={'infer_blockers','generate_crafting_blockers','resolve_blockers'}
om={m.name:ast.dump(m) for m in cls.body if isinstance(m,(ast.FunctionDef,))}
nm={m.name:ast.dump(m) for m in ncls.body if isinstance(m,(ast.FunctionDef,))}
print('other methods identical:',all(om[k]==nm[k] for k in om if k not in moved),'| same method set:',set(om)==set(nm))
print('delegate bodies:',[ast.unparse(m.body[-2:] if m.name=='resolve_blockers' else m.body[-1:]) for m in ncls.body if isinstance(m,ast.FunctionDef) and m.name in moved])
oldtop=[ast.dump(n) for n in old.body if not isinstance(n,(ast.ImportFrom,ast.Import,ast.ClassDef))]
newtop=[ast.dump(n) for n in new_i.body if not isinstance(n,(ast.ImportFrom,ast.Import,ast.ClassDef))]
print('module-level non-import non-class nodes identical:',oldtop==newtop)
nonmeth=lambda c:[ast.dump(m) for m in c.body if not isinstance(m,ast.FunctionDef)]
print('class non-method members identical:',nonmeth(cls)==nonmeth(ncls))
