#!/usr/bin/env bash
# Abort watcher for a stack run. usage: stack_guard.sh <rundir> [real|dry]
# Every GUARD_INTERVAL seconds (default 60; the first line at once) it appends "<UTC> avail=<MiB> swap=<MiB> mode=<mode> thresholds=<a>/<b>" to <rundir>/guard.log.
# Trigger: MemAvailable < MIN_AVAIL_MIB (default 1500) or swap used > MAX_SWAP_MIB (default 7500), or a reading that is empty or not a number (logged as READ FAIL; fail safe).
# Real mode on trigger: kills the PID in <rundir>/locust.pid (if present), runs `docker compose <COMPOSE_ARGS> down` (never -v), writes <rundir>/guard.abort.
# Dry mode prints "WOULD DOWN ..." and exits without touching anything (use it with a huge MIN_AVAIL_MIB to prove the trigger path before a run).
# It stops when <rundir>/guard.stop exists. It never matches processes by pattern: only the PID file.
# COMPOSE_ARGS defaults to "--profile observability"; set COMPOSE_ARGS="-f compose.yaml -f <override> --profile observability" when an override is in use
# (then export whatever variables the override requires before starting this script).
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)" || exit 2
RUN="${1:?usage: stack_guard.sh <rundir> [real|dry]}"; MODE="${2:-real}"
MIN_AVAIL_MIB="${MIN_AVAIL_MIB:-1500}"; MAX_SWAP_MIB="${MAX_SWAP_MIB:-7500}"
# MAX_SWAP_GROWTH_MIB (default off = 0): also trigger when swap used grows more than this above the first reading of the run.
MAX_SWAP_GROWTH_MIB="${MAX_SWAP_GROWTH_MIB:-0}"; BASE_SWAP=""
# MAX_DISK_PCT (default off = 0): also trigger when any filesystem in DISK_PATHS (default "/ /data") reads this `df` percent or more
# (TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE: Loki throttles at 90% by its own formula, which reads about 5 points below df). An unreadable value is a trigger.
MAX_DISK_PCT="${MAX_DISK_PCT:-0}"; DISK_PATHS="${DISK_PATHS:-/ /data}"
COMPOSE_ARGS="${COMPOSE_ARGS:---profile observability}"
mkdir -p "$RUN"; rm -f "$RUN/guard.stop" "$RUN/guard.abort"
while [ ! -f "$RUN/guard.stop" ]; do
  a=$(awk '/MemAvailable/{print int($2/1024)}' "${MEMINFO_FILE:-/proc/meminfo}" 2>/dev/null); w=$(free -m 2>/dev/null | awk '/Swap:/{print $3}')
  echo "$(date -u +%T) avail=${a} swap=${w} mode=${MODE} thresholds=${MIN_AVAIL_MIB}/${MAX_SWAP_MIB}" >> "$RUN/guard.log"
  # Fail safe: an empty or non-numeric reading is a trigger (a blind watcher is worse than an abort).
  trig=0
  case "$a" in ''|*[!0-9]*) trig=1; echo "$(date -u +%T) READ FAIL avail='${a}'" >> "$RUN/guard.log";; esac
  case "$w" in ''|*[!0-9]*) trig=1; echo "$(date -u +%T) READ FAIL swap='${w}'" >> "$RUN/guard.log";; esac
  [ -z "$BASE_SWAP" ] && case "$w" in ''|*[!0-9]*) ;; *) BASE_SWAP="$w";; esac
  if [ "$trig" = 0 ] && [ "$MAX_SWAP_GROWTH_MIB" -gt 0 ] && [ -n "$BASE_SWAP" ] && [ "$((w - BASE_SWAP))" -gt "$MAX_SWAP_GROWTH_MIB" ]; then trig=1; fi
  if [ "$trig" = 0 ] && { [ "$a" -lt "$MIN_AVAIL_MIB" ] || [ "$w" -gt "$MAX_SWAP_MIB" ]; }; then trig=1; fi
  disk=""
  if [ "$MAX_DISK_PCT" -gt 0 ]; then
    for p in $DISK_PATHS; do
      d=$(df -P "$p" 2>/dev/null | awk 'NR==2{gsub("%","",$5); print $5}')
      disk="${disk} ${p}=${d}%"
      case "$d" in ''|*[!0-9]*) trig=1; echo "$(date -u +%T) READ FAIL disk ${p}='${d}'" >> "$RUN/guard.log";; *) [ "$d" -ge "$MAX_DISK_PCT" ] && trig=1;; esac
    done
    echo "$(date -u +%T) disk:${disk} threshold=${MAX_DISK_PCT}%" >> "$RUN/guard.log"
  fi
  if [ "$trig" = 1 ]; then
    if [ "$MODE" = dry ]; then echo "$(date -u +%T) WOULD DOWN avail=${a} swap=${w}${disk}" | tee -a "$RUN/guard.log"; exit 0; fi
    echo "ABORT $(date -u +%T) avail=${a} swap=${w}${disk}" > "$RUN/guard.abort"
    [ -s "$RUN/locust.pid" ] && kill "$(cat "$RUN/locust.pid")" 2>/dev/null
    # shellcheck disable=SC2086
    docker compose $COMPOSE_ARGS down > "$RUN/guard.down.log" 2>&1
    exit 0
  fi
  sleep "${GUARD_INTERVAL:-60}"
done
