# yiros-workflow

Personal workflow backup for moving to a new machine. This repo stores the parts of my agent/terminal setup that are meant to be portable: Pi, Claude Code, Codex, cmux, Ghostty, shared skills, shell helpers, and themes.

Do not treat this as a blind dotfiles installer. Review paths first, then copy the pieces you want.

This public version is sanitized: machine-specific absolute paths, Codex project allow rules, Claude plugin/job metadata, auth files, sessions, logs, and caches are intentionally omitted or templated.

## What is included

### Machine dependencies

- `Brewfile` — Homebrew formulae/casks, VS Code extensions, global npm/uv tools captured from this machine. Use it as a starting point on a fresh Mac, then install apps that are not managed by Homebrew.

### Terminal and UI

- `home/.config/ghostty/` — Ghostty config, theme, and local theme backups.
- `home/.config/cmux/` — cmux UI config, workspace colors, pane colors, shortcuts, and backups.
- `home/.cmux/hooks/` — cmux hook scripts, mainly Codex lifecycle/notification hooks.
- `home/.p10k.zsh` — Powerlevel10k prompt theme.
- `home/.zshrc`, `home/.zprofile`, `home/.bash_profile` — shell startup files.
- `home/.config/zsh/cc.zsh` — Claude Code wrapper/helpers.

### Pi

- `home/.pi/agent/AGENTS.md` — global Pi instructions.
- `home/.pi/agent/settings.json` — Pi settings: default provider/model, theme, packages.
- `home/.pi/agent/models-store.json` — model catalog/custom model metadata.
- `home/.pi/agent/extensions/` — custom Pi extensions:
  - `cmux-session.ts`
  - `harness-handoff.ts`
  - `laya-triage.ts`
  - `selfhealing.ts`
  - `usage-footer.ts`
  - `workflow.ts`
- `home/.pi/agent/themes/` — Pi themes, including `dark-tokyo-soft.json`.
- `home/.pi/agent/npm/` — Pi local package manifest/lock for installed packages.

### Claude Code

- `home/.claude/CLAUDE.md` — global Claude Code instructions.
- `home/.claude/settings.json` and `settings.local.json` — Claude Code settings and local allowlist.
- `home/.claude/statusline-command.sh` — custom status line.
- `home/.claude/hooks/` — custom Claude hooks.
- `home/.claude/skills/` — Claude skills, including workflow orchestration skills.

Important custom scripts inside skills:

- `home/.claude/skills/harnesses/scripts/agent-inbox.py` — inbox/watcher helper used by workflow/cmux orchestration.
- `home/.claude/skills/executor/scripts/pretrust.sh` — pretrust helper for worker worktrees.
- `home/.claude/skills/executor/scripts/wait-agents.sh` — helper for waiting on agent panes.
- `home/.claude/skills/research/plantillas/lanzar.sh` — research launcher template.
- `home/.claude/skills/research/referencias/auditar.sh` — research audit helper.
- `home/.claude/skills/research/referencias/probar-fuentes.sh` — source-check helper.

### Shared skills and harness workflow

- `home/.agents/shared/cross-harness-workflow.md` — shared cross-harness coordination protocol.
- `home/.agents/skills/` — shared skills used by Claude/Pi/Codex workflows.

Some skills are symlinks between `.agents/skills` and `.claude/skills`; keep symlinks intact when restoring.

### Codex/OpenAI harness

- `home/.codex/AGENTS.md` — global Codex instructions.
- `home/.codex/config.toml` — Codex model/config/trust settings.
- `home/.codex/hooks.json` — Codex hooks.
- `home/.codex/rules/` — Codex rules.
- `home/.codex/herdr-agent-state.sh` — harness state helper.

## What is intentionally excluded

This repo should not contain credentials or machine-local runtime state. Do not add these unless you know exactly why:

- `auth.json`
- tokens, secrets, keys, API keys
- histories and transcripts
- sessions
- logs
- sqlite/db files
- caches
- telemetry
- `node_modules`
- virtualenvs
- Claude plugin metadata/jobs/accounts

