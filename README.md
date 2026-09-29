# Yiros Workflow

Portable cmux-first workflow for Pi, Claude Code, Codex, and human operators.

It is not a dotfiles dump. It is a small set of reusable agent instructions, skills, cmux hooks, harness config, and optional terminal theme files. Credentials, sessions, logs, caches, local permissions, and backups stay out of the repo.

## What is included

| Layer | Path | What it changes | Install if you want |
| --- | --- | --- | --- |
| Shared agent protocol | `home/.agents/` | Global cross-harness rules and shared skills | Pi/Claude/Codex to coordinate the same way |
| Claude Code | `home/.claude/` | Claude settings, statusline, hooks, Claude skills | Claude Code as planner/executor/worker/reviewer |
| Pi | `home/.pi/agent/` | Pi settings, extensions, theme, npm packages | Pi inside the same cmux workflow |
| Codex | `home/.codex/` | Codex instructions, hooks, rules | Codex panes in the workflow |
| cmux | `home/.cmux/`, `home/.config/cmux/` | cmux hooks and UI config | event-based multi-agent orchestration |
| Terminal UI | `home/.config/ghostty/`, `zsh/` | Ghostty and Powerlevel10k themes only | the same terminal look |
| Claude helper shell | `home/.config/zsh/cc.zsh` | optional `cc` wrapper for named Claude sessions | easier Claude session management |

Shell startup files like `.zshrc`, `.zprofile`, and `.bash_profile` are intentionally not shipped. If you do not want to change your terminal UI, skip the Terminal UI layer.

## The workflow model

1. A human starts from cmux.
2. A planner writes a plan.
3. An executor opens isolated worker panes/worktrees.
4. Workers report back through cmux, not by stealing each other's panes.
5. Reviewers check completed diffs against the original brief.
6. Handoffs use `cmux send` plus `cmux send-key enter`, with an explicit `ACK <task-id>`.

Agents get the protocol from `~/.agents/shared/cross-harness-workflow.md` plus their harness-specific global instructions.

## Skills layout

Claude Code and the shared agent layer intentionally share many skills through symlinks:

- `home/.agents/skills/*`: shared skills usable across harnesses.
- `home/.claude/skills/*`: Claude-native skills.
- symlinked skills are one logical skill, exposed in both places.
- Pi-specific functionality lives under `home/.pi/agent/extensions/` and npm packages, not as Claude skills.

See `docs/COMPONENTS.md` for the map.

## Quick safety check

```sh
git clone https://github.com/Jero110/yiros-workflow.git ~/workflow
cd ~/workflow
./scripts/check-public.sh --online
```

Current npm audit status for `home/.pi/agent/npm`: `found 0 vulnerabilities`.

`pi-background-tasks` is not included because its compatible dependency chain previously pulled a moderate `undici` advisory.

## Install only what you want

Run commands from the repo root. Review files before overwriting existing config.

### 1. Shared protocol only

```sh
mkdir -p ~/.agents
rsync -a home/.agents/ ~/.agents/
```

### 2. Claude Code layer

```sh
mkdir -p ~/.claude
rsync -a home/.claude/ ~/.claude/
chmod +x ~/.claude/statusline-command.sh ~/.claude/hooks/*.sh
```

### 3. Pi layer

```sh
mkdir -p ~/.pi/agent
rsync -a home/.pi/agent/ ~/.pi/agent/ --exclude npm/node_modules
npm install --prefix ~/.pi/agent/npm --ignore-scripts
npm audit --prefix ~/.pi/agent/npm --package-lock-only
```

### 4. Codex layer

```sh
mkdir -p ~/.codex
rsync -a home/.codex/ ~/.codex/
chmod +x ~/.codex/herdr-agent-state.sh
```

### 5. cmux layer

```sh
mkdir -p ~/.cmux ~/.config/cmux
rsync -a home/.cmux/hooks/ ~/.cmux/hooks/
rsync -a home/.config/cmux/ ~/.config/cmux/
```

### 6. Optional terminal UI

```sh
mkdir -p ~/.config/ghostty
rsync -a home/.config/ghostty/ ~/.config/ghostty/
```

Powerlevel10k themes are in `zsh/`. Copy one manually only if you want that prompt style.

### 7. Optional Claude shell helper

```sh
mkdir -p ~/.config/zsh
cp home/.config/zsh/cc.zsh ~/.config/zsh/cc.zsh
printf '\nsource ~/.config/zsh/cc.zsh\n' >> ~/.zshrc
```

The `cc` wrapper keeps Claude permission prompts by default. It only passes `--dangerously-skip-permissions` when you explicitly run with `CC_DANGEROUS_SKIP_PERMISSIONS=1`.

## Install with an agent

Give the agent this instruction:

> Read `docs/AGENT_INSTALL.md` and `docs/COMPONENTS.md`. Inspect my existing files, propose the exact layers and destination paths, and wait for approval before overwriting anything. Do not copy credentials, sessions, logs, caches, histories, local permission files, or backups.

## Verify

```sh
./scripts/check-public.sh --online
pi --help
claude --version
codex --version
cmux ping
```

Authentication is always local and manual:

```sh
pi auth
claude
codex login
gh auth login
```

## Maintenance rules

- No credentials, tokens, sessions, histories, logs, caches, local permissions, or backups.
- No `node_modules`; keep only `package.json` and `package-lock.json`.
- Keep symlinks as symlinks; use `rsync -a`.
- Run `./scripts/check-public.sh --online` before publishing.
- Review every diff before pushing.

See `SECURITY.md` and `THIRD_PARTY_NOTICES.md` before redistributing bundled material.
