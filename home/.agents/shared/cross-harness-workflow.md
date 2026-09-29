# Cross-Harness Workflow Core

Applies to Pi, Claude Code, Codex, and any agent coordinated through cmux.

## Handoff transport rule

`cmux send` only types into the target surface. It does not guarantee the target agent received a submitted turn. Every cross-harness handoff must use this sequence:

```bash
cmux send --surface <surface> "<short instruction or file pointer>"
cmux send-key --surface <surface> enter
```

Never count a message as delivered after `cmux send` alone.

## Before sending to an agent pane

1. Resolve the target surface inside the caller's `CMUX_WORKSPACE_ID`.
2. Check health/readiness when the surface is not freshly confirmed:
   ```bash
   cmux surface-health --workspace "$CMUX_WORKSPACE_ID"
   cmux read-screen --surface <surface> --lines 30
   ```
3. Do not send a brief into startup dialogs, trust prompts, update menus, dead shells, or bare shell prompts. Clear or relaunch first.

## Long briefs

For long or multiline briefs, write the brief to a file and send only a short pointer:

```bash
cmux send --surface <surface> "Read /absolute/path/to/brief.md and execute it. Reply: ACK <task-id>."
cmux send-key --surface <surface> enter
```

This avoids multiline text being interpreted by a shell or half-submitted composer.

## ACK requirement

Every executor/dispatcher handoff must request an explicit acknowledgement:

```text
When you receive this, reply exactly: ACK <task-id>
```

Do not mark the worker as dispatched, and do not assume work started, until the ACK appears via notification, transcript/session state, or screen read fallback. If no ACK appears, inspect the target surface before resending.

## Failure interpretation

If the brief appears typed but not submitted, or shell errors like `command not found` / `zsh: bad pattern` appear, treat it as a transport/readiness failure, not a worker failure. Reconfirm the surface, clear dialogs, and resend with `cmux send` plus `cmux send-key enter`.
