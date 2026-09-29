---
name: harnesses
description: Cross-harness orchestration for Claude Code, Pi, Codex/OpenAI API, and other terminal AI agents in cmux panes. Use whenever a planner, executor, worker, or human wants to choose which AI harness/model should run a task, hand off between Claude and Pi/OpenAI models such as Astra, dispatch agents by subscription vs API cost, or hold live back-and-forth conversations with several agent panes at once (send, get each reply the moment it lands, react).
compatibility: Works in Claude Code and Pi because it uses the Agent Skills SKILL.md format and only assumes shell/cmux commands are available.
---

# Harnesses

Use this skill to decide **which terminal AI harness** should own a task and how to launch or hand off to it from another harness. A harness is the outer agent runtime: Claude Code (`cc`/`claude`), Pi (`pi`), or Codex/OpenAI (`codex`). Astra is treated as an **OpenAI model/provider choice**, not as its own harness, unless the user later installs a separate `astra` CLI wrapper.

The goal is not to make one master agent omniscient. The goal is to let the current master/executor route work to the cheapest competent runtime, preserve isolation with cmux + worktrees, and make handoffs explicit enough that Claude and Pi can both understand them.

## User-interaction style

When a harness, dispatcher, planner, or workflow command needs a decision from the user, ask **one interactive question at a time**. Do not dump a questionnaire or a full decision frontier unless the user explicitly asks for a batch. Prefer a concise question with options and one recommended answer, then wait. This keeps cmux/Pi workflow design usable without scrolling through long walls of questions.

Format:

```markdown
**Q<n> - <title>**
<short question + options>

Recommended: <answer>
```

## Vocabulary

- **Master / executor**: the session coordinating work.
- **Worker**: a pane agent in its own git worktree, given a self-contained brief.
- **Harness**: the CLI/runtime used for that pane (`cc`, `pi`, `codex`, `astra`, etc.).
- **Model**: the model/provider inside the harness (`opus`, `sonnet`, `openai/gpt-5`, etc.).
- **Handoff**: opening a new cmux pane in another harness and sending it a brief, or asking the human to do so if cmux is unavailable.

## Routing policy

Use a **hybrid default**: Claude Code for planner/executor/mastermind roles, Pi for routine workers, glue, handoffs, one-shot checks, and configurable cmux-facing orchestration. The working assumption is that Claude Code/Opus is stronger for high-level planning, supervision, and judgment, while Pi tends to be more token-efficient and more configurable around cmux, skills, tools, prompts, model routing, and workflow conventions. Upgrade a Pi worker to Claude Code only when the task needs Claude Code-specific behavior, Opus-level judgment, hard debugging, or when Pi lacks the required provider/model/tool.

| Task shape | Preferred harness/model |
|---|---|
| Planner/executor/mastermind | Claude Code, preferably Opus for hard runs or Sonnet for normal runs |
| Mechanical edits, tests, grep-heavy repo chores | Pi with a cheap/mid OpenAI or Anthropic model |
| Multi-file coding with existing tests | Pi with a strong coding model first; Claude Code Sonnet if Pi is missing capability or struggles |
| Ambiguous architecture, product judgment, tricky debugging | Claude Code Opus / highest-capability model |
| Independent critique or alternate implementation idea | Use a different provider family than the worker if possible |
| Fast one-shot research/summarization | Pi print mode (`pi -p`) |
| User explicitly requests a harness/model | Obey unless unavailable; if they request Astra, use an OpenAI-capable harness, preferably Pi with the OpenAI/Astra model configured |

