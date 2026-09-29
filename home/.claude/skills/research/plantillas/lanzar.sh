#!/bin/bash
# Lanza una corrida FOCUSED: una sola sesión, sin supervisor.
# Termina al cumplir el goal o al agotar los ciclos previstos.
#
#   ./scripts/lanzar.sh        -> background (devuelve un id corto)
#   ./scripts/lanzar.sh fg     -> primer plano, para ver qué hace
#
# Para SUSTAINED (no para nunca) usa ./scripts/supervisor.sh

set -euo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$RAIZ"
mkdir -p logs data/raw

MODO="${1:-bg}"
PROMPT=$(cat "$RAIZ/scripts/ORCHESTRATOR_PROMPT.md")

ARGS=(
  --model opus
  --effort high
  --permission-mode bypassPermissions
  --agents "$(cat "$RAIZ/scripts/agents.json")"
  --add-dir "$RAIZ"
  --name "research-$(basename "$RAIZ")"
  --autocompact 200000
)

if [ "$MODO" = "fg" ]; then
  echo "→ Primer plano. Ctrl+C para parar."
  claude "${ARGS[@]}" "$PROMPT"
else
  echo "→ Lanzando en background..."
  claude --bg "${ARGS[@]}" "$PROMPT"
  echo
  echo "  claude agents        # ver la corrida y su id"
  echo "  claude logs <id>     # ver qué hace"
  echo "  claude attach <id>   # entrar a corregir el rumbo"
  echo "  claude stop <id>     # detener"
fi
