#!/bin/bash
# Auditoría de una corrida de research. Correr en sesión APARTE y pegarle
# la salida al auditor.
#
# Uso:  ./auditar.sh [raiz-del-proyecto]

RAIZ="${1:-.}"
cd "$RAIZ" || exit 1
V="vault"

echo "======================================================"
echo " AUDITORÍA — $(date '+%Y-%m-%d %H:%M')"
echo " Proyecto: $(pwd)"
echo "======================================================"

echo
echo "=== GOAL (¿sigue alineado?) ==="
head -25 "$V/90-Meta/GOAL.md" 2>/dev/null || echo "  SIN GOAL.md ← problema grave"

echo
echo "=== NOTAS POR CARPETA ==="
for d in "$V"/*/; do
  printf "  %-24s %s\n" "$(basename "$d")" "$(ls -1 "$d"*.md 2>/dev/null | wc -l | tr -d ' ')"
done

echo
echo "=== ESTADOS (¿verifica o solo lee?) ==="
grep -rh "^estado:" "$V" 2>/dev/null | sort | uniq -c | sort -rn | sed 's/^/  /'
echo "  → si domina 'sin-verificar', lee SOBRE las cosas sin comprobarlas"

echo
echo "=== DATOS DESCARGADOS (bytes reales = trabajo real) ==="
du -sh data/raw/* 2>/dev/null | head -20 | sed 's/^/  /' || echo "  (vacío)"

echo
echo "=== CITAS SIN DOI VERIFICADO (riesgo de invención) ==="
n=0
for f in $(grep -rl "tipo: paper" "$V" 2>/dev/null); do
  grep -qE "^(doi|arxiv_id):" "$f" || { echo "  SIN DOI: $f"; n=$((n+1)); }
done
[ "$n" -eq 0 ] && echo "  ✓ todas las notas de paper tienen identificador"

echo
echo "=== NOTAS SIN SUMMARY (rompen la compresión) ==="
find "$V" -name "*.md" ! -name "MOC-*" ! -name "INDEX.md" ! -name "CONVENCIONES.md" \
  ! -name "GOAL.md" ! -name "ARBOL.md" ! -name "FUENTES-DISPONIBLES.md" 2>/dev/null \
  -exec sh -c 'grep -q "^summary:" "$1" || echo "  FALTA: $1"' _ {} \; | head -15

echo
echo "=== NOTAS DEMASIADO LARGAS (>800 palabras = acumula) ==="
find "$V" -name "*.md" 2>/dev/null \
  -exec sh -c 'w=$(wc -w < "$1"); [ "$w" -gt 800 ] && echo "  $w palabras: $1"' _ {} \; | head -10

echo
echo "=== IDEAS GENERADAS ==="
if [ -f "$V/40-Hipotesis/IDEAS.md" ] || [ -f "$V/IDEAS.md" ]; then
  grep -hE "^[-*] |^### " "$V"/**/IDEAS.md "$V"/IDEAS.md 2>/dev/null | head -25 | sed 's/^/  /'
else
  echo "  (sin IDEAS.md)"
fi
echo "  → ¿son DIVERSAS o variaciones de la misma?"

echo
echo "=== ÁRBOL: ramas exploradas vs pendientes ==="
grep -oE "\[(sin-explorar|en-curso|prometedor|agotado)\]" "$V/00-INDEX/ARBOL.md" 2>/dev/null \
  | sort | uniq -c | sed 's/^/  /' || echo "  (sin ARBOL.md)"

echo
echo "=== ACTIVIDAD RECIENTE ==="
echo "  archivos tocados en la última hora:"
find "$V" data -newermt "-1 hour" -type f 2>/dev/null | wc -l | sed 's/^/    /'
echo "  últimas líneas del supervisor:"
tail -5 logs/supervisor.log 2>/dev/null | sed 's/^/    /' || echo "    (sin log)"

echo
echo "======================================================"