## Fresh machine restore guide for an agent

If an agent is asked to restore this setup on a new machine, use this procedure:

1. Clone repo:

   ```sh
   git clone https://github.com/Jero110/yiros-workflow.git ~/workflow
   cd ~/workflow
   ```

   Optional machine dependencies, if Homebrew is available:

   ```sh
   brew bundle --file Brewfile
   ```

   Install separately if missing: cmux.app, Claude.app, ChatGPT/Codex app, and any private/manual app not handled by Homebrew.

2. Review before copying:

   ```sh
   find home -maxdepth 3 -type f | sort
   find home -type l -ls
   ```

3. Copy terminal configs:

   ```sh
   mkdir -p ~/.config ~/.cmux
   rsync -a home/.config/ghostty/ ~/.config/ghostty/
   rsync -a home/.config/cmux/ ~/.config/cmux/
   rsync -a home/.cmux/hooks/ ~/.cmux/hooks/
   ```

4. Copy Pi config:

   ```sh
   mkdir -p ~/.pi/agent
   cp home/.pi/agent/AGENTS.md ~/.pi/agent/AGENTS.md
   cp home/.pi/agent/settings.json ~/.pi/agent/settings.json
   cp home/.pi/agent/models-store.json ~/.pi/agent/models-store.json
   rsync -a home/.pi/agent/extensions/ ~/.pi/agent/extensions/
   rsync -a home/.pi/agent/themes/ ~/.pi/agent/themes/
   rsync -a home/.pi/agent/npm/ ~/.pi/agent/npm/
   ```

5. Copy Claude Code config and skills:

   ```sh
   mkdir -p ~/.claude
   cp home/.claude/CLAUDE.md ~/.claude/CLAUDE.md
   cp home/.claude/settings.json ~/.claude/settings.json
   cp home/.claude/settings.local.json ~/.claude/settings.local.json
   cp home/.claude/statusline-command.sh ~/.claude/statusline-command.sh
   rsync -a home/.claude/hooks/ ~/.claude/hooks/
   rsync -a home/.claude/skills/ ~/.claude/skills/
   chmod +x ~/.claude/statusline-command.sh ~/.claude/hooks/*.sh 2>/dev/null || true
   ```

6. Copy shared agent skills:

   ```sh
   mkdir -p ~/.agents
   rsync -a home/.agents/ ~/.agents/
   ```

7. Copy Codex config:

   ```sh
   mkdir -p ~/.codex
   cp home/.codex/AGENTS.md ~/.codex/AGENTS.md
   cp home/.codex/config.toml ~/.codex/config.toml
   cp home/.codex/hooks.json ~/.codex/hooks.json
   cp home/.codex/herdr-agent-state.sh ~/.codex/herdr-agent-state.sh
   rsync -a home/.codex/rules/ ~/.codex/rules/
   chmod +x ~/.codex/herdr-agent-state.sh 2>/dev/null || true
   ```

8. Copy shell files if desired:

   ```sh
   cp home/.zshrc ~/.zshrc
   cp home/.zprofile ~/.zprofile
   cp home/.p10k.zsh ~/.p10k.zsh
   mkdir -p ~/.config/zsh
   cp home/.config/zsh/cc.zsh ~/.config/zsh/cc.zsh
   ```

9. Re-auth manually. The repo does not include credentials:

   ```sh
   pi auth
   claude
   codex login
   gh auth login
   ```

10. Verify:

   ```sh
   pi --help
   cmux ping
   git -C ~/workflow status --short --branch
   ```

## Agent instruction for future updates

When asked to update this repo:

1. Work in `~/workflow`.
2. Copy only portable config, skills, extensions, themes, scripts, and docs.
3. Do not copy credentials, sessions, histories, logs, caches, sqlite/db files, telemetry, or generated runtime state.
4. Run a quick keyword scan for secrets before committing.
5. Commit with a clear message.
6. Push to `origin main` only when explicitly asked.
