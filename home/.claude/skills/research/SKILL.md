---
name: research
description: Monta y lanza investigacion autonoma continua - orquestador Opus delgado que despacha subagentes e indexa todo en un vault Obsidian. Usar para investigar un tema, explorar un espacio de problemas, o buscar y verificar fuentes de datos.
trigger: /research
---

# /research — investigacion autonoma continua

El usuario escribe `/research` y **nada mas**. Tu montas todo y te pones a
trabajar en esta misma sesion. No le pidas que corra comandos en su shell.

**Llama a:** `/wikilm` (estructura del vault).

## Arquitectura

> **Separar quien decide de quien lee.**

```
         ORQUESTADOR (tu, contexto CHICO)
                     │  despacha 3-5 en paralelo
     ┌───────────┬───┴───┬───────────┐
  agente      agente   agente     agente     ← queman contexto y mueren
     └───────────┴───────┴───────────┘
                     │  devuelven ≤10 lineas
                     ▼
                  vault/   ← la memoria real
```

Tu **nunca** investigas. Tu contexto se mantiene chico a proposito, y por eso la
corrida dura horas sin degradarse. El conocimiento vive en disco, no en tu
ventana.

## Paso 1 — Preguntar

Interroga al usuario hasta llegar a un entendimiento compartido antes de montar
nada. Trabaja en **rondas**: la frontera es cada pregunta cuyos prerequisitos ya
estan resueltos — lo que puedes preguntar *ahora* sin adivinar respuestas que
aun no tienes. Pregunta toda la frontera junta, numerada, con tu recomendacion:

```
**Q1** - **<titulo>**: <cuerpo, puede tener opciones>

Recomendacion: <tu respuesta recomendada>

---

**Q2** - **<titulo>**: <cuerpo>

Recomendacion: <tu respuesta recomendada>
```

Usa `AskUserQuestion` cuando las opciones sean discretas; texto libre cuando no.
Cada ronda que el usuario responde reacomoda el arbol: lo resuelto empuja la
frontera y desbloquea preguntas que dependian de eso. Recalcula la frontera y
lanza la siguiente ronda. Una pregunta cuya respuesta depende de otra que sigue
abierta en esta ronda pertenece a una ronda **posterior**, no a esta.

Los hechos los averiguas tu, nunca el usuario: si una pregunta de la frontera
necesita un dato del entorno (filesystem, red, un archivo previo), despacha un
subagente a buscarlo en vez de preguntarselo. No bloquees el resto de la
frontera por eso — solo las preguntas que dependen de ese dato esperan.

Preguntas minimas que casi siempre aplican (no son las unicas, son el piso):

1. **Goal** — que debe lograr, no que tema. *"Investigar movilidad"* es un tema.
   *"Encontrar 15 preguntas de tesis viables con datos descargables"* es un goal.
   Si dan un tema, insiste una vez.
2. **Profundidad** — explorar amplio o profundizar en pocas lineas.
3. **Datos** — solo probar que responden, o tambien bajar muestras.
4. **Material de partida** — PDFs, links, notas previas. Leelos antes de montar.

La ronda termina cuando la frontera queda vacia: cada rama del arbol visitada,
nada asumido en silencio. No montes nada hasta que el usuario confirme que
llegaron a un entendimiento compartido. Si el usuario ya dio todo esto en su
mensaje inicial de forma inequivoca, no repreguntes lo ya resuelto.

## Paso 2 — Montar el andamiaje

Invoca `/wikilm` para las convenciones. Crea **solo** esto:

```
<proyecto>/
├── vault/
│   ├── 00-INDEX/{INDEX.md, ARBOL.md}
│   ├── 90-Meta/{CONVENCIONES.md, GOAL.md, FUENTES-DISPONIBLES.md}
│   └── <categorias inferidas del goal>/
├── data/raw/           (si el goal implica datos)
├── scripts/{ORCHESTRATOR_PROMPT.md, agents.json}
└── logs/
```

Los MOC **no** se crean por adelantado. Se crean cuando hay notas que poner
dentro. Un MOC vacio es ruido.

## Paso 3 — Probar la red ANTES de arrancar

Esto es lo que evita que los agentes inventen citas. Corre
`referencias/probar-fuentes.sh`, que escribe `FUENTES-DISPONIBLES.md`.

Verificado en esta maquina: **Crossref, arXiv, DOAJ y PubMed pasan; OpenAlex y
Unpaywall dan 403** (proxy corporativo Zscaler). Con Crossref + arXiv alcanza.

**No evadas el proxy.** Es un control de seguridad de la empresa; saltarlo desde
una maquina del trabajo puede costar caro y no hace falta.

## Paso 4 — Trabajar (aqui mismo, en esta sesion)

No lances nada en el shell del usuario. **Tu eres el orquestador.** Lee
`scripts/ORCHESTRATOR_PROMPT.md` y ejecuta ese bucle en esta conversacion:

1. Leer `INDEX.md` y `ARBOL.md`.
2. Decidir 3-5 encargos independientes.
3. Despacharlos **en paralelo, en una sola respuesta**, con la tool `Agent`.
4. Recibir resumenes cortos (≤10 lineas).
5. Actualizar `INDEX.md`, `ARBOL.md` e `IDEAS.md`.
6. Volver a 1.

Si el corte de usage de Claude Code interrumpe la sesion, el propio harness la
retoma solo cuando el usage se reinicia (ajuste nativo del CLI). No hace falta
ninguna guardia ni script propio para eso: al reanudar, relee `GOAL.md` e
`INDEX.md` antes de seguir despachando.

## Reglas que hacen que funcione

1. **Prohibido WebSearch/WebFetch para ti.** Si no lo prohibes, lo haces, y tu
   contexto explota.
2. **Contrato de retorno literal** en cada subagente: archivos + ≤3 hallazgos +
   pendientes. Nunca contenido.
3. **Paralelo siempre**, 3-5 por ciclo. Uno a la vez desperdicia todo.
4. **Verificado ≠ leido.**
5. **1 de cada 5 encargos abre territorio nuevo.** Sin esto, converge.
6. **Toda cita con DOI/URL verificado** o marcada `sin-verificar`.
7. **Probar datos, no descargarlos.** `head -5`, API con `limit=1`, o DuckDB
   leyendo remoto. Un CSV de 200MB en contexto no aporta nada que un head no de.

## Paso 5 — Auditar

No puedes juzgarte a ti misma: crees que vas bien porque produces archivos. Las
metricas que delatan se ven desde fuera. `referencias/auditar.sh` imprime el
bloque para revisar en sesion aparte:

| Senal | Que significa |
|---|---|
| Casi todo `sin-verificar` | Lee *sobre* las cosas sin comprobarlas |
| `data/raw/` vacio y cero URLs probadas | Puro humo: no hay trabajo real |
| Notas sin `summary` | El vault dejo de comprimir |
| Ideas todas iguales | Convergencia prematura |
| Citas sin DOI validado | **Riesgo de invencion** |

## Errores conocidos

- **Orquestador que se vuelve investigador** — el mas comun. Se corrige
  recordandole la regla: delega, no leas.
- **Subagentes que devuelven ensayos** — el contrato no era literal.
- **Lanzar `claude` anidado como tool Bash** — el clasificador de permisos lo
  bloquea (`Create Unsafe Agents`). No lo intentes: monta y trabaja aqui.
- **Citas inventadas** — no se verifico contra Crossref/arXiv.
