#!/bin/bash
# Prueba qué fuentes de verificación responden desde esta red y escribe el
# resultado al vault. El orquestador lo lee para saber contra qué puede
# verificar — y qué debe marcar como sin-verificar en vez de inventar.
#
# Uso:  ./probar-fuentes.sh [ruta-del-vault]

SALIDA="${1:-vault}/90-Meta/FUENTES-DISPONIBLES.md"
mkdir -p "$(dirname "$SALIDA")"

probar() {
  local nombre="$1" url="$2" nota="$3"
  local code body estado
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 15 "$url" 2>/dev/null)
  body=$(curl -s -m 15 "$url" 2>/dev/null | head -c 80)

  case "$body" in
    *[Zz]scaler*|*"blocked by"*|*"Access Denied"*) estado="BLOQUEADA (proxy)" ;;
    *) case "$code" in
         200) estado="OK" ;;
         429) estado="rate-limit (usable con pausas)" ;;
         403) estado="403 (bloqueada o requiere key)" ;;
         000) estado="sin respuesta" ;;
         *)   estado="HTTP $code" ;;
       esac ;;
  esac

  printf "| %s | %s | %s |\n" "$nombre" "$estado" "$nota" >> "$SALIDA"
  printf "  %-18s %s\n" "$nombre" "$estado"
}

cat > "$SALIDA" <<EOF
---
tipo: meta
titulo: Fuentes de verificación disponibles desde esta red
summary: Qué APIs de verificación de citas responden desde esta máquina y cuáles están bloqueadas.
tags: [meta, fuentes, verificacion]
fecha_consulta: $(date +%Y-%m-%d)
---

# Fuentes de verificación disponibles

> Probado el $(date '+%Y-%m-%d %H:%M'). **El orquestador DEBE leer esto.**
>
> Verifica citas SOLO contra las fuentes marcadas OK.
> Lo que no puedas verificar va como \`estado: sin-verificar\`.
> **Nunca inventes un DOI, un autor o un año.**

| Fuente | Estado | Uso |
|--------|--------|-----|
EOF

echo "Probando fuentes de verificación..."
probar "Crossref"   "https://api.crossref.org/works?query=test&rows=1" "Validar DOIs. La autoritativa."
probar "arXiv"      "https://export.arxiv.org/api/query?search_query=all:test&max_results=1" "Preprints; confirma existencia."
probar "DOAJ"       "https://doaj.org/api/search/articles/test?pageSize=1" "Revistas de acceso abierto."
probar "PubMed"     "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=test&retmax=1" "Biomédicas."
probar "SemanticScholar" "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1" "Citas; 429 frecuente."
probar "OpenAlex"   "https://api.openalex.org/works?search=test&per-page=1" "Catálogo abierto."
probar "Unpaywall"  "https://api.unpaywall.org/v2/10.1038/nature12373?email=test@example.com" "PDFs abiertos."

cat >> "$SALIDA" <<'EOF'

## Cómo verificar una cita

**DOI (la prueba definitiva):**
```bash
curl -s "https://api.crossref.org/works/<DOI>" | jq -r '.message.title[0] // "NO EXISTE"'
```
404 = el DOI no existe. Si lo escribió un agente, **lo inventó**. Bórralo.

**Buscar por título antes de citarlo:**
```bash
curl -s "https://api.crossref.org/works?query.title=<titulo>&rows=3" \
  | jq -r '.message.items[] | "\(.DOI) | \(.title[0])"'
```

**arXiv:**
```bash
curl -s "https://export.arxiv.org/api/query?id_list=<ID>" | grep -o '<title>[^<]*' | tail -1
```

## Regla anti-invención

Toda nota `tipo: paper` lleva `doi:` o `arxiv_id:` **verificado contra la API**,
o `estado: sin-verificar` en el frontmatter.

Una nota que cita un paper sin DOI comprobado es **sospechosa por defecto**.
Es preferible una nota que diga "creo que existe un trabajo sobre X pero no
pude verificarlo" que una cita falsa con autores y año inventados.
EOF

echo
echo "→ Escrito en: $SALIDA"
