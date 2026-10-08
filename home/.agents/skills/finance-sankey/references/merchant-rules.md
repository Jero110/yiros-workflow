# Reglas de comercios aprendidas

Estas reglas fueron confirmadas por el usuario y tienen prioridad sobre inferencias genéricas cuando el descriptor coincide. Conserva siempre la descripción original para auditoría.

| Patrón del descriptor | Comercio normalizado | Categoría | Subcategoría | Confianza | Nota |
|---|---|---|---|---|---|
| `MERPAGO*ROCKSOLID`, `ROCKSOLID` o `ROCK SOLID` | Rock Solid | Deporte | Actividad deportiva | high | Cargo deportivo confirmado por el usuario. Mantener Deporte separado de Ocio. |
| `ARTZ PEDREGAL` sin otro comercio identificable | Artz Pedregal | Transporte | Estacionamiento | high | El usuario confirmó que estos cargos corresponden a estacionamiento del centro comercial. |

## Límites de las reglas

- Aplica las coincidencias sin distinguir mayúsculas y tolerando espacios repetidos.
- Si `ARTZ`, `ARTZ PEDREGAL` o `ROCK SOLID` aparecen acompañados por el nombre claro de otro comercio, clasifica según ese comercio; no fuerces la regla del recinto.
- No clasifiques cualquier cargo de un centro comercial como estacionamiento. La regla corresponde al descriptor genérico exacto `ARTZ PEDREGAL`.
- Si un estado nuevo aporta evidencia que contradice una regla, marca el movimiento para revisión en vez de ocultar la contradicción.
