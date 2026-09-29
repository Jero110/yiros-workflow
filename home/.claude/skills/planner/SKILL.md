---
name: planner
description: Use when a task splits into 2+ independent subtasks worth planning as a dispatched run — produces a written plan (project name, per-subtask contracts, model), then hands off to `executor`, which runs every subtask as a cmux pane worker in its own git worktree. Doesn't touch git or the Agent tool, and its only cmux actions are renaming its own tab/workspace and raising the executor's pane at hand-off.
---

# Planner

## Overview

Plan a multi-subtask run to completion on paper: independence check, per-subtask contract, and model. Every subtask runs as a cmux pane worker — that part isn't a decision (Step 3). Write it to a `.md` file. Stop.

**This skill never dispatches work.** It doesn't open a worktree, doesn't call the `Agent` tool, and never opens a worker pane — the only panes it ever touches are its own (rename) and the executor's (hand-off, Step 5). All actual dispatch is `executor`'s job, deliberately in a different skill — see "Why split from execution" below.

## Why split from execution

A plan that's fully written down is fully written down — nothing about re-reading it back costs less because the same session that wrote it is still open. What *does* cost tokens is a session carrying an entire brainstorm-or-grilling transcript into execution it doesn't need: the executor only ever needed the finished contract, never the back-and-forth that produced it.

This mirrors `superpowers:writing-plans` → `superpowers:executing-plans` in this same skill set: `writing-plans` is explicit that its output must contain zero placeholders and zero "similar to Task N" back-references, precisely *because* the plan is read by a session with no memory of how it was written. Same reasoning here, applied to dispatch contracts instead of implementation tasks. The DAG "Plan & Execute" pattern used across current multi-agent systems draws the same line: a Planner produces the full graph up front; an Executor consumes it and dispatches, without inheriting the Planner's reasoning trace.

**Concretely for you:** finish planning here, review the `.md`, and when you're ready to actually run it, either continue in this same session or open a brand new one — either way say "execute `<path>`" and invoke `executor`. Nothing is lost by waiting or by switching sessions; the contract is the interface.

## When NOT to Use (the whole run)

- Only one subtask → just do it.
- Every subtask is short, one-shot, and independent, AND nobody needs to watch it happen → skip the planning ceremony and just do the work directly; a full dispatch run isn't worth the setup.
- Subtasks share state or run in sequence → sequence the work, don't parallelize either way.

## Step 0: Setup — do this first, before asking anything

**Run this immediately on invoking the skill, in your very first turn**, before the brainstorm-vs-grilling question and before any exploration. It is two fast local socket calls; don't defer them until the plan is written.

```bash
cmux rename-tab "planner"
```

Two things this buys, both of which are worthless if done late:
- The user can see which pane is the planner **while** planning happens, not after.
- You confirm cmux is reachable up front. If this errors, you're not in a cmux workspace, and Step 5's hand-off dispatch won't work either — say so now rather than discovering it at hand-off.

This renames your own **tab** (the terminal, showing your role) — not the workspace (the sidebar folder, showing the project). Keep the two separate: the workspace gets the project name once Step 1 settles it (below), the tab keeps saying `planner` for as long as this session is planning.

