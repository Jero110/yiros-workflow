# Global Codex Instructions

## Entorno: cmux + otros agentes

Trabajo siempre desde cmux cuando la tarea involucre otros agentes o harnesses.

- Para invocar, coordinarte con, o hacer handoff a otro agente/harness (Pi, Claude Code, Codex), sigue `~/.agents/shared/cross-harness-workflow.md`.
- No tomes control de un pane ajeno ni mandes input a otro agente sin petición explícita del usuario.
- Todo handoff por cmux requiere `cmux send --surface ... "..."` seguido de `cmux send-key --surface ... enter`; `send` solo escribe texto y no cuenta como turno entregado.
- Para briefs largos, escribe un archivo y manda solo la ruta.
- Pide siempre `ACK <task-id>` antes de marcar el worker como despachado.
