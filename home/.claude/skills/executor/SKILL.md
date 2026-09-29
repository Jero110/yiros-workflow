---
name: executor
description: Use when you have a written planner plan (a .md with project name, per-subtask contracts, and model) and need to actually run it — dispatching each subtask as an isolated Claude Code worker in its own cmux pane and git worktree, supervising them to a reviewed result. Takes the plan's path; do not use this skill to write a plan, use `planner` for that.
---

# Executor

## Overview

Read a `planner`-produced plan, dispatch each subtask as a Claude Code worker in its own cmux pane and git worktree, supervise to completion, review, and hand the user something mergeable.

**This skill never plans.** It doesn't decide independence, doesn't write contracts, doesn't pick a project name. All of that already happened in `planner` and is sitting in the `.md` you were handed. If no plan file exists yet, stop and say so — invoke `planner` first, don't improvise contracts inline.

**Autonomy inside the approved plan.** Do not interrupt for routine implementation decisions: decide, act, and record material assumptions. The plan's Goal, User decisions/hard constraints, Scope, and Validation are binding. Planner assumptions and approach are flexible. If continuing requires credentials/login, a product decision, violating a user constraint, or expanding scope, ask the user one concise question after advancing other unblocked work. If several approaches or sessions produce no meaningful progress, stop looping and escalate with evidence. Do not silently declare success on a blocker.

**Core principle:** the communication channel between Claudes is thin — worktree + pane + event stream. No supervision engine sits on top of it. You don't watch workers; you block on `cmux events` and it wakes you with the surface that needs you (Step 3).

**Why cmux panes and never native subagents:** a subagent's report lands in your context whether you want it or not, and its work is invisible to the user until it reports back. A worker in a pane is watchable live, can be messaged mid-task, and keeps its context for a follow-up fix. Subagents also share the primary checkout — no worktree of their own — so nothing stops two of them from editing the same file at once. That's why this framework has exactly one dispatch mechanism (Step 1).

**Always load the `cmux` skill first, unconditionally, before Step 0.** This skill's whole job is dispatching and supervising panes — creating them, checking other sessions' state, sending messages between workers — so it needs full command knowledge of cmux (new-pane, **new-split**, tree, **events**, read-screen, notifications, send/send-key, set-buffer/paste-buffer) loaded up front, not fetched on demand mid-dispatch. Note that this skill's Step 1 and Step 3 override the `cmux` skill where they differ: `new-split` for worker stacking, and the event stream — not notification polling — as the supervision loop. Every run dispatches panes, so there is no run that doesn't need it.

**Also load the `harnesses` skill before dispatch.** Plans may specify `Harness: claude-code | pi | codex | astra | auto` in addition to `Model`. Use `harnesses` to choose and launch the right terminal agent while preserving this executor's cmux/worktree layout. Older plans without `Harness` default to `claude-code`.

## Layout

Fixed geometry, not ad hoc splits — so a glance at the screen tells you what's what without reading titles:

```
┌───────────┬───────────────┐
│           │   worker A    │
│ executor  ├───────────────┤
│  (left)   │   worker B    │
│           ├───────────────┤
│           │   worker C    │
├───────────┤               │
│ reviewer  │   worker D    │
│ (if any)  │               │
└───────────┴───────────────┘
```

- **executor's own pane stays leftmost**, fixed, for the whole run. The left column is executor's alone — nothing else goes there except a reviewer *below* it (see below). If a worker ever lands in the left column, the layout is broken; fix it before dispatching further.
- **Workers stack to its right, split vertically** — one pane per active worker, top to bottom in dispatch order, **all at equal height**. The shape is n×2: one tall executor on the left, n workers evenly stacked on the right. Achieving this is mechanical and exact — `new-split down --surface <previous worker>` per worker, then `workspace.equalize_splits` once. Step 1.8 has the commands and the verification; both matter, because the wrong command produces a plausible-looking but wrong grid.
- **A reviewer (or any other single right-hand-of-executor helper — a test runner, a one-off investigation) goes below executor's own pane**, left column, not mixed into the worker stack. One at a time — see Step 4.
- **Hard cap: 7 panes open at once, total** (executor + reviewer, if any + every live worker). This is tighter than the 2-4 worker dispatch cap below by design — the dispatch cap limits *review-worthy* concurrent work, this cap limits *screen* clutter, and the two multiply, not add: executor (1) + reviewer (1) + up to 4-5 live workers stays inside it. If a plan has more subtasks than fit, the extras queue — see Step 1.
- **Close panes the moment they stop earning their spot** — a worker once its review passes (Step 4), a reviewer once its verdict lands, a test/browser tab once you've read what you needed from it. Don't batch closes for later; an idle pane past its purpose is clutter, not a record — the ledger is the record.
- **Dev servers, localhost previews, and anything you're testing against open as tabs**, not as additional split panes — they're not workers and don't belong in the worker stack. `cmux new-pane --type browser --url http://localhost:3000` opens as its own tab; don't `--direction` it into the split layout.
- **Web searches / browser research open as tabs**, same reasoning — research is not a worker and doesn't compete for the fixed split geometry.
- **Rename every pane you open so `cmux tree` is self-describing without opening it, and keep tab vs workspace straight**: the workspace (sidebar folder) already carries the project name — `planner` set it, or you set it in Step 0.5 if this run started here — and nothing after that should rename the workspace again. Every pane from here on, including your own, gets its **tab** renamed instead (`rename-tab --surface`, or bare `rename-tab` for your own): yourself to `executor` (Step 0.5), each worker to `<worker>` right after confirming its banner (Step 1.9), the reviewer to `reviewer` when opened (Step 4). Tabs say *role*; the workspace says *project* — never mix the project name into a tab or the role into the workspace name.

