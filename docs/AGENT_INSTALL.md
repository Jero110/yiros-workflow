# Agent install guide

Use this when a human asks you to install Yiros Workflow on a macOS account.

Goal: install only approved layers, preserve existing config, and keep secrets/local runtime state out of the repo and out of copies.

## Rules

1. Read `README.md`, `docs/COMPONENTS.md`, `.gitignore`, and `SECURITY.md` first.
2. Inspect existing destination paths before proposing changes.
3. Show a layer-by-layer and file-by-file plan.
4. Wait for explicit approval before overwriting anything.
5. Preserve symlinks with `rsync -a`.
6. Do not copy credentials, auth files, sessions, histories, logs, caches, databases, telemetry, local permission files, `settings.local.json`, `node_modules`, or backups.
7. Do not install shell startup files. This repo intentionally does not ship `.zshrc`, `.zprofile`, or `.bash_profile`.
8. Do not change terminal UI unless the human explicitly chooses the Terminal UI layer.
9. Do not enable dangerous/unattended permission modes unless the human explicitly asks for that exact change.
10. Do not authenticate, push, publish, or change repo visibility without explicit approval.

## Preflight

```sh
uname -s
git status --short --branch
command -v rsync jq python3 node npm zsh
find home -type l -print
./scripts/check-public.sh --online
```

Inspect destinations without printing secret values:

```sh
for path in \
  ~/.agents \
  ~/.claude \
  ~/.pi/agent \
  ~/.codex \
  ~/.cmux \
  ~/.config/cmux \
  ~/.config/ghostty \
  ~/.config/zsh/cc.zsh; do
  test -e "$path" && printf 'exists: %s\n' "$path"
done
```

Stop and report any failed check.

## Install commands by layer

Run only the layers the human approved.

### Shared protocol

```sh
mkdir -p ~/.agents
rsync -a home/.agents/ ~/.agents/
```

### Claude Code

```sh
mkdir -p ~/.claude
rsync -a home/.claude/ ~/.claude/
chmod +x ~/.claude/statusline-command.sh ~/.claude/hooks/*.sh
```

### Pi

```sh
mkdir -p ~/.pi/agent
rsync -a home/.pi/agent/ ~/.pi/agent/ --exclude npm/node_modules
npm install --prefix ~/.pi/agent/npm --ignore-scripts
npm audit --prefix ~/.pi/agent/npm --package-lock-only
```

### Codex

```sh
mkdir -p ~/.codex
rsync -a home/.codex/ ~/.codex/
chmod +x ~/.codex/herdr-agent-state.sh
```

### cmux

```sh
mkdir -p ~/.cmux ~/.config/cmux
rsync -a home/.cmux/hooks/ ~/.cmux/hooks/
rsync -a home/.config/cmux/ ~/.config/cmux/
```

### Optional terminal UI

Only if the human explicitly wants the terminal look:

```sh
mkdir -p ~/.config/ghostty
rsync -a home/.config/ghostty/ ~/.config/ghostty/
```

Powerlevel10k prompt variants live in `zsh/`; copy one only on request.

### Optional Claude shell helper

Only if the human wants the `cc` wrapper:

```sh
mkdir -p ~/.config/zsh
cp home/.config/zsh/cc.zsh ~/.config/zsh/cc.zsh
```

Then ask before adding this line to their shell startup file:

```sh
source ~/.config/zsh/cc.zsh
```

## Local auth

Never copy auth from another machine. Ask the human to run the relevant commands:

```sh
pi auth
claude
codex login
gh auth login
```

## Verify

```sh
jq -e . ~/.pi/agent/settings.json
jq -e . ~/.claude/settings.json
python3 -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$HOME/.codex/config.toml"
npm audit --prefix ~/.pi/agent/npm --package-lock-only
pi --help
claude --version
codex --version
cmux ping
```

Skip checks for layers that were not installed.

## Final report

Keep it short:

- layers installed;
- files changed;
- checks run and results;
- skipped layers;
- manual auth still needed.
