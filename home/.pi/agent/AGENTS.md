# Global Pi Instructions

## Estilo de respuesta

- No uses emojis en respuestas, reportes, verdicts, notifications ni formatos de skills, salvo que el usuario los pida explícitamente.
- Mantén el workflow lean: añade herramientas útiles y accionables, no instrucciones largas por añadir instrucciones.

## Entorno: cmux + otros agentes

Trabajo siempre desde **cmux**. En paralelo pueden estar corriendo otros
agentes (Claude Code, Pi, Codex) en distintos panes del mismo cmux, no
sesiones aisladas.

- Por defecto, cada workflow opera exclusivamente en el `CMUX_WORKSPACE_ID` del
  caller. Eventos, panes, sesiones, notificaciones y watchers se filtran a ese
  workspace; nunca actuar sobre otros workspaces salvo petición explícita.
  Antes de hacer watch/send/handoff, comprobar que la surface sigue perteneciendo
  a ese workspace. No usar el workspace visualmente enfocado como referencia.
- Si te pido invocar, coordinarte con, o hacer handoff a otro agente/harness
  (Claude Code, Codex, otro Pi), carga la skill `harnesses` para decidir
  routing/modelo, y la skill `cmux` para la ejecución real (abrir pane,
  mandar el brief, leer su pantalla/output). Estas dos van juntas: no uses
  una sin la otra para este caso. Sigue también
  `~/.agents/shared/cross-harness-workflow.md`.
- Si solo necesitas ver qué está haciendo otro agente ya corriendo (no
  lanzarlo), usa `cmux` directamente (`cmux tree`, `cmux sessions --agent
  claude --json`, `cmux read-screen`) en vez de inspeccionar procesos a
  mano con `ps`/`lsof`.
- No tomes control de un pane ajeno ni mandes input a otro agente sin que
  yo lo pida explícitamente.
- Todo handoff por cmux requiere `cmux send --surface ... "..."` seguido de
  `cmux send-key --surface ... enter`; `send` solo escribe texto y no cuenta
  como turno entregado. Para briefs largos, escribe un archivo y manda solo la
  ruta. Pide siempre `ACK <task-id>` antes de marcar el worker como despachado.
- Cuando tu rol de workflow quede claro (planner, executor, worker, reviewer),
  renombra tu propia tab una vez: `planner`, `executor`, `worker-<tarea>` o
  `reviewer-<tarea>`. En Pi puedes usar `/workflow role <rol-tarea>`; en otro
  harness, `cmux rename-tab --surface <tu propia surface> "<rol-tarea>"`.
  Nunca renombres el workspace por este motivo ni una tab ajena. No adivines
  el rol por el modelo o por el nombre genérico de la terminal.

## Búsqueda web

Para cualquier búsqueda web, usar Exa MCP (`web_search_exa` / `web_fetch_exa`) por defecto.
Si los créditos de Exa se acaban (error 429 o similar), usar la búsqueda web normal como respaldo.