Cost/config principle: use Claude Code where intelligence is the bottleneck and Pi where harness configurability/token efficiency is the bottleneck. Planner and executor should generally be Claude Code so the run's central judgment is strong. Spawned workers may use **any available harness** (`claude-code`, `pi`, or `codex`) instead of defaulting to one account. Prefer the user's coding-model pool by task difficulty and current quota: for normal coding use Claude **Sonnet**, OpenAI/Codex **Terra**, or **GPT-5.5**; for hard/Opus-level work use OpenAI/Codex **Sol** or Claude **Opus**. If one pool is near limit, blocked, or has a worse reset window, route the worker to another pool/harness. Most OpenAI/Astra/Sol/Terra/GPT-5.5 calls should generally go through Pi first when Pi can access the model; use Codex/OpenAI CLI when Pi cannot access the desired model/provider, when Codex has better available quota, or when the user explicitly asks for Codex. Do not silently run many expensive API agents; say when a dispatch may cost money.

## Quota-aware dispatch preference

Before dispatching workers, quickly check account status when practical:

- Pi footer/status if already visible: compare `openai`, `pi`, and `claude` 5h/week percentages and reset times.
- Claude: `claude -p /usage`.
- Codex/OpenAI CLI: `codex app-server --stdio` with `account/rateLimits/read` if a script already exists, or `codex login status` as a weaker fallback.
- Pi OpenAI/Codex auth: Pi stores credentials in `~/.pi/agent/auth.json`; a Pi extension may expose Pi-specific usage in the footer. Prefer that over assuming Pi and Codex CLI are the same account.

Routing rule for coding workers:

1. For **normal coding**, use **Sonnet**, **Terra**, or **GPT-5.5**, choosing the pool with the best available quota.
2. For **hard / Opus-equivalent work**, use **Sol** or **Opus**.
3. Prefer **Pi** for OpenAI/Codex models when Pi can launch the exact model and has quota; use **Codex CLI** when Codex has better quota or Pi cannot launch that model.
4. If a selected pool is ≥80% on 5h or close to weekly exhaustion, prefer another pool unless the task specifically needs it. If everything is constrained, dispatch fewer workers and tell the user.

Ledger every auto choice as `harness/model/account-pool reason`, e.g. `pi/terra because Pi 5h 20%, Codex blocked, Claude week 99%`.

## Availability check

Before launching a non-default harness, check it exists and can see the requested model/provider:

```bash
command -v cc claude pi codex astra 2>/dev/null || true
pi --list-models 2>/dev/null | head -40 || true
```

`pi --list-models` lists only providers Pi has credentials for (`~/.pi/agent/auth.json`). **If a model isn't listed, Pi can't run it**, even if the alias resolves: on this machine Pi only has `openai-codex`, and `pi --model haiku` launched fine but died on the first message with `Error: No API key found for amazon-bedrock`. For Claude models, launch `claude --model <model>` directly instead of going through Pi.

If a requested harness is missing, do **not** fake it. Fall back in this order unless the user says otherwise:

1. `pi`
2. `cc` / Claude Code
3. `codex`
4. custom wrapper only if the user provides one

## Plan contract fields

When a plan will be executed by an executor, include both fields in every subtask:

```markdown
**Mechanism:** pane
**Harness:** claude-code | pi | codex | openai | auto
**Model:** <harness-specific model or tier>
```

Use `Harness: auto` when the executor should choose at dispatch time using the routing policy above. If the desired model is Astra, write `Harness: pi` or `Harness: openai` and `Model: <the configured OpenAI/Astra model id>`. If an older plan has only `Model`, treat `Harness` as `claude-code` for backward compatibility.

## Launch commands for cmux panes

Always launch from the worker's worktree with an absolute `cd`. Quote the prompt/brief safely when embedding it in a command; if the brief is long, launch the interactive harness first, confirm the banner, then send a short file pointer.

**Safe cmux handoff rule:** `cmux send` only types into the target surface. A submitted turn requires both:

```bash
cmux send --surface <surface> "<brief or file pointer; request ACK <task-id>>"
cmux send-key --surface <surface> enter
```

For dispatcher/executor handoffs, request `ACK <task-id>` and do not mark the worker dispatched until the ACK is observed. If text is visible but no ACK arrives, treat it as a transport/readiness issue, not a worker refusal.

### Fast same-workspace spawn recipes

