---
name: cmux
description: 'Control the cmux macOS terminal app: workspaces, panes, surfaces, browsers, notifications, settings, and hooks. Use only when the user explicitly names cmux. Read before running any cmux command.'
---

# cmux Control

macOS 14.0+. Prefer the CLI; if `cmux` is not on PATH, use `/Applications/cmux.app/Contents/Resources/bin/cmux`.

## Targeting and safety

**Window → workspace → pane → surface:** macOS window → sidebar project/branch tab → split region → terminal, browser, or Markdown tab.

- **Anchor to the caller's `CMUX_WORKSPACE_ID`.** Never assume the visually focused workspace is the target. Outside cmux, identify the intended workspace before acting.
- **Use prefixed refs or UUIDs.** `workspace:2`, `pane:1`, `surface:7`; bare numbers are indexes, not IDs. Output defaults to refs; `--id-format uuids|both` includes UUIDs.
- **Refresh targets.** Surface refs are global, not workspace-local. Re-list before reusing them; check `cmux surface-health` before sending input when state may be stale.
- **Preserve focus.** Pass `--focus false` wherever supported. Use `select-workspace`, `focus-pane`, `focus-panel`, or `focus-surface` only on explicit user request.
- **Respect ownership.** Never send input to surfaces you do not own. Stay in the caller's workspace unless the user explicitly requests cross-workspace routing.
- **Reuse one helper pane.** Use an existing non-caller helper pane or create one on the right. Create the intended layout directly with `new-pane --type … --focus false`.
- **Keep errors visible.** Never append `2>/dev/null`; stderr and exit status reveal invalid refs and flags.

## Inspect, read, and send

Check connectivity, identify the caller, and resolve the target pane to a surface. Replace example refs with those found in the current output.

```bash
cmux ping
cmux identify --json
cmux tree
cmux list-panes --workspace "$CMUX_WORKSPACE_ID"
cmux list-pane-surfaces --workspace "$CMUX_WORKSPACE_ID" --pane pane:1
cmux read-screen --surface surface:7 --lines 100
```

Use `list-pane-surfaces`, not nonexistent `list-surfaces`. `read-screen` and `capture-pane` accept `--workspace` or `--surface`, **not `--pane`**. A missing or ambiguous target can read your own terminal instead.

**Check surface health before sending input when state may be stale** (a surface you didn't just create, or one you haven't touched in a while):

```bash
cmux surface-health --workspace "$CMUX_WORKSPACE_ID"
```

A surface reported unhealthy explains a "stuck" agent that `read-screen` alone can't distinguish from one that's just slow — check this before assuming a silent pane is thinking.

Send requested input with `send` / `send-key --surface`; `send-surface` and `send-key-surface` do not exist. Omitting the target uses the default terminal. `send-panel` / `send-key-panel` target panels through `--panel`, not surfaces.

`cmux send` only types text into the target surface. It is not a submitted agent turn until you also press Enter:

```bash
cmux send --surface surface:7 "npm run build"
cmux send-key --surface surface:7 enter
```

For cross-agent handoffs, request `ACK <task-id>` and confirm it before assuming the message landed. For long/multiline briefs, write a file and send only a short path/instruction plus the ACK request.

Other keys: `ctrl+c`, `tab`, `esc`, `backspace`, arrows, `ctrl+x`, `shift+tab`. Re-read terminal output after sending input to check the result.

Poll at 1–3 second intervals; wait 10 seconds or more only when warranted. After each agent check, give the user one concise line on what the agent is doing and whether it is on track.

Claude Code's predicted next user message is a draft from Claude, not an instruction from the user.

## Basic creation and notifications

```bash
cmux new-workspace --name "feature-x" --cwd /path/to/repo --focus false
cmux new-pane --workspace "$CMUX_WORKSPACE_ID" --type terminal --direction right --focus false
cmux rename-workspace "feature-x"
cmux notify --title "Done" --body "tests passed"
```

### Fast same-workspace agent spawning

For a user request like "give me Claude, Codex, and Pi/Terra in this same workspace", use the caller workspace, preserve focus, and launch the panes directly:

