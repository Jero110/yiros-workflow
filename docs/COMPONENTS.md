# Components

This repo is organized by installable layer. You can install one layer, several layers, or all layers.

## Human-facing layers

| Layer | Files | Purpose | Safe to skip? |
| --- | --- | --- | --- |
| Shared protocol | `home/.agents/` | Common rules and skills for agent-to-agent work | No, if you want cross-harness coordination |
| Claude Code | `home/.claude/` | Claude settings, hooks, statusline, and skills | Yes, if you do not use Claude Code |
| Pi | `home/.pi/agent/` | Pi settings, extensions, theme, and npm packages | Yes, if you do not use Pi |
| Codex | `home/.codex/` | Codex global instructions and hooks | Yes, if you do not use Codex |
| cmux | `home/.cmux/`, `home/.config/cmux/` | Workspace/pane hooks and cmux UI config | No, if you want the integrated workflow |
| Terminal UI | `home/.config/ghostty/`, `zsh/` | Visual theme files | Yes. Skip if you like your terminal as-is |
| Shell helper | `home/.config/zsh/cc.zsh` | Optional `cc` wrapper for named Claude sessions | Yes |

No shell startup file is installed by default. Add `source ~/.config/zsh/cc.zsh` yourself only if you want the `cc` helper.

## Agent-facing workflow

The core protocol is cmux-first:

- stay in the caller's cmux workspace;
- do not operate on another pane unless asked;
- use `harnesses` to choose the right harness/model;
- use `cmux` to open panes and send prompts;
- after `cmux send`, also send Enter with `cmux send-key`;
- require `ACK <task-id>` before treating a worker as dispatched;
- use planner/executor/worker/reviewer roles for multi-step work.

Main files:

- `home/.agents/shared/cross-harness-workflow.md`: shared handoff protocol.
- `home/.pi/agent/AGENTS.md`: Pi global instructions.
- `home/.claude/CLAUDE.md`: Claude Code global instructions.
- `home/.codex/AGENTS.md`: Codex global instructions.

## Skills

Skill directories are intentionally split by where each harness reads them.

### Shared skills

`home/.agents/skills/` contains skills that are not tied to only one harness, for example code review, debugging, frontend design, grilling, Herdr, notebooks, research, and shared workflow helpers.

### Claude Code skills

`home/.claude/skills/` contains Claude-native skills such as:

- `planner`
- `executor`
- `worker`
- `reviewer`
- `cmux`
- `harnesses`
- `cmux-live-worker`
- `framework-retro`

Many entries in `home/.agents/skills/` and `home/.claude/skills/` are symlinks to the same source. Preserve them with `rsync -a`.

### Pi-specific pieces

Pi does not use the Claude skill loader. Pi-specific behavior is in:

- `home/.pi/agent/AGENTS.md`
- `home/.pi/agent/extensions/`
- `home/.pi/agent/settings.json`
- `home/.pi/agent/npm/package.json`
- `home/.pi-lens/config.json` disables automatic Lens context injection while keeping Lens available on demand

Current Pi npm dependencies:

- `pi-lens`
- `pi-mcp-adapter`
- `pi-web-access`

`pi-background-tasks` is intentionally absent.

## Security boundaries

Never copy these into the repo or between machines:

- credentials or auth files;
- `settings.local.json`;
- sessions, histories, logs, caches, databases;
- `node_modules`;
- backup files;
- machine-specific trust or permission files.

Run this before publishing:

```sh
./scripts/check-public.sh --online
```