When the user asks for several agents in the **same cmux workspace**, do not waste time rediscovering basic syntax if the harnesses are known to exist. Use the caller workspace: first agent splits right of you, each next one splits **down from the previous agent** (`new-split`, not `new-pane`, which would land under you), then equalize:

```bash
cwd=$(pwd)
ws=${CMUX_WORKSPACE_ID:?}
s1=$(cmux new-pane --workspace "$ws" --type terminal --direction right --focus false \
  --command "cd '$cwd' && codex --model gpt-5.6-luna" | grep -o 'surface:[0-9]*')
s2=$(cmux new-split down --surface "$s1" --focus false \
  --command "cd '$cwd' && claude --model haiku --dangerously-skip-permissions" | grep -o 'surface:[0-9]*')
s3=$(cmux new-split down --surface "$s2" --focus false \
  --command "cd '$cwd' && pi --name pi-terra --model gpt-5.6-terra" | grep -o 'surface:[0-9]*')
cmux rpc workspace.equalize_splits '{"workspaceId":"'"$ws"'"}' >/dev/null
echo "$s1 $s2 $s3"
```

**Startup dialogs to clear before sending anything** (a message sent into a dialog is lost or picks an option):
- **Codex**: an "Update available" menu (default = *Update now*) — `send-key down` then `enter` to pick *Skip*. In a directory it hasn't seen, then a "Do you trust the contents of this directory?" menu (default = *Yes, continue*) — `enter`.
- **Pi**: an "Update Available" banner that does not block the prompt; send normally.
- **Claude Code**: the folder-trust dialog in unseen directories (see `executor`'s `pretrust.sh`).

If exact model availability is uncertain, do one compact check first:

```bash
command -v claude pi codex 2>/dev/null || true
pi --list-models terra 2>/dev/null | head -20 || true
```

After spawning, verify the surfaces are live with `cmux tree` and `cmux read-screen --surface surface:<n> --lines 30`.

### Naming / renaming practical note

Prefer setting session names at launch when the harness supports it:

```bash
pi --name pi-terra --model gpt-5.6-terra
# Claude/Codex pane titles are usually inferred from the running app/model; if a durable label is needed,
# put it in the shell command prompt/banner or record surface refs in the report.
```

cmux pane/surface refs are the reliable handles for orchestration (`pane:42`, `surface:77`). If a future cmux version exposes pane rename commands, prefer those for human readability, but do not block a spawn just to rename.

### Claude Code worker

Prefer the actual Claude Code executable (`claude`) unless `cc` is known to be a Claude Code wrapper in the current environment. On macOS `cc` often resolves to `/usr/bin/cc` (clang), not Claude Code; always check before using it.

```bash
command -v cc claude 2>/dev/null || true
cc --help 2>&1 | head -3      # must say Claude Code, not clang
cd <worktree> && claude --model <model>
```

For trusted cmux worker panes where the user explicitly wants no permission prompts, launch Claude with dangerous bypass so its shell/tool use doesn't stop at approvals. (Replies themselves don't need it: `agent-inbox.py` reads them without the agent running any command.)

```bash
cd <worktree> && claude --model haiku --dangerously-skip-permissions
```

Examples: `--model opus`, `--model sonnet`, `--model haiku`.

### Pi interactive worker

```bash
cd <worktree> && pi --name <session-name> --model <model>
```

Examples: `--model openai/gpt-4o`, `--model anthropic/claude-sonnet-4`, `--model sonnet:high`.

Pi discovers shared skills from `~/.agents/skills/` and project `.agents/skills/`. This skill lives in the Agent Skills format, so Pi can load it with `/skill:harnesses` or automatically when the prompt matches.

### Pi one-shot worker

Use for bounded research or review where no follow-up pane is needed:

```bash
cd <worktree> && pi -p --name <session-name> --model <model> "<brief>"
```

Do not use one-shot mode for code-editing subtasks that may need executor follow-up; use interactive Pi instead.

### Codex/OpenAI worker

```bash
cd <worktree> && codex --model <model>
```

Codex CLI flags differ by version. If this command fails, run `codex --help` and adapt rather than guessing.