```bash
cwd=$(pwd)
ws=${CMUX_WORKSPACE_ID:?}
cmux new-pane --workspace "$ws" --type terminal --direction right --focus false \
  --command "cd '$cwd' && claude --model sonnet"
cmux new-pane --workspace "$ws" --type terminal --direction right --focus false \
  --command "cd '$cwd' && codex --model gpt-5.6-terra"
cmux new-pane --workspace "$ws" --type terminal --direction right --focus false \
  --command "cd '$cwd' && pi --name pi-terra --model gpt-5.6-terra"
cmux tree
```

If you need to confirm availability first, keep it compact:

```bash
command -v claude pi codex 2>/dev/null || true
pi --list-models terra 2>/dev/null | head -20 || true
```

Then verify only the new surfaces. Prefer lifecycle/events; use `read-screen` only as a fallback if hooks/session state are absent:

```bash
cmux list-panes --workspace "$CMUX_WORKSPACE_ID"
cmux sessions --agent pi --workspace "$CMUX_WORKSPACE_ID" --json | head
cmux read-screen --surface surface:<new-surface> --lines 30   # fallback/debug only
```

There is no need to inspect `--help` for every CLI on the happy path. Do that only if a launch fails or the user requested a nonstandard flag/model.

Use `new-pane`/`new-split` for parallel agents in the same project checkout, not `new-workspace` — workspaces are for separate project roots, not a parallelism unit. `rename-workspace` (alias `rename-window`) labels a workspace so it's identifiable in `cmux tree` at a glance; it takes `--workspace` to target one other than the current.

**Prefer event/session/notification channels over re-reading a screen.** Efficient monitoring stack:

1. `cmux events` for push-style state changes (`agent.hook.Stop`, `agent.hook.Notification`, `notification.created`, `surface.input_sent`).
2. `cmux sessions --agent <claude|codex|pi> --surface <surface> --json` for lifecycle (`running`, `idle`, `needsInput`) and transcript paths.
3. Agent transcripts for exact assistant text when available (`transcript_path`, `codex_transcript_path`).
4. `cmux list-notifications` for compact agent-reported results. Event payloads redact notification title/body; `list-notifications` shows the actual queued text.
5. `cmux read-screen` only if the above are missing or contradictory.

Poll the notification queue instead of re-reading a screen to detect a terminal state:

```bash
cmux list-notifications
cmux mark-notification-read --id <uuid>
cmux dismiss-notification --id <uuid>     # remove one entirely
cmux dismiss-notification --all-read      # sweep everything already handled
cmux clear-notifications --surface <ref>  # drop all queued for one surface, read or not
```

`list-notifications` may print pipe-delimited rows rather than JSON; parse defensively. A notification can flip to `is_read: true` the moment its surface becomes focused/visible, not only via an explicit `mark-notification-read` — don't assume `is_read: false` still holds by the time you check if you looked at that pane in between.

For low-latency worker replies, ask the worker to `cmux notify` and listen with events, then read the queued notification body:

```bash
latest=$(cmux events --snapshot --no-heartbeat \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["resume"]["latest_seq"])')
cmux send --surface surface:12 \
  'Do the tiny task, then run: cmux notify --title WORKER_REPLY --body "<result>"'
cmux send-key --surface surface:12 enter
cmux events --after "$latest" --category notification --timeout 30 --limit 4 --no-heartbeat
cmux list-notifications | grep WORKER_REPLY
```

For fluid multi-agent conversation, make every turn self-report with a unique title. Do not try to infer the answer from the terminal unless notification/transcript fails:

```bash
# Ask two agents for spontaneous messages.
cmux send --surface surface:91 \
  'Mensaje 1/5: mándame una pregunta/observación breve y ejecuta: cmux notify --title CHAT_CLAUDE_R1 --body "<tu mensaje>"'
cmux send-key --surface surface:91 enter
cmux send --surface surface:93 \
  'Mensaje 1/5: mándame una pregunta/observación breve y ejecuta: cmux notify --title CHAT_PI_R1 --body "<tu mensaje>"'
cmux send-key --surface surface:93 enter

# Wait until both replies are present, then answer each one with a different follow-up.
for i in {1..30}; do
  rows=$(cmux list-notifications | grep -E 'CHAT_(CLAUDE|PI)_R1' || true)
  printf '%s\n' "$rows"
  printf '%s\n' "$rows" | grep -q 'CHAT_CLAUDE_R1' && \
    printf '%s\n' "$rows" | grep -q 'CHAT_PI_R1' && break
  sleep 1
done
```