**Verified quirk:** while the workspace has never been explicitly named (its sidebar title is still cmux's own default), renaming the *sole* tab in it also overwrites the workspace title as a side effect — the two stay linked until something renames the workspace directly. That's exactly the situation right after this Step 0 call, so don't be surprised if the sidebar briefly shows "planner" too; Step 1's `rename-workspace` fixes it for good the moment the project name is known, and after that the two stay independent (confirmed: once a workspace has an explicit name, further tab renames — even of its only pane — no longer touch it).

Loading the full `cmux` skill is **not** needed here — a rename creates no panes and dispatches nothing. Step 5 loads it, once, for the actual hand-off. Don't load it preemptively "in case"; that's the overhead this split exists to avoid.

## Step 1: Plan

Decide whether the task needs clarification:

- Small/local ticket → do a quick brainstorm yourself, at most 1-3 lightweight questions, then plan.
- Large/ambiguous/risky change → ask the user: **quick brainstorm or grilling?**
- If the user explicitly asks for grilling, use it.

- **Brainstorm** → use `planner-scoping`, not `superpowers:brainstorming` directly. It's a fork of that skill with the same questions → approaches → design → spec arc, but its terminal state hands back to *this* skill's Step 2 instead of `writing-plans`. Using the unforked `superpowers:brainstorming` here will walk its own hard gate straight into `writing-plans` — a single-session implementation plan, not a dispatch plan — silently swapping frameworks mid-run.
- **Grilling** → use the `grilling` skill directly; it has no terminal-state gate of its own, so it's safe to use unforked. It asks one interactive question at a time, each with a recommended answer; look facts up yourself instead of asking. **External dependency** — not bundled with this skill. If `Skill(grilling)` errors with "Unknown skill", install it: `npx skills@latest add mattpocock/skills --skill=grill-me` (this pulls the whole mattpocock/skills repo; keep `grilling`, the other 36 skills it installs are unrelated to this framework and safe to delete).

Either sub-skill ends in a spec (or, for grilling, a settled design tree) handed back to *this* skill's Step 2 — not to `writing-plans`, not to any implementation skill. The subtask contracts in Step 4 are `planner`'s own spec-equivalent for dispatch purposes.

Planning produces a short **project name** (e.g. `auth-refactor`). Every worker `executor` later dispatches is named `<project>-<worker>`. That naming is the whole usage-tracking story — see `framework-retro`.

The project name is settled here; now name the **workspace** after the project (the sidebar folder, shared by planner and — later — executor):
```bash
cmux rename-workspace "<project>"
```
The tab stays `planner` (Step 0) — don't fold the project name into the tab too; the tab's job is to say *which role* is running, the workspace's job is to say *which project*.

## Step 2: Independence check

**REQUIRED:** apply `superpowers:dispatching-parallel-agents`'s gate. Are the subtasks genuinely independent — no shared state, no sequential dependency? If not, do not parallelize.

**Shared foundation is not a reason to skip parallelizing — it's a reason to sequence one step in front of it.** A common real shape: several feature slices are independent from *each other*, but all of them sit on top of the same models/config/auth that doesn't yet exist. That foundation is not itself a subtask worth a worker — it's small, mechanical, and every worker would otherwise invent its own incompatible version, guaranteeing a merge conflict in exactly the file everyone touches.

When you hit this shape: note in the plan that the shared foundation must be built first, directly, in the primary checkout, before any worker is dispatched — models, schemas, config, whatever every slice needs to import. This is a note for whoever runs `executor` (possibly you, possibly a fresh session), not something this skill does itself. Say so explicitly in the plan so it's a documented decision, not a silent scope grab discovered mid-run.

## Step 3: Mechanism — always `pane`

**There is one mechanism: `pane`.** Every subtask is a cmux pane worker in its own git worktree. This is not a decision to make per subtask — there is nothing to weigh, because native subagents are not part of this framework.

Why the choice was removed: a subagent's work is invisible until it reports back, it can't be messaged by another worker, and it shares the primary checkout with no worktree of its own. Live visibility and worktree isolation *are* the framework. A run dispatched as subagents is not a cheaper version of this framework — it's a different thing that happens to produce files, in one shared checkout, where the user can't see any of it.

**Size, simplicity and speed are irrelevant here.** "This one's too trivial to deserve a pane" is the exact reasoning that once turned a whole run into invisible background agents. Three one-function files with tests are three pane workers.

So: write `Mechanism: pane` in every contract. If a subtask seems too small to deserve its own pane, that's a signal it should be **merged into an adjacent subtask**, not demoted to a subagent — fold it in and write one pane worker for the combined work.

**This is still a plan, not an action.** Planner never opens a pane and never calls `Agent`; it writes the contracts and `executor` dispatches them.

## Step 4: Write a task contract per subtask

Four parts, nothing else:

```
Objective:      what must be true when done
Constraints:    what must not change
Validation:     the exact command that proves it
Stop condition: when to stop working
```

Plus **`Mechanism: pane`** (always — Step 3), **`Harness`** (`claude-code`, `pi`, `codex`, `openai`, or `auto`), and a **model**, chosen per `harnesses` + `superpowers:subagent-driven-development`'s Model Selection:

| Task shape | Model |
|---|---|
| Mechanical, isolated, 1-2 files, plan contains the code | cheapest tier |
| Integration, multi-file, debugging, prose-described work | standard / mid tier |
| Architecture, judgment | most capable |

**Always specify the harness and model explicitly.** Omitting them inherits whatever session runs `executor` — usually the most expensive tier. Use `Harness: auto` only when executor should deliberately decide at dispatch time based on cost/capability/availability. For old Claude-only behavior, write `Harness: claude-code`.

Write every contract as if the reader has never seen this conversation — because by the time `executor` reads it, it hasn't. No "similar to the login worker's setup," no "as discussed above." Spell it out, every time, same discipline as `writing-plans`'s "No Placeholders."

If one subtask's brief plausibly needs a small answer from another subtask's worker (a name it picked, a shape it chose), say so explicitly in the contract — "ask `<project>-<other-worker>` for the name it used for X" — since at planning time no pane exists yet to reference by surface ID. `executor` resolves the actual surface ref at dispatch time.

## Step 5: Write the plan file

Save to `docs/planner/plans/YYYY-MM-DD-<project>.md` (user preference for plan location overrides this default). Keep the plan lean and fixed-structure: human decisions at the top, agent contracts below. Do not include global workflow policy, model-routing theory, or long reasoning traces.

Structure:

```markdown
# <Project Name> — Planner Plan

**Project name:** <project>
**Planned:** YYYY-MM-DD

## Goal
<the user-approved outcome>

## User decisions / hard constraints
- <things the user explicitly asked for; executor must not override>

## Planner assumptions / flexible approach
- <LLM-proposed approach; executor may change this to achieve the goal>

## Scope
In:
- ...

Out:
- ...

## Revisión humana / Human approval checklist
- <the stable section the user reads before execution>

## Shared foundation (if any)
<what must be built first, in the primary checkout, before dispatch>

## Review guidance
- <task/area>: validation-only | fast_ai | deep_ai | human

## Subtask: <name>

**Mechanism:** pane
**Harness:** claude-code | pi | codex | openai | auto
**Model:** <tier or harness-specific model>
**Review stack:** validation-only | fast_ai | deep_ai | human

Objective:      ...
Constraints:    ...
Validation:     ...
Stop condition: ...

Cross-refs: <any "ask worker X for Y" notes>

---

(repeat per subtask)
```

Review guidance follows the tree model: leaf changes can be validation-only or fast_ai; trunk changes (auth, permissions, security, data model, migrations, billing, critical integrations, public APIs, central state, infra/deploy, large cross-cutting refactors, leakage/exposure risk) require deep_ai and usually human.

Then stop. Ask the user, don't just declare the next step:

> Plan written to `<path>`. Confirm this plan to proceed — say the word and I'll open the executor to dispatch it.

Wait for an explicit confirmation before treating the plan as ready to execute, even in the same session. Do not invoke `executor` yourself off an ambiguous or absent reply.

Once confirmed, raise the executor in its own pane rather than folding execution into this session — this keeps the planning transcript out of executor's context per "Why split from execution" above. **Load the `cmux` skill now, just for this one dispatch** (`Skill(cmux)`) and load `harnesses` if the user wants the executor itself to run under Pi/Codex/Astra instead of Claude Code. You're about to run a real `new-pane` + health-check + `send` sequence, and this is the one place in this skill's job that isn't the rename-only exception above:
```bash
# default Claude Code executor
cmux new-pane --direction right --focus false \
  --command "cd <repo-root> && cc <project>-executor --model <executor-model>"

# alternative executor harness, using harnesses' launch table
cmux new-pane --direction right --focus false \
  --command "cd <repo-root> && <executor harness launch command>"
# -> prints: OK surface:<N> pane:<N> workspace:<N>   — keep that surface ref
```
Then verify it actually started (`cmux surface-health`, `cmux read-screen --surface <surface> --lines 20` for the `cc`/Claude Code banner) before sending it anything. **If `read-screen` shows a "Do you trust this folder?" prompt instead of a banner**, send `down` then `enter` to accept, and re-read before continuing — a brief sent into that prompt is swallowed. This shouldn't happen when the executor starts in the repo root (trust is inherited from the parent directory). If the repo root itself isn't trusted yet, pre-accept it once instead of clicking through:
```bash
~/.claude/skills/executor/scripts/pretrust.sh <repo-root>
```
No CLI flag skips that dialog — verified that `--dangerously-skip-permissions` and `--permission-mode bypassPermissions` both still hit it.

Name the executor's tab before handing it the plan, so `cmux tree` is self-describing from the start. The executor is a new pane in this same workspace (`new-pane` above), not a workspace of its own — the workspace already carries the project name from Step 1, so this must rename the **tab**, not the workspace:
```bash
cmux rename-tab --surface <surface> "executor"
cmux send --surface <surface> "Run the executor skill on docs/planner/plans/<file>.md"
cmux send-key --surface <surface> enter
```
This is the same launch pattern `executor` itself uses for workers — reuse it rather than reinventing a different one here. If the user says to just continue in this same session instead of opening a pane, that's fine too — invoke `executor` here directly, no cmux dispatch needed.

**Everything else stays off-limits:** no worktrees, no calling `Agent`, no touching a worker's pane — that's still entirely `executor`'s job. This skill's only cmux actions, ever, are the self-rename above and this one hand-off dispatch. If the user asks you to execute right now instead of just raising the executor pane, that's a request to switch skills — invoke `executor` with the plan's path yourself, in this session, rather than opening a pane for it.

## Autonomy rule

Decide routine things yourself: subtask boundaries, model tier, mechanism recommendation, contract wording. Do not ask permission for these.

The only genuine stop-and-ask in this skill is Step 1's brainstorm-vs-grilling choice — everything past that is yours to decide and write down.

## Red Flags

- Creating a worktree, opening a worker pane, or calling `Agent` from inside this skill → that's `executor`'s job; you've mixed the phases back together. (Renaming your own pane and raising the executor's pane at hand-off are the only exceptions — see Step 1 and Step 5.)
- A contract that references "the discussion above" or "like the other worker" → the reader of this plan has no access to this conversation.
- Skipping Step 2's independence check because subtasks "seem" independent → apply the gate explicitly, every time.
- Writing `subagent` as a mechanism, or reasoning about whether a subtask "deserves" a pane → there is one mechanism (`pane`); a subtask too small for its own pane gets merged into another, not demoted.