### OpenAI/Astra model through Pi

Astra is an OpenAI-side model/provider choice in this workflow. Prefer launching it through Pi so orchestration stays configurable:

```bash
cd <worktree> && pi --name <session-name> --model openai/<astra-model-id>
```

If Pi lists the model under a different ID, use the exact ID from:

```bash
pi --list-models astra
pi --list-models openai
```

Use Codex only if Pi cannot access the requested OpenAI/Astra model.

## Pi handoff commands

A Pi extension is available at `~/.pi/agent/extensions/harness-handoff.ts`. After `/reload` or a fresh Pi start, it adds:

```text
/to-cc [--close] [model] [brief]
/cc-executor [--close] <plan.md> [model]
```

Use `/to-cc --close opus "<brief>"` to open a Claude Code pane from Pi and gracefully exit the Pi session after launch. Use `/cc-executor --close docs/planner/plans/foo.md opus` when Pi has helped prepare context but the actual executor/mastermind should run in Claude Code.

## Handoff protocol

When handing off from Claude to Pi, Pi to Claude, or either to an API-backed harness:

1. Create or reuse an isolated worktree if code will be edited.
2. Open a cmux pane running the target harness.
3. Confirm the target harness banner/prompt is live before sending the brief.
4. Send a self-contained brief. Include: objective, constraints, validation command, stop condition, allowed files, and reporting format.
5. Tell the target harness to end its turn with the report as plain text in its reply. The coordinator reads it with `scripts/agent-inbox.py` (see below). No `cmux notify` needed: a multi-line notify body is cut at the first newline, while the turn-end text arrives whole.
6. Record the handoff in the executor ledger with harness + model.

### Talking to live agents: `agent-inbox.py`

Use `scripts/agent-inbox.py` (in this skill) to hear back from agent panes — any mix of Claude Code, Codex and Pi. One call blocks until **any** watched agent has something for you and prints it as one line:

```text
REPLY surface:167 (turn) | <full text of its last answer>
QUESTION surface:166 | <detail>        # parked on AskUserQuestion
APPROVAL surface:166 | <detail>        # parked on a permission prompt
TURN_NO_TEXT surface:168 | <kind>      # turn ended, no text found — read-screen it
TIMEOUT                                # exit 2
```

**Agents do not need to run `cmux notify`.** They just answer. The script waits for the turn-end event cmux emits for all three harnesses, then reads the reply from cmux's hook store (`~/.cmuxterm/<agent>-hook-sessions.json` → `lastBody`, a local file). If that is truncated (~200 chars, ends in `…`), it reads the harness transcript instead: Claude/Codex `transcriptPath`; Pi `~/.pi/agent/sessions/*/<ts>_<sessionId>.jsonl`. Measured on this machine, send→reply was ~1.5s (Haiku), ~1.7s (Codex Luna), ~3.4s (Pi Terra) without notify, vs ~2.6 / 3.1 / 3.8s when the agent had to run `cmux notify` itself — the notify tool call costs the agent an extra model round-trip.

**It never loses a reply.** It resumes the event stream from the last event it handled (state in `~/.cache/cmux-inbox/<state>/`), not from "now", so replies that landed while you were composing your answer to someone else come back on the next call. This is the failure the older patterns had: blocking on events anchored at the current seq silently skipped every agent that finished between two calls, leaving them idle and waiting.

**The loop — one tool call per step: answer whoever spoke, then wait for the next.**

```bash
IN=~/.claude/skills/harnesses/scripts/agent-inbox.py
say(){ cmux send --surface "surface:$1" "$2" >/dev/null && cmux send-key --surface "surface:$1" enter >/dev/null; }

# open: one message per agent (different topics are fine), then wait
say 166 'Tema CACHE: ...';  say 167 'Tema GUARDRAILS: ...';  say 168 'Tema COSTOS: ...'
$IN --state chat --surface surface:166 --surface surface:167 --surface surface:168 --timeout 90

# every later step: react to the one that answered, then wait again
say 167 '<reaction to what 167 just said>'
$IN --state chat --surface surface:166 --surface surface:167 --surface surface:168 --timeout 90
```

