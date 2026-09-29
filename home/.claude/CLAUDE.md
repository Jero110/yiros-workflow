# Global Claude Code Instructions

## Entorno Python

Usar `uv` con un entorno por proyecto, nunca un entorno global compartido:

```bash
uv init                    # al arrancar un proyecto nuevo
uv add <paquete>           # instalar dependencias
uv run python3 <script.py> # ejecutar scripts
```

Nunca usar `pip install`, `python`/`python3` directo, ni `conda`.

## Entorno: cmux + otros agentes

Trabajo siempre desde **cmux**. En paralelo pueden estar corriendo otros
agentes (Pi, Claude Code, Codex) en distintos panes del mismo cmux, no
sesiones aisladas.

- Si me piden invocar, coordinarse con, o hacer handoff a otro
  agente/harness (Pi, Codex, otra sesión Claude), cargar la skill
  `harnesses` para decidir routing/modelo, y la skill `cmux` para la
  ejecución real (abrir pane, mandar el brief, leer su pantalla/output).
  Estas dos van juntas: no usar una sin la otra para este caso. Seguir también
  `~/.agents/shared/cross-harness-workflow.md`.
- Si solo se necesita ver qué está haciendo otro agente ya corriendo (no
  lanzarlo), usar `cmux` directamente (`cmux tree`, `cmux sessions --agent
  claude --json`, `cmux read-screen`) en vez de inspeccionar procesos a
  mano con `ps`/`lsof`.
- No tomar control de un pane ajeno ni mandar input a otro agente sin que
  el usuario lo pida explícitamente.
- Todo handoff por cmux requiere `cmux send --surface ... "..."` seguido de
  `cmux send-key --surface ... enter`; `send` solo escribe texto y no cuenta
  como turno entregado. Para briefs largos, escribir un archivo y mandar solo la
  ruta. Pedir siempre `ACK <task-id>` antes de marcar el worker como despachado.

## Búsqueda web

Para cualquier búsqueda web, usar Exa MCP (`web_search_exa` / `web_fetch_exa`) por defecto.
Si los créditos de Exa se acaban (error 429 o similar), usar la búsqueda web normal (WebSearch/WebFetch) como respaldo.
