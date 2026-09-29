# Nota sobre `agents.json`

> **NUNCA metas comentarios dentro de `agents.json`.**
> `claude --agents` valida **cada clave de primer nivel** como definición de un
> agente. Una clave extra —aunque empiece con `_`— tumba el lanzamiento:
>
> ```
> Error: Invalid --agents configuration: _comentario: Invalid input
> ```
>
> La corrida muere en 0 segundos. Por eso esta nota vive aquí y no allá.

## Esquema que el CLI exige

Cada clave de primer nivel es el **nombre del rol**, y su valor debe tener
exactamente:

| Campo | Obligatorio | Qué es |
|---|---|---|
| `description` | sí | Una línea. El orquestador la lee para decidir a quién despachar. |
| `prompt` | sí | Las instrucciones del rol. |
| `tools` | sí | Array de herramientas permitidas. |

Nada más. Sin `_comentario`, sin `notas`, sin `version`.

## Cómo adaptar la plantilla

Ajusta los roles al dominio del goal. El patrón base son tres funciones:

- uno que **ADQUIERE** (busca, descarga, abre y verifica datos reales)
- uno que **SINTETIZA** (convierte lo del vault en ideas juzgadas)
- uno que **VERIFICA** escéptico (intenta romper lo que se afirmó)

`investigador` es el cuarto, para literatura y conceptos.

**El contrato de retorno —las últimas dos líneas de cada `prompt`— no se cambia
nunca.** Es lo que mantiene chico el contexto del orquestador: el subagente
quema contexto, escribe a disco y devuelve ≤10 líneas.

## Validar antes de lanzar

`supervisor.sh` ya lo hace y aborta si falla. Para comprobarlo a mano:

```bash
jq -e 'to_entries | all(.value | has("description") and has("prompt") and has("tools")
       and (keys - ["description","prompt","tools","model"] | length == 0))' agents.json
```

`jq .` solo valida **sintaxis**, no el esquema del CLI. Un JSON perfectamente
válido puede seguir tumbando el lanzamiento.