Rules that keep it fast:
- **Send and wait in the same Bash call.** A separate call just to send is dead time.
- **Never wait for all agents before replying.** Reply only to whoever just answered; the others keep thinking and show up on the next call.
- **Run it in the foreground.** In background, the completion notice reaches you late (or the call gets moved to background when the user types), and agents sit idle.
- **Use one `--state` name per conversation.** The first call with a new name (or `--reset`) starts from now and ignores older history.
- **Don't parse replies with `read-screen`** (clips text in narrow panes) or `cmux sessions --json` (can be ~130KB).
- Keep prompts asking for short answers when you want a fast back-and-forth; model think time dominates, cmux overhead is under 0.5s.

**Optional `--prefix CHAT_` mode:** agents end each turn with `cmux notify --title CHAT_<X> --body "..."` and those notifications are the replies. Only use it when you need a named, structured signal; it is slower, and a turn that ends without the notify still falls back to the transcript. Without `--prefix`, notifications are ignored on purpose — Claude and Pi post their own truncated turn-end notifications.

Verified on this machine: backlog (three replies landing while busy → returned in one call), live interleaving across Claude Haiku / Codex Luna / Pi Terra, long replies returned complete from all three transcripts. **Not yet exercised:** the `QUESTION` / `APPROVAL` branches and the no-event-stream polling fallback.

Harness quirks it already handles:
- **Pi reports normal turn ends as `agent.error.reported`**, not `agent.turn.completed`. Anything waiting only for `turn.completed` never sees Pi finish.
- **Pi's hook record has no `transcriptPath`**; the script finds it by `sessionId`.
- **cmux emits each event twice**; deduped on `seq`.

Minimal cross-harness brief:

```text
You are a <harness> worker launched by an executor in cmux.
Worktree: <absolute path>
Harness/model: <harness>/<model>

Objective: ...
Constraints: ...
Validation: ...
Stop condition: ...

Report back with:
STATUS: DONE | BLOCKED | NEEDS_CONTEXT
SUMMARY: ...
VALIDATION: command + result
FILES CHANGED: ...
```

## Executor integration

An executor using this skill should:

- Load `harnesses` before dispatch.
- Parse `Harness` and `Model` from each subtask.
- If `Harness: auto`, choose by role: planner/executor/mastermind => Claude Code; ordinary worker/review/one-shot/glue => Pi. Deviate only for a stated reason: unavailable model/tool, Claude Code-specific need, Opus-level judgment, user instruction, or a failed Pi attempt. Log the reason.
- Keep the existing cmux/worktree layout; only the pane command changes.
- Prefer Pi for low/medium-risk reviews too. Use heterogeneous review selectively: if a Pi worker changed high-risk code, consider Claude/Opus review; if a Claude worker changed routine code, Pi review is usually enough.
- Never let harness choice override isolation: every code-editing worker still gets its own worktree and pane.

## Red flags

- Launching an API harness for many broad subtasks without warning about possible cost.
- Sending a brief before confirming the target harness is actually at its prompt.
- Assuming Pi has the same tools, commands, or skills loaded as Claude. Include what it needs or tell it to `/skill:harnesses`.
- Treating `Model: opus` or `Model: astra` as meaningful inside every harness. Model names are harness-specific; Astra should route through an OpenAI-capable harness, preferably Pi.
- Letting one harness edit the primary checkout while other workers edit worktrees.
- Waiting for every agent to answer before replying to any → reply to whoever answered; `agent-inbox.py` returns the others on the next call.
- Running the reply watcher in the background, or blocking on `cmux events` anchored at "now" between turns → agents finish unseen and sit idle.
- Asking agents to `cmux notify` their answers by default → slower (extra model round-trip) and the body is cut at the first newline.
- Launching Pi with a model `pi --list-models` doesn't show → it starts, then fails on the first message.
