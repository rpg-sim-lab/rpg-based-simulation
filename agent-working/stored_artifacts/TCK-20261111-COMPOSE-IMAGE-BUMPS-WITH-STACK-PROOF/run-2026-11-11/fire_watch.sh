. "$(dirname "$0")/ntfy_lib.sh"; RPW=$(cat /tmp/claude-1000/rpw_cb); RUN=$(dirname "$0"); PW=$(tr -d '[:space:]' < docker/secrets/grafana_admin_password)
st(){ curl -s -K - <<<"user = \"admin:$PW\"
url = \"http://127.0.0.1:3000/api/prometheus/grafana/api/v1/rules\"" | python3 -c "
import json,sys
for x in json.load(sys.stdin)['data']['groups']:
  for r in x['rules']:
    if r['name']=='TargetDown': print(' '.join(a['labels'].get('job','?')+'='+a['state'] for a in r.get('alerts',[]) if a['state']!='Normal') or 'all Normal')"; }
