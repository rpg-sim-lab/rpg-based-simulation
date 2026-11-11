# Sourced by the proof steps. Secrets stay in shell variables and reach curl over stdin (-K -); nothing is echoed. The topic is never printed.
cd /data/vboxuser/Work/rpg-based-simulation/.claude/worktrees/platform
TOPIC=$(tr -d '[:space:]' < docker/secrets/ntfy_topic); TOKEN=$(tr -d '[:space:]' < docker/secrets/ntfy_token)
NT=http://127.0.0.1:2586
pub_anon(){ curl -s -o /dev/null -w '%{http_code}' -K - <<<"url = \"$NT/$TOPIC\"
data = \"$1\""; }
pub_token(){ curl -s -o /dev/null -w '%{http_code}' -K - <<<"url = \"$NT/$TOPIC\"
header = \"Authorization: Bearer $TOKEN\"
data = \"$1\""; }
read_msgs(){ curl -s -K - <<<"url = \"$NT/$TOPIC/json?poll=1&since=${1:-30m}\"
user = \"proofreader:$RPW\"" | python3 -c "
import json,sys
for l in sys.stdin:
    l=l.strip()
    if not l: continue
    m=json.loads(l)
    if m.get('event')!='message': continue
    import datetime
    print(datetime.datetime.utcfromtimestamp(m['time']).strftime('%H:%M:%SZ'), 'prio',m.get('priority'), 'tags',m.get('tags'), '|', (m.get('title') or '')[:70], '|', (m.get('message') or '')[:110].replace(chr(10),' / '))"; }
