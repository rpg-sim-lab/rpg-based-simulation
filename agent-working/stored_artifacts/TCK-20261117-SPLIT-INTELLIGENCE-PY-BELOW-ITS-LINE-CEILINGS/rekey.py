import re,sys
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,'.')
from codebase.health.registry import load_rows, write_rows
P=Path('codebase/baselines/code_health_exceptions.jsonl')
I='src/systems/strategic_systems/intelligence.py';B='src/systems/strategic_systems/blocker_lifecycle.py'
rows=load_rows(P)
txt=open('/mnt/data2/rpg-measure/intsplit/code_health_70dbcc5d3_full.out').read().split('\n')
# measured values from the tool's own output
newbl={}   # (symbol,tool,rule)->value  (new rows)
for l in txt[:14]:
    m=re.match(r'\s+'+re.escape(B)+r'(?::\d+)?(?: (\S+))? \[(\S+) (\S+(?: \S+)?)\] value=(\d+)',l)
    if m:
        sym,tool,rule,val=m.groups(); newbl[(sym,tool,rule)]=int(val)
impr={}
for l in txt:
    m=re.match(r'\s+'+re.escape(I)+r'(?::\d+)?(?: (\S+))? \[(\S+) (\S+)\] (\d+) < ceiling (\d+)',l)
    if m: impr[(m.group(1),m.group(2),m.group(3))]=int(m.group(4))
print('BL measured rows:',len(newbl),'| intelligence improved rows:',len(impr))
byk={r.key:r for r in rows}
out=[];log=[]
moved_sym={'StrategicIntelligenceSystem.infer_blockers':'infer_blockers','StrategicIntelligenceSystem.resolve_blockers':'resolve_blockers'}
keep=[]
for r in rows:
    if r.file==I and r.symbol in moved_sym:
        ns=moved_sym[r.symbol]; v=newbl[(ns,r.tool,r.rule)]
        assert v<=r.ceiling,(r,v)
        nr=replace(r,file=B,symbol=ns,value=v,ceiling=v); keep.append(nr)
        log.append(f'RE-KEY  {I} {r.symbol} [{r.tool} {r.rule}] ceiling {r.ceiling} -> {B} {ns} ceiling {v}'+('' if v==r.ceiling else f'  (DECREASE by {r.ceiling-v})'))
        continue
    keep.append(r)
# per-file ruff rows: new BL rows copied from the intelligence row's metadata (same rule, value = measured)
for (sym,tool,rule),v in newbl.items():
    if sym is None or sym=='None':
        src=byk[(I,None,tool,rule)]
        assert v<=src.ceiling
        keep.append(replace(src,file=B,value=v,ceiling=v))
        log.append(f'ADD(moved) {B} [{tool} {rule}] ceiling {v}  (moved from intelligence.py, which had {src.ceiling})')
final=[]
# lower by EXACTLY the moved amount (rest of any drop is pre-existing slack on main: left alone); lengths = the tool's measured values
MOVED={('ruff','ANN001'):1,('ruff','C901'):2,('ruff','E722'):1,('ruff','PLC0415'):3,('ruff','PLR0912'):2,('ruff','PLR0915'):1,('ruff','PLR1702'):4}
for r in keep:
    if r.file==I:
        if (r.tool,r.rule) in MOVED and r.symbol is None:
            nv=r.ceiling-MOVED[(r.tool,r.rule)]
            log.append(f'TIGHTEN {I} [{r.tool} {r.rule}] ceiling {r.ceiling} -> {nv}  (moved amount {MOVED[(r.tool,r.rule)]})')
            r=replace(r,value=min(r.value,nv),ceiling=nv)
        elif (r.tool,r.rule) in {('line_count','module-length'),('line_count','class-length')}:
            nv=impr[(r.symbol,r.tool,r.rule)]
            log.append(f'TIGHTEN {I} {r.symbol or ""} [{r.tool} {r.rule}] ceiling {r.ceiling} -> {nv}  (measured; the move alone causes it)')
            r=replace(r,value=nv,ceiling=nv)
    final.append(r)
write_rows(P,final)
open('/mnt/data2/rpg-measure/intsplit/baseline_row_diff.txt','w').write('\n'.join(log)+'\n')
print('\n'.join(log))
