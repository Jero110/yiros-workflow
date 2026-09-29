#!/usr/bin/env python3
"""agent-inbox — block until a cmux agent pane needs you, then print what it needs.

Two modes:
  - No --prefix (fastest, recommended): agents just answer. On turn end the full reply
    is read from cmux's hook store (`lastBody`), or from the harness transcript when
    that is truncated. Works for Claude Code, Codex and Pi. Measured ~1.5-3.5s from
    send to reply vs ~2.6-3.8s when the agent has to run `cmux notify` itself.
  - --prefix CHAT_: agents end each turn with `cmux notify --title CHAT_...`; those
    notifications are the reply. A turn that ends without one still falls back to the
    transcript.

One call covers, in this order:
  1. Backlog: prefixed notifications not yet seen (landed while you were busy).
  2. Event stream, resumed from the last handled seq (never "from now", so nothing
     that fired between two calls is lost):
       notification.created                 -> print the prefixed reply
       agent.question.requested             -> pane is waiting on a question
       agent.approval.requested             -> pane is parked on a permission prompt
       agent.turn.completed / error.reported -> turn over; print the reply text
     (Pi reports some normal turn ends as agent.error.reported.)
  3. Fallback when `cmux events` is unavailable: poll notifications every 0.5s.

Output, one line per item (surface refs, not UUIDs):
  REPLY surface:164 CHAT_X | <body>        (from a notify)
  REPLY surface:164 (turn) | <full text>   (from turn end)
  QUESTION surface:163 | <detail>
  APPROVAL surface:163 | <detail>
  TURN_NO_TEXT surface:165 | <kind>        (turn ended, no text found)
  TIMEOUT
Exit: 0 = something to handle, 2 = timeout.

Usage:
  agent-inbox.py [--surface surface:N ...] [--prefix CHAT_] [--timeout 90]
                 [--state NAME] [--reset]
First run (or --reset) marks everything already present as seen and starts from now.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CMUX = os.environ.get("CMUX_BIN", "cmux")


def cmux(*args):
    return subprocess.run([CMUX, *args], capture_output=True, text=True).stdout


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def surface_refs():
    """UUID -> surface:N for every surface cmux knows about."""
    out = cmux("tree", "--id-format", "both")
    return {u: r for r, u in re.findall(r"(surface:\d+)\s+([0-9A-Fa-f-]{36})", out)}


class State:
    def __init__(self, name):
        self.dir = Path.home() / ".cache" / "cmux-inbox" / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.seen_file = self.dir / "seen.jsonl"
        self.cursor_file = self.dir / "cursor"
        self.seen = {}
        if self.seen_file.exists():
            for line in self.seen_file.read_text().splitlines():
                if line.strip():
                    e = json.loads(line)
                    self.seen[e["id"]] = e

    @property
    def fresh(self):
        return not self.cursor_file.exists()

    def mark(self, n):
        e = {"id": n["id"], "surface": n.get("surface_id"), "at": n.get("created_at")}
        self.seen[e["id"]] = e
        with self.seen_file.open("a") as f:
            f.write(json.dumps(e) + "\n")

    def cursor(self):
        return int(self.cursor_file.read_text()) if self.cursor_file.exists() else None

    def set_cursor(self, seq):
        self.cursor_file.write_text(str(seq))

    def _inputs(self):
        f = self.dir / "last_input.json"
        return json.loads(f.read_text()) if f.exists() else {}

    def set_input(self, surface, at):
        d = self._inputs()
        d[surface] = at
        (self.dir / "last_input.json").write_text(json.dumps(d))

    def notified_since_input(self, surface):
        """True if this surface sent a notification after the last input it received."""
        since = self._inputs().get(surface)
        for e in self.seen.values():
            if e["surface"] == surface and e["at"]:
                if since is None or parse_ts(e["at"]) >= parse_ts(since):
                    return True
        return False


HOOK_STORES = Path.home() / ".cmuxterm"
PI_SESSIONS = Path.home() / ".pi" / "agent" / "sessions"


def hook_entry(surface):
    """cmux's per-harness hook record for this surface (claude / codex / pi)."""
    for agent in ("claude", "codex", "pi"):
        f = HOOK_STORES / f"{agent}-hook-sessions.json"
        if not f.exists():
            continue
        try:
            d = json.loads(f.read_text())
        except ValueError:
            continue
        items = d.get("sessions", d) if isinstance(d, dict) else d
        if isinstance(items, dict):
            items = list(items.values())
        for it in items:
            if it.get("surfaceId") == surface:
                return agent, it
    return None, None


def assistant_text(line):
    """Assistant text from one transcript line, for Claude, Pi and Codex formats."""
    try:
        d = json.loads(line)
    except ValueError:
        return None
    if d.get("type") == "assistant":                                   # Claude Code
        content = (d.get("message") or {}).get("content")
    elif d.get("type") == "message" and (d.get("message") or {}).get("role") == "assistant":  # Pi
        content = d["message"].get("content")
    elif d.get("type") == "response_item" and (d.get("payload") or {}).get("role") == "assistant":  # Codex
        content = d["payload"].get("content")
    else:
        return None
    if not isinstance(content, list):
        return None
    text = "".join(c.get("text", "") for c in content if c.get("type") in ("text", "output_text"))
    return text or None