## Step 0: Load the plan, take over from planner

0. Load the `cmux` skill (`Skill(cmux)`) before anything else in this list — see above.
1. Read the plan file (path given by the user, or the most recent under `docs/planner/plans/`).
2. Confirm it has the shape `planner` produces: project name, per-subtask contracts with Objective/Constraints/Validation/Stop condition, and a model. If a field is missing or ambiguous, don't stop and don't ask — fill it with the most reasonable default (e.g. model → the plan's global model or Sonnet; missing Validation → the repo's test suite plus the Objective's own check; missing Stop condition → Validation passes), record each one as `ASSUMED:` in the ledger, and flag it in the final report as a planning gap for `planner`. The only case where you can't proceed is no plan file at all — then say so and end. (A `Mechanism` line is optional and always means `pane` — see Step 1.)
3. **If a shared foundation is noted in the plan**, build it yourself first, directly in the primary checkout — commit it — before dispatching anything. Then proceed.
4. **Always check this workspace for a live planner pane and close it if found** — the plan file is self-sufficient once written, and the planning session isn't needed again regardless of whether this is the same conversation:
   ```bash
   cmux tree
   ```
   Look for a surface still running the planning session (its pane title or recent output will show planner's work — the plan-writing, the "Plan written to `<path>`" message). If found, close it:
   ```bash
   cmux close-surface --surface <planner's surface>
   ```
   Skip this only if `cmux tree` shows no such pane (e.g., planning happened outside cmux entirely, or it was already closed).
5. Rename your own **tab** to identify your role — the workspace (sidebar folder) should already carry the project name from `planner`'s Step 1, so don't rename it again here:
   ```bash
   cmux rename-tab "executor"
   ```
   **Exception:** if you were invoked standalone, with no `planner` run in this workspace (`cmux tree` in step 4 above found nothing to close and the workspace still has its default name), name the workspace after the project too, since nobody else did:
   ```bash
   cmux rename-workspace "<project>"
   ```

## Step 1: Dispatch — pane workers in worktrees

**Every subtask is a cmux pane worker in its own git worktree. There is no other path.** Do not call the `Agent` tool to dispatch a subtask, whatever the plan's `Mechanism` field says — if an older plan says `subagent`, treat it as `pane` and note the correction in the ledger.

This is not a preference to weigh per subtask. A subagent runs invisibly, can't be messaged by another worker, and shares the primary checkout with every other subagent — which is precisely the collision worktrees exist to prevent. It has really gone wrong: a plan marked three code-writing subtasks as `subagent`, and the run dispatched three invisible agents into one checkout while the user was watching an empty screen waiting for panes.

**"These subtasks are small, so panes are overkill" is the failure mode, not an optimization.** Size never makes a subtask ineligible for a pane. Neither does simplicity, speed, or the run being short.

You may still use the `Agent` tool for **your own** research while supervising — a lookup, a search across the repo — the way any session would. That is not dispatching a subtask, and it never replaces a worker.

Concurrency cap: **2–4 pane workers at once**, regardless of how many subtasks exist. Extra subtasks queue. Choose the exact number adaptively: use 2 when quota is tight, tasks are risky, or reviews will be hard; use 3 as the normal default; use 4 only when tasks are independent, tests are cheap, and at least one harness/account pool has comfortable quota. Do not "spam" a single provider just because it is the default harness.

**The cap exists because review, not dispatch, is the actual bottleneck.** More parallel workers than you (or the user) can meaningfully review just produces a review backlog and under-reviewed merges — the failure mode observed across current multi-agent coding practice, not a theoretical concern. 3-5 concurrent is the reported sweet spot; treat pushing past 4 as a decision to make deliberately, not a default.

**Do the shared setup once, then fan out the rest in parallel.** Steps 1-3 below are per-repo, not per-subtask — do them a single time before touching any individual worker. Steps 4 onward are per-subtask and genuinely independent of each other (different worktree, different pane, different everything) — issue them for all subtasks concurrently (multiple tool calls in one message) instead of looping one worker fully through steps 4-9 before starting the next.

Shared setup, once per repo:

1. **Detect existing isolation first** (`superpowers:using-git-worktrees` Step 0). Never nest worktrees.
2. **Find where this project already puts worktrees — do not assume `.worktrees/`.** An existing project-local directory wins over the default; explicit user instruction wins over both:
   ```bash
   git worktree list                    # reveals the convention already in use
   ls -d .worktrees worktrees 2>/dev/null
   ```
   Priority: user instruction → existing directory (`.worktrees/` if both exist) → default `.worktrees/`. A repo already using `.claude/worktrees/` keeps using it — that's also Claude Code's own built-in default for `--worktree`/`EnterWorktree`, so a repo that has never customized this already has that directory.
3. **Verify that directory is gitignored** before creating anything:
   ```bash
   git check-ignore -q <worktree-dir> || echo "NOT IGNORED — add to .gitignore and commit first"
   ```
   Exit 1 means not ignored. Add it to `.gitignore` and commit *that* first — otherwise the whole worktree tree gets committed into the repo. A repo with no `.gitignore` at all still needs this.
4. **Set up `.worktreeinclude` for gitignored files every worker needs** (`.env`, secrets, local config) instead of copying them by hand per worker. This is Claude Code's own built-in mechanism, not cmux- or executor-specific:
   ```bash
   test -f .worktreeinclude || cat > .worktreeinclude <<'EOF'
   .env
   .env.*
   EOF
   git add .worktreeinclude && git commit -m "chore: copy env files into new worktrees"
   ```
   Syntax matches `.gitignore`; only files that are both gitignored and matched by a pattern here get copied — tracked files are never duplicated. If the project already has a `.worktreeinclude`, trust it and skip creating one; add missing patterns rather than overwriting if a specific file a worker needs (per its contract) isn't covered. This replaces manual `cp` of `.env`-style files — never symlink them regardless of mechanism, copies only.

5. **Pre-accept the folder-trust dialog for every worker directory, in one call, before opening any pane.** Otherwise each worker may park on `Do you trust this folder?` waiting for a human to pick "Yes, I trust this folder" — and you'd be clicking through that pane by pane while nothing runs:
   ```bash
   ~/.claude/skills/executor/scripts/pretrust.sh <worktree-dir>/<task-1> <worktree-dir>/<task-2> ...
   # or check first, changing nothing:
   ~/.claude/skills/executor/scripts/pretrust.sh --check <dir> ...
   ```
   It resolves each path, skips any that already inherit trust from a parent (so it's a **no-op for in-repo worktrees**, the normal case), writes only what's missing, backs up `~/.claude.json` first, and is idempotent — safe to run on every dispatch.

   This is worth doing unconditionally because it costs one call and removes a class of silent stall. It matters whenever worker directories sit **outside** the trusted repo. No CLI flag substitutes for it: verified that neither `--dangerously-skip-permissions` nor `--permission-mode bypassPermissions` skips the trust gate, which runs before permission handling.

   Trust matches the **resolved** path (`/tmp/x` is really `/private/tmp/x` on macOS); the script handles that, but it's why hand-registering the unresolved path does nothing.

For each pane-worker subtask, in parallel:

5. Create it: `git worktree add <worktree-dir>/<task-name> -b <task-name>`
6. **Bootstrap:** install deps matching the project's own convention (`uv sync`, `npm ci`, …), then run the existing tests once to verify a clean baseline. A dirty baseline makes every later failure ambiguous. (Gitignored files arrive automatically via `.worktreeinclude` from step 4 — nothing to copy by hand here.)
7. **Check the name is free** — `cc <name>` *resumes* an existing session, so a collision silently hands a stale session a new brief. **Check `cmux tree`, not `cc ls`:** a worker under this skill never exits (see `worker`'s "Stay in session. Do not exit."), and `cc`'s own session registration only runs after its wrapped `claude` process exits — so a live worker from a run in progress is invisible to `cc ls` by construction, and that check always false-negatives on the exact case it exists to catch.
   ```bash
   cmux tree | grep -q "<task-name>" && echo "COLLISION"
   ```
   On collision, suffix (`-2`) and ledger the rename. Never resume across tasks.
8. Open the pane per the Layout section above — first worker splits right of executor, each subsequent worker splits **down from the last worker**, then equalize — `cd`-ing into the directory resolved in step 2:
   ```bash
   # first worker only: new-pane, splitting right of executor
   cmux new-pane --direction right --focus false \
     --command "cd <worktree-dir>/<task-name> && <harness launch command>"

   # every subsequent worker: new-split, targeting the PREVIOUS worker's surface
   cmux new-split down --surface <previous-worker-surface> --focus false \
     --command "cd <worktree-dir>/<task-name> && <harness launch command>"

   # after the last worker is open, make the right column evenly divided
   cmux rpc workspace.equalize_splits '{"workspaceId":"'"$CMUX_WORKSPACE_ID"'"}'
   ```
   **Use `new-split` for workers 2..N, never `new-pane --direction down`.** `new-pane` ignores `--surface` for direction purposes and splits relative to the *active* pane, so the second worker lands **under the executor** in the left column instead of under worker 1 — the left side stops being all-executor and the grid is wrong from then on. `new-split <dir> --surface <ref>` is the only form that actually splits the surface you name. Verified: `new-pane --surface w1 --direction down` put the worker at x=240 (executor's column); `new-split down --surface w1` put it at x=809 (worker column), as intended.

   **Always run `equalize_splits` after the last worker opens.** Splitting each new worker off the previous one halves only that one's space, so without it worker 1 keeps h=526 while workers 2 and 3 get h=263 each — the "one pane split many times, another not at all" imbalance. After equalizing, all three sit at h=350. This is the whole fix for uneven stacking; don't try to compute sizes by hand.

   Build `<harness launch command>` from the plan's `Harness` + `Model` using the `harnesses` skill. Examples: `cc <task-name> --model <model>` for Claude Code, or `pi --name <task-name> --model <model>` for Pi. If `Harness: auto`, choose before launching and ledger the actual harness/model. For auto choices, prefer quota-aware routing across Claude/Pi/Codex instead of exhausting one pool: normal coding should use Sonnet, Terra, or GPT-5.5; hard/Opus-level work should use Sol or Opus; pick the account/harness with the best current 5h/week headroom and reset time.

   `new-pane` has **no `--cwd` flag** — the `cd` in `--command` is how the worker lands in its worktree. Use an **absolute** path for `<worktree-dir>` here: the new pane's default cwd is not guaranteed to be the repo root, so a relative `cd` can fail silently and leave a bare shell where you expect a running agent.

   **Verify the geometry, don't trust `cmux tree`** — its output is a flat list and shows nothing about left/right/up/down, so a broken grid looks identical to a correct one there. Read real pixel frames instead:
   ```bash
   cmux rpc pane.list '{"workspaceId":"'"$CMUX_WORKSPACE_ID"'"}' | python3 -c "
   import json,sys
   d=json.load(sys.stdin)
   for p in sorted(d['panes'], key=lambda p:(p['pixel_frame']['x'], p['pixel_frame']['y'])):
       f=p['pixel_frame']
       print('%-10s x=%-6.0f y=%-6.0f w=%-6.0f h=%-6.0f %s' % (p['ref'],f['x'],f['y'],f['width'],f['height'],p['surface_refs']))
   "
   ```
   Correct output has **exactly one x for the executor** (the smallest) spanning the full height, and every worker sharing a single larger x with equal heights.

   Steps 8-10 stay strictly sequential *within* one worker — never send a brief before step 9 confirms that worker's own banner. But there's nothing stopping worker A from being at step 9 while worker B is still at step 5: open all N panes (step 8) first, back to back, then move through step 9/10 for each.
9. **REQUIRED — confirm the agent actually started before sending anything else:**
   ```bash
   cmux surface-health --workspace "$CMUX_WORKSPACE_ID"
   cmux read-screen --surface <surface> --lines 30
   ```
   Check surface health first — an unhealthy surface explains a launch that looks stuck before you even get to reading its screen. Then look for the `cc`/Claude Code banner or its prompt. A bare shell prompt (`❯` with no banner, or a `cd: no such file or directory` line) means the launch command failed and you are looking at an empty shell, not a worker. Fix the command and retry step 8 — do not proceed to step 10 on a hunch that it probably worked.

   **Third state, easy to miss: the folder-trust prompt** (`Do you trust this folder?` / `❯ No, exit`). It looks alive, but it is not a worker yet and it will swallow your brief. Clear it with `down` then `enter`, then re-read and confirm the banner:
   ```bash
   cmux send-key --surface <surface> down     # move off the default "No, exit"
   cmux send-key --surface <surface> enter
   ```

   **If step 5's `pretrust.sh` ran, you should never see this** — treat it as a signal that something is off rather than a routine click-through. Trust is keyed by **resolved** path in `~/.claude.json` (`projects.<path>.hasTrustDialogAccepted`) and **inherited from parent directories**, so an in-repo worktree is covered automatically and `pretrust.sh` covers the rest.

   Seeing it anyway means one of:
   - The worker directory wasn't in the list you passed to `pretrust.sh`.
   - The launch `cd`'d somewhere other than the directory you pre-trusted.
   - `~/.claude.json` wasn't writable, or the script reported an error you skipped past.

   Clear the prompt so the worker starts, then fix the cause before the next dispatch — clicking through it every run is the thing step 5 exists to eliminate.

   Once confirmed live, rename it per the Layout section's naming rule. The worker is a pane/split inside the executor's own workspace, not a workspace of its own, so this must rename its **tab**, not the (shared) workspace — `rename-workspace` here would silently rename the executor's own workspace tab instead of the worker's. The tab label is just the worker's name (the workspace already says which project); keep the `<project>-<worker>` form for the ledger/worktree/dispatch identifier, not for the tab text:
   ```bash
   cmux rename-tab --surface <worker-surface> "<worker>"
   ```
10. Send the brief to the new surface, then submit and require ACK:
    ```bash
    cmux send --surface <surface> "<the 4-part contract, verbatim from the plan>

When you receive this, reply exactly: ACK <task-id>"
    cmux send-key --surface <surface> enter
    ```
    `cmux send` only types into the target composer; it is not delivered until the explicit `send-key ... enter`. Never count a worker as dispatched after `send` alone.

    For long or multiline contracts, prefer a file handoff instead of pasting the entire brief:
    ```bash
    cmux send --surface <surface> "Read /absolute/path/to/<task-id>-brief.md and execute it. Reply exactly: ACK <task-id>."
    cmux send-key --surface <surface> enter
    ```

    Do not ledger the worker as dispatched until you have seen `ACK <task-id>` via notification, transcript/session state, or screen-read fallback. If the text is visible in the input line but no ACK arrives, inspect readiness before resending; it may have been typed but not submitted.

    Sending a brief into a dead shell types it as literal shell commands, one line at a time — every line break executes, every `(`, `[`, `:` gets interpreted by the shell. This produces a wall of `zsh: bad pattern` / `command not found` errors that looks like noise, not like a dispatch failure. Treat any such errors on a just-opened surface as proof step 9 was skipped or misjudged, not as a worker problem.
11. Ledger it only after ACK (Step 2, below).

**Never paste your own conversation history into a brief.** Send exactly what the plan's contract says — the contract was written assuming zero shared context, so it needs nothing added.

## Review and completion policy

Use the plan's review guidance as a starting point; the actual diff decides the tier. Leaf changes may need validation only; ordinary changes get a new independent fast_ai reviewer session; trunk/critical changes get a new independent deep_ai reviewer session and human review. Human review never replaces AI review. Fast and deep reviewers normally use Sonnet or GPT-5.5, preferably a different provider from the worker. Do not spend Opus/Sol on routine review. A passed review is not human approval; queue human review without opening VS Code until the user requests it.

If a worker loses quota, wait when its task is nonblocking and reset is near; otherwise hand off useful diff/progress or restart clean if tangled. If the executor's quota is running out, hand off plan path, goal, ledger, live pane refs and next actions to another capable executor before exhaustion. Routing defaults belong in `harnesses`, not in each plan.

Before claiming completion: meet the goal, validate, commit the changes, and report briefly what succeeded, what could not be done and why. At the end of the final report, offer optional post-run self-healing. Only run it if the user accepts; propose skill/extension diffs and apply only after explicit approval. Record unusual workflow friction via `/selfheal note`, not a new run telemetry system.

## Step 2: Ledger

`progress.md` at the run's workspace path. **One line per event.** Nothing structured — no rulings, no adjudication, no spend tracking.

```
dispatched auth-refactor-login  .worktrees/auth-login  surface:12  sonnet  14:32
notify auth-refactor-login DONE 14:51
review auth-refactor-login PASS 14:58
```

Write-only on the happy path. Its only job: if your pane dies, a fresh `executor` invocation reads this plus `cmux tree` and the original plan `.md`, and knows what's still running instead of reconstructing it from memory.

## Step 3: Supervise — block on the event stream, don't poll

**Do not poll. Block.** cmux exposes a real event stream (`cmux events`) carrying the agents' hook firings in real time. One blocking call replaces the whole polling loop: you sleep until a worker actually needs you, then wake with that worker's surface and what it said. Measured on this machine: a worker's turn-completion reaches the stream in **~1s**, a worker asking a question in **~2s**.

Use the `harnesses` skill's watcher, in the **foreground**, with one `--state` per run:

```bash
~/.claude/skills/harnesses/scripts/agent-inbox.py --state <project> --timeout 900 \
  --surface <worker-1-surface> --surface <worker-2-surface>
```

It prints one line per item and exits `0`, or prints `TIMEOUT` and exits `2`. Surfaces come back as `surface:N` refs, so no UUID mapping is needed:

| Line | Means | Your move |
|---|---|---|
| `QUESTION surface:N \| …` | Worker called `AskUserQuestion` — **its pane just turned blue waiting on you** | Read the question from the transcript (below), answer it |
| `APPROVAL surface:N \| …` | Worker is parked on a permission prompt | Approve/deny via `send-key` |
| `REPLY surface:N (turn) \| <text>` | Worker ended a turn; `<text>` is its full last message | If it reported a terminal state, read `REPORT.md` in its worktree; otherwise it's working or asking in plain text — handle it |
| `TURN_NO_TEXT surface:N \| …` | Turn ended but no text was found | Liveness check (`surface-health`, `read-screen`) |

**Why this watcher and not the older `executor/scripts/wait-agents.sh`:** `wait-agents.sh` anchors at the *current* event seq on every call. Any worker that finishes while you're busy handling another one fires its event *between* two calls, and the next call never sees it: that worker sits idle and invisible until the 15-minute timeout. Observed live with three agents. `agent-inbox.py` persists the last handled seq and resumes from it, so nothing is lost between calls. It also returns the reply text in the same call, and it treats Pi's turn ends correctly: Pi reports normal turn ends as `agent.error.reported`, not `agent.turn.completed`, so `wait-agents.sh` never sees a Pi worker finish. Keep `wait-agents.sh` only as a fallback if `agent-inbox.py` is missing.

**This closes the gap the old polling loop could not.** A worker parked on a question fires no `cmux notify`; under polling that state was invisible and only a human watching the panes would catch it. The event stream catches it in ~2s. (The `QUESTION`/`APPROVAL` branches follow the same `agent.notification.decision` kinds `wait-agents.sh` used, but have not yet been exercised through `agent-inbox.py` itself. If a worker looks parked with no line returned, check its pane.)

**Why this beats every alternative**, measured per check on this machine:

| Mechanism | Bytes into your context | Latency | Catches a blue/waiting pane? |
|---|---|---|---|
| `agent-inbox.py` | **one line per event** | ~1-2s | **Yes** |
| `cmux list-notifications --json` | ~840 per poll | poll interval | No |
| `cmux read-screen` | ~892 per poll | poll interval | Only by eyeballing |
| `cmux sessions --agent claude --json` | **~130,000** | poll interval | Via `agent_lifecycle` |

`cmux sessions --json` dumps every saved record for every agent — ~130KB, unfiltered by surface in practice. **Never call it in a supervision loop.** It is a last-resort forensic tool for a worker whose surface you've lost, not a status check.

Loop shape, for a run with live workers:

```
while workers remain:
    agent-inbox.py --state <project> --timeout 900 --surface <each live worker>
    -> on exit 0: handle each printed line, then loop immediately
    -> on exit 2: nothing happened in 15 min — check liveness (surface-health, top)
```

**Run it in the foreground.** In the background, the completion notice reaches you late, or the call gets moved to background when the user types, and workers sit idle meanwhile. Between wakeups you spend **zero** tool calls and zero context on supervision. If `cmux events` is unavailable, the script falls back to polling notifications on its own.

**One caveat, verified:** cmux emits each event **twice**; the script dedupes on `seq`, so only handle duplicates yourself if you call `cmux events` directly. Also note many `agent.hook.*` events carry `surface_id: null` (only `workspace_id`) — `agent.notification.decision`, which the script filters on, reliably carries the surface, which is why it's the event to watch.

**Rule that applies everywhere in this skill, not just Step 4: never `read-screen` to read what a worker actually wrote.** A narrow split pane can render a column only a few characters wide and silently lose text — not just wrap it badly. This bit during testing on exactly this kind of read (trying to see a worker's DONE report), not just on reviewer verdicts. `read-screen` is fine, and only fine, for a liveness glance — is there a banner, is the prompt idle, is it visibly stuck. The moment you want to know *what it said*, use one of these instead, in order of preference:
0. **The `REPLY … (turn) | <text>` line `agent-inbox.py` already gave you** — the worker's full last message, read from cmux's hook store or its transcript, never from the screen. For a terminal report, still open `REPORT.md` in its worktree; that is where the `worker` contract puts the evidence.
1. **`cmux list-notifications --json`'s `body` field** — but **only ever the first line of it**. Verified on this machine: `cmux notify --body` is truncated at the first newline, so a worker that sends a multi-line report gets `STATUS: DONE` stored and its entire VALIDATION block silently dropped. The queue also evicts older entries (3 were retained during testing). Treat the notify body as a one-line status flag and a pointer, never as the report. The moment you need more than that one line, go to the transcript.
2. **The session's `.jsonl` transcript** — for anything longer, or for a worker parked on a question that hasn't (and won't) notify. Every Claude Code session writes its full transcript, unwrapped, regardless of pane width, to `~/.claude/projects/<cwd-with-dashes>/<session-id>.jsonl`:
   ```bash
   ls -t ~/.claude/projects/*<worktree-dir-name-with-dashes>*/*.jsonl | head -1
   ```
   Parse the last assistant message's text content (`message.content[].text` on `type: "assistant"` entries, one JSON event per line). Step 4 below reuses this same mechanism for review verdicts specifically — same technique, same reason.

`cmux notify` is how a worker tells you it reached a terminal state with a message attached. Don't detect *that* by re-reading the worker's pane — query the structured notification queue instead:

```bash
cmux list-notifications --json
```

This returns every queued notification with `surface_id`, `is_read`, `title`, `body`, `created_at` — filter by the worker's `surface_id` and `is_read: false` to know precisely whether *that* worker notified, with the real body text, no screen-rendering involved. This is strictly better than `read-screen` for this purpose: it can't be broken by a narrow pane (a real failure mode — see Step 4), and it distinguishes "notified" from "still working" with certainty instead of inference.

**This queue is the fallback, not the primary loop — Step 3's `agent-inbox.py` is push, and it works.** `cmux events` is a genuine streaming subscription: a blocking call that returns the instant a worker needs you. (`cmux wait-for` is *not* that — it's a named sync token for coordinating scripts, and it can't observe an agent session. That limitation is real and is why `wait-for` isn't used here; it does not apply to `cmux events`.)

Use the notification queue when you need the one-line body a worker attached to a report, or when the event stream is unavailable. If you ever do fall back to polling it, 30-60s while actively supervising; don't stretch past a couple of minutes, or a human watching the same panes will see a `DONE`/`BLOCKED` before you do.

```bash
cmux list-notifications --json | python3 -c "
import json, sys
data = json.load(sys.stdin)
unread = [n for n in data if not n['is_read']]
for n in unread:
    print(n['surface_id'], '|', n['title'], '|', n['body'])
"
```

Note in the live-tested output on this machine that a notification can be silently marked `is_read: true` the moment its originating surface is focused/visible — not just when you explicitly call `mark-notification-read`. Don't assume `is_read: false` will still be true by the time you check a worker's surface if you looked at its pane in between; the queue and the pane can race. When in doubt about a specific worker, the `read-screen` fallback below still exists for that reason.

Mark what you've handled so the queue doesn't re-surface it:

```bash
cmux mark-notification-read --id <uuid>
```

`cmux notify` catches terminal states. It does **not** catch a worker mid-task, parked at its own prompt with a question, waiting on *you* — nothing about that state fires a notify. **The event stream does catch it** (`agent.question.requested` / `agent.approval.requested`, ~2s), which is why Step 3 makes it the primary loop; you no longer have to eyeball panes for this. Use the pane read below only when the event stream is unavailable, or when a worker has gone quiet with no event at all (genuinely stalled, hibernated, or a dead shell). Check liveness first:

```bash
cmux surface-health --workspace "$CMUX_WORKSPACE_ID"
cmux read-screen --surface <surface> --lines 20
```

Use this only when the notification queue shows nothing but you have reason to suspect a worker stalled (e.g., unusually long since dispatch with no notify) — not as your default 30s loop. The queue is the primary signal; this liveness check is the fallback for the gap it can't cover. Check `surface-health` alongside it: a stale-looking screen and an unhealthy surface point at the pane itself being broken, not at the agent being slow.

**If `read-screen` shows a parked question you need the full text of** (a multi-line prompt, a menu with wrapped option text), don't fight the render — go straight to the `.jsonl` per the rule above instead of squinting at a possibly-truncated pane.

Whichever signal caught it, you have three moves available — use whichever the situation calls for:

- **Parked on a question, otherwise fine** → answer it and move on. Same as handling `NEEDS_CONTEXT`, just caught without waiting for the worker to remember to notify.
- **Visibly off track but salvageable** (misread part of the contract, chasing the wrong file, minor confusion) → clarify in place, same pane, same context. No reset needed — this is cheaper than a restart and preserves useful work already done.
- **Genuinely stuck, thrashing, or burning context with no progress** (repeating the same failed approach, context climbing with no forward motion, clearly lost) → close it and redispatch fresh, rather than let it keep spending. This is a judgment call, not a fixed turn-count trigger — you're watching for "no longer converging," not counting to a number.

```bash
cmux close-surface --surface <surface>
```

**Don't judge "still working" from the screen alone — check real process activity:**

```bash
cmux top --workspace $CMUX_WORKSPACE_ID
```

This shows live CPU% and memory per pane, tree-structured. A pane sitting at 0% CPU for a while despite a busy-looking screen (mid-edit text, a spinner) is a stronger stuck signal than the screen itself — text can be stale, CPU can't. Use this to break ties when `read-screen` looks ambiguous, not as a routine replacement for the notification-queue poll above.

**Watch for memory pressure hibernating a worker out from under you.** cmux can hibernate inactive/hidden agent surfaces under memory pressure — you'll see a `cmux está utilizando...memoria` notification in the queue when this is happening. A hibernated worker looks identical to a stalled one from the outside (no progress, no notify) until you check:

```bash
cmux memory --workspace $CMUX_WORKSPACE_ID
```

For a run you're actively supervising, turn hibernation off for its duration so a worker never silently disappears mid-task:

```bash
cmux agent-hibernation off   # before Step 1 dispatch
cmux agent-hibernation on    # after Step 6 close-out, or when you're done supervising
```

If a worker is genuinely still working productively (mid-edit, running a command, making progress), leave it — the default action is always to leave it alone; only intervene when the screen shows a specific reason to. This changes nothing about `DONE`/`BLOCKED` handling below — those still arrive by notify.

Handle reports per `superpowers:subagent-driven-development`:

| Status | Action |
|---|---|
| `DONE` / `DONE_WITH_CONCERNS` | Proceed to review. Read the concerns first. |
| `NEEDS_CONTEXT` | Send the missing context to the same live pane. |
| `BLOCKED` | Assess: more context, escalate model, split the task, or correct the plan. Never force the same model to retry unchanged. |

**Workers may message each other directly, on a narrow channel.** When worker A's brief references something worker B owns (a shared interface, a constant, a decision B already made — as flagged in the plan's cross-refs), routing that through you every time adds a round-trip for no benefit. Let a worker `cmux send` a short, specific question straight to another worker's surface when:

**Hand every worker the surface map at dispatch, in its brief.** The plan only had worker *names*; resolve them once with a single call and append the mapping to each brief:

```bash
cmux tree --id-format both        # name -> surface:<ref> + UUID, whole run in one read
```

Tell each worker its own name and its peers' refs, e.g. `you are api-auth (surface:128); peers: api-db=surface:135`. A worker with no map cannot use this channel at all, and will route everything through you.

**Also tell them the prefix convention:** cross-worker messages must start with `[worker <name> asks]`. Verified in testing: a worker receiving an unlabeled instruction to message another pane **refuses it as session manipulation** — twice, including when the framework was explained. The transport is fine (the identical `send` from you is answered normally); the refusal is about missing provenance. Without the prefix in the brief, the cross-worker channel silently doesn't exist and you'll see questions come back to you instead.

- It's a **question or a status ask**, not a code change — "what did you name the shared enum" is fine; "let me edit your file" is not. `cmux set-buffer`/`paste-buffer` is a reasonable alternative to a `send` for a short value one worker wants to hand another programmatically, rather than as a typed message.
- It never substitutes for a real interface decision that should have been made in the plan — this is for filling small gaps in an otherwise-independent split, not for two workers renegotiating scope live. If the question reveals the split wasn't actually independent, that's a planning miss to feed back into `planner` next time, not something to patch over with more cross-talk.
- **A worker never edits, reads via shell, or reasons about another worker's worktree files directly** — worktree isolation is what prevents the collision this skill exists to avoid, and a stray cross-worker file read defeats it as surely as a stray write would. The channel is text (or a buffer value) between two Claudes, nothing else.

You don't need to broker each message, but you do need to see that it happened — it'll show up as a `cmux notify` or plain `send` on the receiving worker's surface, which your poll already covers. If cross-talk turns into a real back-and-forth, that's a `DONE_WITH_CONCERNS`-worthy detail for the sender to flag in its own report.

## Step 4: Review

After `DONE`/`DONE_WITH_CONCERNS`, apply the review tier above. For fast_ai or deep_ai, open a **new independent pane** running `reviewer` with that tier, positioned below executor's own pane. Validation-only needs no AI reviewer. Never reuse the worker's pane — self-review is not independent review.

Once confirmed live, rename its tab — it's a pane in the executor's own workspace, same as a worker, so this is `rename-tab`, not `rename-workspace`:
```bash
cmux rename-tab --surface <reviewer-surface> "reviewer"
```

**One reviewer at a time, always.** If a second worker reports DONE while a review is already in progress, it queues — its worktree and pane stay live and untouched, you just don't open a second reviewer pane for it yet. This isn't just layout tidiness: review is the actual bottleneck (Step 1's cap rationale applies here too), and a queue of one thing you're reading beats two verdicts arriving in parallel that get skimmed instead of read.

Open the reviewer pane, get its verdict (see below), then close it before opening the next one — never let reviewer panes accumulate.

**Don't close the worker's pane on DONE.** Keep it live until its review actually lands ✅ — if the reviewer finds something, Step 5's one retry goes to that same pane with its context intact; closing early would force a cold redispatch for a fix that should've been a two-line note. Close the worker's pane only once its own review passes, or after the one retry in Step 5 fails and you've told the user.

**Reading a verdict: use the `.jsonl` rule from Step 3, no exception.** The temptation here is worse than elsewhere — a busy multi-pane workspace makes `read-screen` look even more broken (narrow columns, lost text), and trusting your own diff inspection instead is exactly the self-review-substituting-for-independent-review pattern this step exists to prevent. Get the reviewer's actual verdict text from its `.jsonl`, same command as Step 3, same reasoning: it's the same mechanism `cc usage` and `framework-retro` already rely on for token accounting — reuse it here for content, not just numbers.

## Step 5: When review finds a problem

**One retry, not a loop.** Send the finding to the worker's still-live pane (it's still open — see Step 4). If the second attempt still isn't right, **record it in the ledger for the final report and move on** (don't stop to tell the user mid-run), then close the worker's pane per the Layout section's cleanup rule. Do not escalate models, redispatch, or adjudicate rounds.

This is a deliberate trade against `subagent-driven-development`'s 5-round fix loop: a second miss is cheaper to surface in the final report than to automate around.

## Step 6: Finish

**Never automerge.** Use `superpowers:finishing-a-development-branch` for close-out; the user merges from the primary checkout.

Don't ask the user to confirm anything — leave each reviewed branch ready to merge and open the actual diff for them instead of a text summary — `cmux diff --branch` renders it in a browser split, which is easier to review than terminal text and doesn't depend on them trusting your description of what changed:

```bash
cmux diff --branch --repo <worktree-path> --title "<task-name> ready to merge"
```

Check conflicts/rebase **only here**, never during the run. If `main` moved, rebase that branch, one worktree at a time. On a rebase conflict, abort the rebase (`git rebase --abort`), leave the branch as it was, and list it in the report as "needs manual rebase" — don't resolve it and don't ask.

**End the run with one final report — the only time you address the user.** It contains:
- **Resultado:** per subtask — branch, review verdict, ready to merge / needs attention.
- **Supuestos:** every `ASSUMED:` line from the ledger — what you assumed and why, so the user can correct it.
- **Pendiente para ti:** merges, pushes, rebase conflicts, subtasks that failed their one retry.

## Autonomy rule

**You never ask the user anything during the run.** Everything is either decided by the plan or decided by you — with the assumption recorded and reported at the end. This covers routine things (phrasing a correction, closing a stuck pane, wording a ledger line) and non-routine ones (a gap in the plan, an ambiguous contract, a worker's question the plan doesn't answer, a failed retry).

The only things you don't *do* yourself are actions that reach outside the worktrees: **merge, push, publish, resolving a rebase conflict.** You don't ask about them either — you leave them ready and list them under "Pendiente para ti" in the final report.

## Red Flags

- Writing or revising a task contract from scratch instead of pulling it from the plan → that's `planner`'s job; if the plan is missing something, that's a planning gap to send back, not yours to improvise.
- Reading a worker's pane more often than the ~30-60s healthcheck, or reading it to judge the work rather than to check if it's stuck on a question → that's supervision creeping back in, not a status read.
- Calling the `Agent` tool to dispatch a subtask, for any reason → every subtask is a pane worker in a worktree; there is no subagent path.
- Concluding "these are small/simple, panes are overkill, I can skip cmux" → that is the known failure mode, not an optimization. Size never makes a subtask ineligible for a pane.
- Honoring a `Mechanism: subagent` line from an older plan → treat it as `pane` and note the correction in the ledger.
- Pasting your conversation history into a brief → send exactly what the contract says.
- Dispatching without the model the plan specified → you just billed a different tier than planned.
- Creating a worktree before checking `git check-ignore` → you may commit the whole tree.
- Copying gitignored files by hand instead of setting up `.worktreeinclude` once → repeats manual work Claude Code already solves declaratively.
- Sending a brief right after `new-pane` without checking `surface-health` and reading the surface first → you cannot tell a live agent from a dead shell that is about to eat your brief as commands.
- Declaring "workers are running in parallel" without having seen each worker's banner/prompt on its surface → that is a guess dressed as a status report.
- Reusing the worker's pane for review → same blind spots.
- A third fix attempt → record it for the final report instead.
- Merging because it "obviously" applies cleanly → not yours to decide; leave it under "Pendiente para ti".
- Calling `AskUserQuestion`, or ending a turn with a question to the user, at any point during the run → assume, record `ASSUMED:`, keep going, report at the end.
- Forwarding a worker's question to the user → answer it yourself from the plan and your judgment.
- Closing a worker's pane the moment it says DONE → keep it live until its review actually passes; a queued or in-progress review may still need to send it a fix.
- Opening a second reviewer pane while one is still active → queue it instead; one reviewer at a time, always.
- Splitting a dev-server preview or a research browser into the worker column → those are tabs, not workers; don't let them compete for the fixed split geometry.
- More than 7 panes open at once → hit the cap before dispatching further; queue the rest.
- Opening worker 2+ with `new-pane --direction down` instead of `new-split down --surface <prev worker>` → the worker lands in the executor's own column and the n×2 grid is broken from that point on.
- Skipping `workspace.equalize_splits` after the last worker → the right column ends up with one tall pane and the rest squeezed; splitting is halving, so it never self-balances.
- Judging the layout from `cmux tree` → it's a flat list with no geometry; a wrong grid looks identical to a right one. Read `pane.list` pixel frames.
- Polling `cmux sessions --agent claude --json` in a supervision loop → ~130KB into your context per call; use the event stream.
- Treating a multi-line `cmux notify --body` as a delivered report → everything after the first line is silently dropped.
- Dispatching a worker without its peers' surface refs and the `[worker <name> asks]` prefix convention → the cross-worker channel silently doesn't exist; peers refuse unlabeled messages.
- Clicking "Yes, I trust this folder" pane by pane after dispatch → run `pretrust.sh` on every worker directory once, before opening any pane.
- Supervising with a watcher that starts from "now" on each call (`wait-agents.sh`) or running the watcher in the background → workers that finish between calls go unseen and sit idle; use `agent-inbox.py` in the foreground.