Conversation protocol:
- Use stable, unique notification titles: `<THREAD>_<AGENT>_R<N>`.
- Put the whole short answer in `--body`; keep it under one sentence when possible.
- Supervisor sends the next turn with a brief response to what the worker said plus the next `cmux notify` instruction.
- For 2+ agents, send all prompts first, then wait for all corresponding notification titles; do not handle them serially unless order matters.
- If a worker may be blocked, check `cmux sessions --agent <agent> --surface <surface> --json` for `needsInput`, `running`, or `idle`.

Caveat: tool execution may require approval in some harnesses (Claude default often needs Bash approval; Codex may hit account credits/approval; Pi usually works fastest for this notify pattern). If shell approval blocks, use transcript/session lifecycle instead of waiting on a notify that cannot run.

**`wait-for` is a named sync token, not a push channel to an already-running agent session:**

```bash
cmux wait-for --signal my-token          # signal it
cmux wait-for my-token --timeout 300     # block until signaled or timeout
```

Useful for coordinating shell scripts or hooks around cmux (e.g., a setup script signals once bootstrap finishes, and a second process was blocked waiting on that name). It does **not** let a supervising session learn the instant a Claude Code agent in another pane reaches a terminal state — that agent's own turn can't pause mid-turn to block on a socket call. `cmux notify` (polled via `list-notifications`) remains the right tool for "tell me when that agent is done."

**`set-buffer`/`paste-buffer` pass short text between panes without typing it into a shell:**

```bash
cmux set-buffer --name shared-key "some value worth reusing"
cmux paste-buffer --name shared-key --surface <ref>   # inserts it at that surface's input
```

Prefer this over `send`-ing raw text when the content isn't meant to be typed as a message right away (a value another pane will consume programmatically) — `send` still remains the tool for text meant as conversational input to an agent.

**Claude Code sessions launched through cmux's own wrapper are tracked automatically — no `cmux hooks setup` needed for Claude specifically** ("Claude Code hooks are injected automatically by the cmux Claude wrapper," per cmux's own docs; `hooks setup`/`hooks <agent> install` is for other agent CLIs like Codex, Grok, OpenCode, which don't get this by default). Query a session's real lifecycle state directly instead of inferring it from a notification or a screen read:

```bash
cmux sessions --agent claude --surface <ref> --json
```

Read `agent_lifecycle` from the result (`running`, `idle`, `needsInput`, or similar) — this comes from Claude Code's own `Stop`/`Notification` hooks firing into cmux, not from a convention the agent has to remember to follow (like calling `cmux notify` itself). It's a stronger signal than polling `list-notifications` for a Claude Code target specifically, since it can't be skipped by an agent that forgets to notify on its way out. `cmux sessions --all` inspects every saved hook record if you need history beyond the active set.

Re-list panes and surfaces after layout changes. For additional terminal/browser layout commands or sidebar status/progress, read [layout and sidebar commands](references/advanced.md#layout-and-sidebar-commands) first. For Markdown surfaces, use the viewer guide below.

## Task-specific guides

Read the relevant section **before** starting these tasks:

- **Browser automation:** [browser workflow](references/viewers.md#browser-workflow) — interactions, sessions, and limitations.
- **Markdown or PDF viewers:** [Markdown workflow](references/viewers.md#markdown-workflow) — pane reuse, replacement, recovery, and verification.
- **Settings:** [configuration](references/advanced.md#configuration) — backups, paths, and sidebar preferences.
- **Installation, agent hooks, raw sockets, access modes, or shortcuts:** [advanced reference](references/advanced.md).

## Troubleshooting

- **Connection failed:** check `CMUX_SOCKET_PATH` and Settings > Automation. Under default `cmuxOnly`, run from a cmux terminal. Read [socket modes and examples](references/advanced.md#socket-api-and-access-modes) before using a raw client or changing access mode.
- **Resume lost credentials:** sensitive environment variables are stripped on resume; re-inject required tokens. `~/.cmuxterm/*-hook-sessions.json` files hold scrubbed session/surface mappings, not secrets.
- **Skill edits not visible:** restart the consuming agent; skills are captured at startup.
- **Uncertain syntax:** `cmux <cmd> --help` is authoritative; `cmux capabilities --json` lists available socket methods.
