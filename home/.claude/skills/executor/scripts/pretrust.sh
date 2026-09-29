#!/usr/bin/env bash
# pretrust.sh — pre-accept Claude Code's folder-trust dialog for worker directories,
# so dispatched workers start straight at their prompt instead of parking on
# "Do you trust this folder?" waiting for a human to pick "Yes, I trust this folder".
#
# Usage:
#   pretrust.sh <dir> [<dir> ...]
#   pretrust.sh --check <dir> [<dir> ...]    # report only, change nothing
#
# Why this exists: no CLI flag skips that dialog. Verified — neither
# --dangerously-skip-permissions nor --permission-mode bypassPermissions skips it;
# the trust gate runs before permission handling. The only lever is the
# `projects.<path>.hasTrustDialogAccepted` entry in ~/.claude.json.
#
# Trust is inherited from a parent directory, so a worktree inside an
# already-trusted repo needs nothing and this is a no-op for it. It matters for
# worker directories OUTSIDE the trusted repo.
#
# Paths are matched RESOLVED: on macOS /tmp/x is really /private/tmp/x, and
# registering the unresolved form has no effect. This script resolves for you.
set -euo pipefail

CONFIG="${CLAUDE_CONFIG:-$HOME/.claude.json}"
CHECK=0
[ "${1:-}" = "--check" ] && { CHECK=1; shift; }
[ $# -eq 0 ] && { echo "usage: pretrust.sh [--check] <dir> [<dir>...]" >&2; exit 64; }
[ -f "$CONFIG" ] || { echo "no $CONFIG — is Claude Code installed?" >&2; exit 3; }

CHECK="$CHECK" CONFIG="$CONFIG" python3 - "$@" <<'PY'
import json, os, sys, shutil, tempfile

cfg   = os.environ["CONFIG"]
check = os.environ["CHECK"] == "1"

with open(cfg) as fh:
    data = json.load(fh)
projects = data.setdefault("projects", {})

def trusted(path):
    """Trust is inherited: a parent entry covers its subdirectories."""
    cur = path
    while True:
        if projects.get(cur, {}).get("hasTrustDialogAccepted"):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent

added = []
for raw in sys.argv[1:]:
    path = os.path.realpath(raw)
    if not os.path.isdir(path):
        print(f"  skip (not a directory): {raw}")
        continue
    via = trusted(path)
    if via:
        print(f"  ok (inherits from {via}): {path}")
        continue
    if check:
        print(f"  WOULD PROMPT: {path}")
        continue
    projects.setdefault(path, {})["hasTrustDialogAccepted"] = True
    added.append(path)
    print(f"  pre-trusted: {path}")

if added and not check:
    # back up, then write atomically — this is the user's global config
    shutil.copy2(cfg, cfg + ".bak")
    tmp = tempfile.NamedTemporaryFile("w", dir=os.path.dirname(cfg), delete=False)
    json.dump(data, tmp, indent=2)
    tmp.close()
    os.replace(tmp.name, cfg)
    print(f"wrote {len(added)} entries to {cfg} (backup at {cfg}.bak)")
elif not added and not check:
    print("nothing to do — every path was already trusted")
PY
