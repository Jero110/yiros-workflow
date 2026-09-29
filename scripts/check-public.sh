#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

online=0
if [[ "${1:-}" == "--online" ]]; then
  online=1
elif [[ $# -gt 0 ]]; then
  printf 'usage: %s [--online]\n' "$0" >&2
  exit 2
fi

for command_name in git jq python3 zsh; do
  command -v "$command_name" >/dev/null || {
    printf 'missing required command: %s\n' "$command_name" >&2
    exit 1
  }
done

repo_files() {
  while IFS= read -r file; do
    if [[ -e "$file" || -L "$file" ]]; then
      printf '%s\n' "$file"
    fi
  done < <(git ls-files --cached --others --exclude-standard)
}

repo_regular_files() {
  while IFS= read -r file; do
    if [[ -f "$file" ]]; then
      printf '%s\n' "$file"
    fi
  done < <(repo_files)
}

printf 'Checking local runtime artifacts...\n'
if find . \
  \( -path './.git' -o -path './home/.pi/agent/npm/node_modules' \) -prune -o \
  \( -name '~' -o -name '.cmuxterm' \) -print | grep -q .; then
  find . \
    \( -path './.git' -o -path './home/.pi/agent/npm/node_modules' \) -prune -o \
    \( -name '~' -o -name '.cmuxterm' \) -print
  printf 'local cmux/runtime artifact found; remove it before publishing\n' >&2
  exit 1
fi

printf 'Checking tracked filenames...\n'
if repo_files | grep -E '(^|/)(auth\.json|settings\.local\.json|history\.jsonl|credentials?|secrets?)(/|$|\.)'; then
  printf 'blocked sensitive filename is tracked\n' >&2
  exit 1
fi

if repo_files | grep -E '(\.bak($|[.-])|\.swp$|~$)'; then
  printf 'backup or editor artifact is tracked\n' >&2
  exit 1
fi

printf 'Checking high-confidence credential patterns...\n'
secret_pattern='-----BEGIN (RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|glpat-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}'
secret_found=0
while IFS= read -r file; do
  if grep -Iq . "$file" && grep -Eq -- "$secret_pattern" "$file"; then
    printf '%s\n' "$file"
    secret_found=1
  fi
done < <(repo_regular_files)
if [[ $secret_found -ne 0 ]]; then
  printf 'possible credential found; inspect the filenames above\n' >&2
  exit 1
fi

printf 'Validating JSON...\n'
while IFS= read -r file; do
  jq -e . "$file" >/dev/null
done < <(repo_regular_files | grep -E '\.json$')

printf 'Validating shell syntax...\n'
while IFS= read -r file; do
  case "$file" in
    *.zsh|*/.zshrc|*/.zprofile) zsh -n "$file" ;;
    *.sh|*/.bash_profile) bash -n "$file" ;;
  esac
done < <(repo_regular_files)

printf 'Validating Python syntax...\n'
while IFS= read -r file; do
  python3 -c 'import ast, sys; ast.parse(open(sys.argv[1], encoding="utf-8").read(), filename=sys.argv[1])' "$file"
done < <(repo_regular_files | grep -E '\.py$')

printf 'Validating TOML...\n'
while IFS= read -r file; do
  python3 -c 'import sys, tomllib; tomllib.load(open(sys.argv[1], "rb"))' "$file"
done < <(repo_regular_files | grep -E '\.toml$')

printf 'Checking whitespace and conflict markers...\n'
git diff --check
conflict_found=0
while IFS= read -r file; do
  if grep -Iq . "$file" && grep -n -E -- '^(<<<<<<<|=======|>>>>>>>)' "$file"; then
    conflict_found=1
  fi
done < <(repo_regular_files)
if [[ $conflict_found -ne 0 ]]; then
  printf 'merge conflict marker found\n' >&2
  exit 1
fi

if [[ $online -eq 1 ]]; then
  command -v npm >/dev/null || {
    printf 'missing required command for online audit: npm\n' >&2
    exit 1
  }
  printf 'Auditing npm lockfile...\n'
  npm audit --prefix home/.pi/agent/npm --package-lock-only --audit-level=moderate
fi

printf 'Public-safety checks passed.\n'
