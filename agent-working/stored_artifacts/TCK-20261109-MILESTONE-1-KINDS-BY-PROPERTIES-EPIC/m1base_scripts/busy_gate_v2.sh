# Shared host gates for rpg measurement runners (rpg-planner, 2026-11-16; from D1 runner a87a54af line 23; v2 adds keep_events_child).
# Source it: `. /mnt/data2/rpg-measure/lib/busy_gate.sh`, then call `rpg_host_gate || exit 9` before EACH heavy process.
# - Heavy job = a python command line naming one of these tools AND a path of this project. Long-lived knowledge-search
#   MCP servers (search_mcp.py, search_shared.py) and other projects' pytests (e.g. /mnt/data2/Work/algo-ai) do not match.
# - keep_events_child (the M1-base child wrapper) is listed so a running M1-base cell is visible. fill_cache is NOT listed:
#   it calls rpg_host_gate itself (fill_cache.py:88), so listing it would make the gate see its own caller. Only the
#   seconds between M1-base cells are blind; that is accepted (rpg-designer, 2026-11-16).
# - Do not put these words plus a project path in the launch line of the runner itself, or in any shell command run while it runs.
# - The memory gate is unchanged: MemAvailable >= 3500 MB.
RPG_HEAVY_WORDS='arm_child|keep_events_child|d1_own_job_spy|hold_spy|tally_spy|v3_trace|d1_step0|pytest|run_cells|paired\.py|smoke_wrapcount|dying_window'
RPG_PROJECT_PATHS='rpg-based-simulation|rpg-measure|rpg-wt'
rpg_busy() { pgrep -af "[p]ython.*(${RPG_HEAVY_WORDS})" | grep -qE "${RPG_PROJECT_PATHS}"; }
rpg_mem_ok() { [ "$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)" -ge 3500 ]; }
rpg_host_gate() {
  local i; for i in 1 2 3 4 5 6; do rpg_busy || break; sleep 5; done
  rpg_busy && { echo "STOP: a heavy job of this project is running (after ~30 s)"; return 9; }
  rpg_mem_ok || { echo "STOP: MemAvailable < 3500 MB"; return 9; }
  return 0
}
