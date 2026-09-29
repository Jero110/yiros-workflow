#!/usr/bin/env bash
# wait-agents.sh — block until a supervised agent surface needs the executor, then print one JSON line and exit.
#
# Usage:
#   wait-agents.sh --timeout 900 --surface <uuid-or-ref> [--surface ...]
#   wait-agents.sh --timeout 900            # any agent surface in any workspace
#   --no-idle                               # ignore agent.idle.observed
#
# Output (one JSON object, stdout). `surface` is a UUID — map it back with
# `cmux tree --id-format both`:
#   {"kind":"agent.question.requested","surface":"DD9D28C1-...","seq":33678,"at":"..."}
#
# kind is one of: agent.question.requested (worker asked something — pane went blue),
#                 agent.approval.requested (permission prompt),
#                 agent.turn.completed, agent.idle.observed
#
# Exit codes: 0 = an event fired, 2 = timed out with nothing, 3 = cmux events unavailable.
set -uo pipefail
CMUX="${CMUX_BIN:-cmux}"
TIMEOUT=900
SKIP_IDLE=0
declare -a WANT_UUIDS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --timeout) TIMEOUT="$2"; shift 2 ;;
    --no-idle) SKIP_IDLE=1; shift ;;
    --surface)
      s="$2"; shift 2
      if [[ "$s" == surface:* ]]; then
        u=$("$CMUX" identify --surface "$s" --json --id-format both 2>/dev/null \
            | python3 -c 'import json,sys;print(json.load(sys.stdin)["caller"]["surface_id"])' 2>/dev/null)
        [ -n "${u:-}" ] && WANT_UUIDS+=("$u")
      else
        WANT_UUIDS+=("$s")
      fi
      ;;
    *) echo "unknown arg: $1" >&2; exit 64 ;;
  esac
done

# Anchor at the current sequence so we never wake on a replayed, already-handled event.
SEQ=$("$CMUX" events --snapshot 2>/dev/null \
      | python3 -c 'import json,sys;print(json.load(sys.stdin)["resume"]["latest_seq"])' 2>/dev/null)
[ -z "${SEQ:-}" ] && { echo '{"error":"cmux events unavailable"}'; exit 3; }

export FILTER="${WANT_UUIDS[*]:-}"
export SKIP_IDLE

# pipefail would surface cmux's SIGPIPE (exit 1) when python exits first on a match,
# masking python's real 0/2 status. Take the status of the LAST pipe element only.
set +o pipefail

"$CMUX" events --after "$SEQ" --name agent.notification.decision \
        --no-heartbeat --no-ack --timeout "$TIMEOUT" 2>/dev/null \
| python3 -u -c '
import json, os, sys
want = set(filter(None, os.environ.get("FILTER","").split()))
# Only these kinds mean "the executor has something to do".
ACT = {"agent.question.requested",   # worker is asking something (pane turns blue)
       "agent.approval.requested",   # worker needs a permission decision
       "agent.turn.completed",       # worker finished a turn
       "agent.idle.observed"}        # worker went idle (delayed follow-up to a turn)
if os.environ.get("SKIP_IDLE") == "1":
    ACT.discard("agent.idle.observed")
seen = set()
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line)
    except ValueError:
        continue
    seq = d.get("seq")
    if seq in seen:          # cmux emits each event twice; dedupe on seq
        continue
    seen.add(seq)
    kind = (d.get("payload") or {}).get("kind")
    surf = d.get("surface_id")
    if kind not in ACT:
        continue
    if want and surf not in want:
        continue
    print(json.dumps({"kind": kind, "surface": surf, "seq": seq,
                      "at": d.get("occurred_at")}), flush=True)
    sys.exit(0)
sys.exit(2)
'
