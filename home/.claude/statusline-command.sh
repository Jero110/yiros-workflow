#!/bin/bash
input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // ""')
short_cwd=$(basename "$cwd")
model=$(echo "$input" | jq -r '.model.display_name // ""')
used=$(echo "$input" | jq -r '.context_window.used_percentage // empty')

# Ventana de contexto: verde < 70, amarillo < 90, rojo >= 90
ctx_color() {
  if [ "$1" -ge 90 ]; then
    printf '\033[0;31m'
  elif [ "$1" -ge 70 ]; then
    printf '\033[0;33m'
  else
    printf '\033[0;32m'
  fi
}

# Límites de uso: escala propia (cian → magenta → rojo brillante) para que
# no se confundan de un vistazo con la ventana de contexto.
lim_color() {
  if [ "$1" -ge 90 ]; then
    printf '\033[1;31m'
  elif [ "$1" -ge 70 ]; then
    printf '\033[0;35m'
  else
    printf '\033[0;36m'
  fi
}

# Ventana de contexto
if [ -n "$used" ]; then
  used_int=${used%.*}
  ctx_str="$(ctx_color "$used_int")ctx: ${used_int}%\033[0m"
else
  ctx_str="ctx: --"
fi

# Límite de 5 horas: uso y cuánto falta para el reset
lim_used=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
lim_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
session_id=$(echo "$input" | jq -r '.session_id // empty')

# Expone el % y la hora de reset por sesión en un archivo, para que scripts
# externos (ej. cc.zsh / _cc_watch_usage) lean el dato real de backend en vez
# de tener que parsear la pantalla truncada al ancho de la terminal. Una sola
# escritura barata (ya calculamos lim_used arriba), nada de spawns extra.
if [ -n "$lim_used" ] && [ -n "$session_id" ]; then
  mkdir -p "$HOME/.claude/rate-limits" 2>/dev/null
  printf '{"used_percentage":%s,"resets_at":%s}\n' "$lim_used" "${lim_reset:-null}" \
    > "$HOME/.claude/rate-limits/${session_id}.json" 2>/dev/null
fi

if [ -n "$lim_used" ]; then
  lim_int=${lim_used%.*}
  lim_str="$(lim_color "$lim_int")◷ 5h: ${lim_int}%"

  if [ -n "$lim_reset" ]; then
    left=$(( lim_reset - $(date +%s) ))
    [ "$left" -lt 0 ] && left=0
    h=$(( left / 3600 ))
    m=$(( (left % 3600) / 60 ))
    # Hora local del reset, además del tiempo restante
    at=$(date -r "$lim_reset" +%H:%M 2>/dev/null || date -d "@$lim_reset" +%H:%M 2>/dev/null)
    if [ "$h" -gt 0 ]; then
      lim_str="${lim_str} (${h}h${m}m → ${at})"
    else
      lim_str="${lim_str} (${m}m → ${at})"
    fi
  fi
  lim_str="${lim_str}\033[0m"
else
  lim_str="5h: --"
fi

# Guardia de /research: no hace polling ni escribe telemetría. Claude Code ya
# invoca la statusline con el uso actual; únicamente al cruzar 90% detenemos la
# corrida visible y dejamos al supervisor la hora exacta del reset.
SUPERVISOR_PID_FILE="$cwd/logs/research-supervisor.pid"
CLAUDE_PID_FILE="$cwd/logs/research-claude.pid"
PAUSE_FILE="$cwd/logs/pause-until"
GLOBAL_PAUSE_FILE="$HOME/.claude/research-pause-until"

# Umbral configurable para poder PROBAR el mecanismo sin esperar horas.
# Produccion: 90. Para bajarlo NO uses una variable de entorno: la statusline
# corre como proceso hijo y no siempre hereda lo que exportaste en tu shell
# (fallo real el 2026-09-13: la prueba nunca disparo por esto).
# En vez de eso, escribe el numero en un archivo:
#     echo 10 > ~/.claude/research-umbral      # activar prueba
#     rm ~/.claude/research-umbral             # volver a 90
UMBRAL_FILE="$HOME/.claude/research-umbral"
if [ -f "$UMBRAL_FILE" ]; then
  UMBRAL=$(tr -cd '0-9' < "$UMBRAL_FILE")
  [ -z "$UMBRAL" ] && UMBRAL=90
else
  UMBRAL="${RESEARCH_UMBRAL:-90}"
fi

if [ -n "$lim_used" ] && [ "$lim_int" -ge "$UMBRAL" ] && [ -n "$lim_reset" ]; then
  # Una sola marca, solo al cruzar el umbral. /research la lee antes de hacer
  # preguntas o montar el vault, incluso si todavía no hay supervisor activo.
  if [ ! -f "$GLOBAL_PAUSE_FILE" ]; then
    printf '%s\n' "$lim_reset" > "$GLOBAL_PAUSE_FILE"
  fi

  if [ -f "$SUPERVISOR_PID_FILE" ] && [ -f "$CLAUDE_PID_FILE" ] && [ ! -f "$PAUSE_FILE" ]; then
    claude_pid=$(tr -d '[:space:]' < "$CLAUDE_PID_FILE")
    if kill -0 "$claude_pid" 2>/dev/null; then
      printf '%s\n' "$lim_reset" > "$PAUSE_FILE"
      kill -TERM "$claude_pid" 2>/dev/null || true
      lim_str="\033[1;31mPAUSANDO research: uso ${lim_int}%\033[0m"
    fi
  fi
fi

# Límite semanal: solo se muestra cuando ya es relevante (>= 50%)
wk_used=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
wk_str=""
if [ -n "$wk_used" ]; then
  wk_int=${wk_used%.*}
  if [ "$wk_int" -ge 50 ]; then
    wk_str="  $(lim_color "$wk_int")7d: ${wk_int}%\033[0m"
  fi
fi

user=$(whoami)
host=$(hostname -s)

printf "\033[0;34m%s@%s\033[0m  \033[1;34m~/%s\033[0m  \033[0;35m%s\033[0m  %b  %b%b" \
  "$user" "$host" "$short_cwd" "$model" "$ctx_str" "$lim_str" "$wk_str"
