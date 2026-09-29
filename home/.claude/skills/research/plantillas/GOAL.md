---
tipo: meta
titulo: GOAL — objetivo de esta corrida de research
summary: El objetivo concreto que la corrida debe cumplir, con sus criterios de exito y restricciones.
tags: [meta, goal]
---

# GOAL

> **El orquestador relee este archivo al arrancar y tras cada interrupción.**
> Es lo que sustituye a un comando `/goal` (que no existe en Claude Code):
> un archivo persiste mejor que un comando, porque sobrevive a los reinicios
> de sesión (incluida la reanudación nativa del CLI tras un corte de usage).

## Objetivo

{{GOAL}}

<!-- Un goal, no un tema.
     Tema:  "investigar movilidad urbana"
     Goal:  "encontrar 15 preguntas de tesis viables, cada una con datos
             descargables y verificados, para elegir una"                -->

## Criterios de éxito

La corrida cumple su goal cuando:

- {{CRITERIO_1}}
- {{CRITERIO_2}}
- {{CRITERIO_3}}

## Restricciones

- {{RESTRICCION_1}}

## Fuera de alcance

Lo que **no** hay que investigar, para no dispersarse:

- {{FUERA_1}}

## Modo

`{{MODO}}`  <!-- sustained: no para hasta que lo paren a mano
                  focused:   para al cumplir el goal o N ciclos -->

## Notas del usuario

<!-- Contexto, preferencias, corazonadas, líneas que le interesan.
     El orquestador las tiene en cuenta al decidir dónde profundizar. -->

{{NOTAS}}