def transcript_path(agent, entry):
    if entry.get("transcriptPath"):
        return Path(entry["transcriptPath"])
    if agent == "pi" and entry.get("sessionId"):
        hits = list(PI_SESSIONS.glob(f"*/*_{entry['sessionId']}.jsonl"))
        return hits[0] if hits else None
    return None


def last_reply(surface, occurred_at):
    """Last assistant message of the agent on this surface, without it having to notify."""
    t_event = parse_ts(occurred_at).timestamp() if occurred_at else 0
    agent, entry = hook_entry(surface)
    for _ in range(15):  # the hook store can land a beat after the event
        if entry and float(entry.get("updatedAt") or 0) >= t_event - 1:
            break
        time.sleep(0.1)
        agent, entry = hook_entry(surface)
    if not entry:
        return None
    body = entry.get("lastBody") or ""
    if body and not body.endswith("…"):
        return body
    path = transcript_path(agent, entry)
    if path and path.exists():
        with path.open("rb") as f:
            f.seek(max(0, path.stat().st_size - 512_000))
            lines = f.read().decode("utf-8", "ignore").splitlines()
        for line in reversed(lines):
            text = assistant_text(line)
            if text:
                return text
    return body or None


def notifications():
    try:
        return json.loads(cmux("list-notifications", "--json") or "[]")
    except ValueError:
        return []


def pending(state, watch, prefix):
    # Without a prefix, notifications are ignored: harnesses post their own
    # (truncated) turn-end notifications, and the turn-end path reads the full text.
    if not prefix:
        return []
    new = [
        n for n in notifications()
        if n["id"] not in state.seen
        and (not watch or n.get("surface_id") in watch)
        and n.get("title", "").startswith(prefix)
    ]
    new.sort(key=lambda n: n.get("created_at", ""))
    for n in new:
        state.mark(n)
    return new


def latest_seq():
    try:
        snap = json.loads(cmux("events", "--snapshot", "--no-heartbeat"))
        return int(snap["resume"]["latest_seq"])
    except (ValueError, KeyError, TypeError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", action="append", default=[])
    ap.add_argument("--prefix", default="")
    ap.add_argument("--timeout", type=float, default=90)
    ap.add_argument("--state", default=os.environ.get("CMUX_WORKSPACE_ID", "default"))
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()

    state = State(a.state)
    refs = surface_refs()
    uuid_of = {r: u for u, r in refs.items()}
    watch = {uuid_of.get(s, s) for s in a.surface}
    ref = lambda u: refs.get(u, u)

    def emit_replies(items):
        for n in items:
            print(f"REPLY {ref(n.get('surface_id'))} {n.get('title','')} | {n.get('body','')}")
        sys.stdout.flush()

    seq_now = latest_seq()
    if a.reset or state.fresh:
        for n in notifications():
            state.mark(n)
        if seq_now is not None:
            state.set_cursor(seq_now)

    # 1. Backlog
    items = pending(state, watch, a.prefix)
    if items:
        emit_replies(items)
        return 0

    deadline = time.monotonic() + a.timeout

    # 3. Fallback: no event stream
    if seq_now is None:
        while time.monotonic() < deadline:
            items = pending(state, watch, a.prefix)
            if items:
                emit_replies(items)
                return 0
            time.sleep(0.5)
        print("TIMEOUT")
        return 2

    # 2. Event stream from the last handled seq
    cursor = state.cursor() or seq_now
    remaining = max(1, int(deadline - time.monotonic()))
    proc = subprocess.Popen(
        [CMUX, "events", "--after", str(cursor),
         "--name", "notification.created", "--name", "agent.notification.decision",
         "--name", "surface.input_sent",
         "--no-heartbeat", "--no-ack", "--timeout", str(remaining)],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
    )
    seen_seq = set()
    try:
        for line in proc.stdout:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            seq = d.get("seq")
            if seq is None or seq in seen_seq:  # cmux emits each event twice
                continue
            seen_seq.add(seq)
            state.set_cursor(seq)
            surf = d.get("surface_id")
            if watch and surf not in watch:
                continue

            if d.get("name") == "surface.input_sent":
                state.set_input(surf, d.get("occurred_at"))
                continue

            if d.get("name") == "notification.created":
                items = pending(state, watch, a.prefix)
                if items:
                    emit_replies(items)
                    return 0
                continue

            payload = d.get("payload") or {}
            kind = payload.get("kind")
            detail = payload.get("message") or payload.get("title") or ""
            if kind == "agent.question.requested":
                print(f"QUESTION {ref(surf)} | {detail}")
                return 0
            if kind == "agent.approval.requested":
                print(f"APPROVAL {ref(surf)} | {detail}")
                return 0
            # Turn ended. Pi reports some normal turn ends as agent.error.reported,
            # so treat both as "turn over" and fall back if no notify came with it.
            if kind in ("agent.turn.completed", "agent.error.reported"):
                items = pending(state, watch, a.prefix)
                if items:
                    emit_replies(items)
                    return 0
                if not state.notified_since_input(surf):
                    text = last_reply(surf, d.get("occurred_at"))
                    if text:
                        print(f"REPLY {ref(surf)} (turn) | {' '.join(text.split())}")
                    else:
                        print(f"TURN_NO_TEXT {ref(surf)} | {kind}")
                    return 0
    finally:
        proc.kill()

    items = pending(state, watch, a.prefix)
    if items:
        emit_replies(items)
        return 0
    print("TIMEOUT")
    return 2


if __name__ == "__main__":
    sys.exit(main())
