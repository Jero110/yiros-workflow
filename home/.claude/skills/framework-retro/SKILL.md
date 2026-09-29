---
name: framework-retro
description: Use when the user asks, after an executor run has finished, where the tokens went, how efficient the run was, or what should change about how workers and reviewers behave
---

# Framework Retro

## Overview

Look back at a finished executor run, work out what it actually cost and where it went wrong, and **propose** a concrete edit to a role's `SKILL.md`.

**Core principle: you propose, the user approves.** This skill never edits a `SKILL.md` itself. A retro that rewrites the framework on its own is a self-healing loop, and that is exactly the always-on supervision overhead the executor design deliberately cut.

## When to Use

- The user asks how a run went, what it cost, or why it was slow.
- The user says a worker or reviewer behaved wrong and wants it fixed for next time.
- **Only after a run.** Never mid-run, never automatically.

## When NOT to Use

- A run is still going → you would be inventing supervision that doesn't exist.
- The user wants a bug fixed in *this* run's output → that is the executor's retry path.
- Nothing actually went wrong and the user didn't ask → there is no retro to run.

## Step 1: Gather the run

Start from the project name. Every worker in a run is named `<project>-<worker>`, which is the entire tracking mechanism — there is no run-id system.

```bash
cc ls | grep <project>          # every worker that ran under this project
```

Then read the ledger the executor wrote — `progress.md` at the run's workspace path. It gives you dispatch/notify/done/retried lines with timestamps, models, and surfaces.

Ask the user for anything else worth reading (a specific pane's scrollback, a diff), rather than guessing at it.

## Step 2: Get the real cost per worker

```bash
cc usage <worker-name>          # per worker, from cc ls
```

Output looks like:

```
auth-refactor-login  (0af65140)
  model      claude-sonnet-5
  turns       859
  input           1.7K
  output        341.6K
  cache write     1.7M
  cache read    182.0M
```

**Never sum these four into one number, and never compare two workers by a total.** Cache-read routinely runs 100–500× output on a long session — the example above is 341.6K output against 182.0M cache read. A summed figure is dominated by cache traffic and tells you nothing about what the work cost. This is the same misreading that made cmux panes look expensive against native subagents when they were roughly a wash.

Compare **like against like**:

| Signal | Read it as |
|---|---|
| High `output`, few `turns` | Real work, efficiently done. |
| High `turns`, low `output` | Thrashing — the brief was probably underspecified. |
| High `cache write` | Large context re-established repeatedly. |
| High `cache read` alone | Normal for a long session. Not waste by itself. |
| Expensive model, mechanical task | Model selection was wrong. |

## Step 3: Find the pattern, not the incident

One worker having a bad run is not a framework problem. Look for something that will **recur**:

- Several workers needed the same missing context → the brief template is short a field.
- A reviewer passed something that broke later → the review contract missed a category.
- Workers routinely took an expensive model for mechanical work → the model-selection guidance isn't binding.
- A worker reported `DONE` without evidence → the report contract isn't being enforced.

If you cannot name the recurrence, **say so and stop.** "This run was fine, one worker got unlucky" is a valid retro outcome.

## Step 4: Propose the diff

Name exactly one role — `worker`, `reviewer`, `planner`, or `executor` — and show the concrete change:

```
File:     ~/.claude/skills/worker/SKILL.md
Evidence: auth-refactor-login and auth-refactor-logout both sent NEEDS_CONTEXT
          asking which test command to use (progress.md 14:38, 14:41).
Change:   add a REQUIRED "Validation" line to the report template.

  - Report: status + one-line summary
  + Report: status + one-line summary + the validation command you ran

Why:      both workers had the command in their brief and still asked,
          so the failure is that the report never made them state it.
```

Every proposal carries **evidence from this run** — a ledger line, a `cc usage` figure, a quoted report. A proposal without evidence is a guess, and guesses accumulate into skill bloat.

Match the fix to the failure (per `superpowers:writing-skills`):

| Failure | Right form |
|---|---|
| Skipped a rule it knew | Prohibition + rationalization table |
| Output was the wrong shape | Positive recipe — state what the output IS |
| Omitted a required element | A REQUIRED slot in the template |
| Should depend on a condition | Conditional on an observable predicate |

## Step 5: Hand it over

Present the proposal and stop. The user approves, edits, or rejects it exactly like any other code change.

If they approve, apply it — and note that the changed skill is now untested. For `worker` and `reviewer`, changes to their contracts warrant re-running a baseline scenario per `superpowers:writing-skills`; those two are dispatched into fresh contexts where nobody can correct them live.

## Red Flags

- Editing a `SKILL.md` because the fix is "obvious" → propose it. Always.
- One total token number per worker → cache-read swamped it. Split the four.
- A proposal with no ledger line or usage figure behind it → that's a guess.
- Proposing changes to three roles at once → you found an incident, not a pattern.
- Running this while workers are still live → wrong tool, wrong time.
