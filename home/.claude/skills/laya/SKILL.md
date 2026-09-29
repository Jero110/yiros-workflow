---
name: laya
description: Use when an AI workflow or script needs a fast, cheap, local typed decision about a piece of text instead of an LLM call - classifying, routing, triaging, flagging spam/phishing, scoring urgency, yes/no checks, guardrails - or when the user mentions Laya, laya-ask, Jev, TypeSafe, or "System One" decision models.
---

# Laya (local typed decisions via `laya-ask`)

## Overview
Laya is an open-weights (Apache 2.0) "System One" decision model, an open alternative to TypeSafe's hosted Jev. It does not generate text: given a **state** (text or JSON) and **typed questions**, it returns calibrated probabilities in one forward pass. It runs locally through `laya-ask`, which is on PATH (source: `~/Desktop/laya`, installed with `uv tool install --editable`).

**Laya never invents labels.** You supply every option. To discover categories, use an LLM first, then classify with Laya.

## Question types
| type | you give | result field |
|---|---|---|
| `choice` | 2+ named options (add `other`) | `choice`, `probabilities` |
| `score` | ordered levels, lowest first | `score` (float 0..n-1), `probabilities` |
| `noul` | a yes/no question | `noul` = P(yes) |

## Quick reference
```bash
laya-ask --status                     # is the server up? (exit 0/1)
laya-ask --serve                      # start server: ~0.4 s/call vs ~16 s cold. Run in background.

laya-ask --quiet "TEXT" "QUESTION"                               # noul
laya-ask --quiet "TEXT" "QUESTION" 'billing=invoices, refunds' 'tech=bugs' other   # choice
laya-ask --quiet --score "TEXT" "How urgent?" low medium high    # score
laya-ask --json --quiet req.json      # or pipe JSON on stdin; several questions in one pass
```
JSON request: `{"state": <str|obj>, "questions": {"<key>": {"type": ..., "instructions": ..., "criteria": {...} | [...]}}}`
Stdout is Laya's raw JSON (`answers.<key>`, `routing.model`). Without `--quiet`, the query is echoed to stderr. `--model english|multilingual|typed-decisions` overrides routing.

Quick mode stores the answer under key `answer`: `jq '.answers.answer.choice'`.

## Workflow for agents
1. Before a batch, run `laya-ask --status`. If it is down, start `laya-ask --serve` in the background and poll `--status` until it is up (~20 s).
2. Put all questions about one text into a single `--json` call.
3. Write `instructions` and option descriptions in English; they work best. The state can be in any language (the router sends it to the multilingual checkpoint).
4. Gate every answer before acting. Otherwise escalate to an LLM or a human.
   - `choice`: act when `answer_confidence` (the top option's probability) ≥ 0.85. Laya always returns a `choice`, even when the probabilities are near uniform (e.g. 0.29/0.26/0.24/0.21). A bare `.choice` means nothing without this check. The separate `confidence` field is entropy-based, and near 0 means chance.
   - `noul`: act on yes when `noul` ≥ 0.85 and on no when `noul` ≤ 0.15. Treat anything in between as unknown.
   - `score`: the float is an expected level. Check `probabilities` for a near tie before rounding.

## Where it is reliable and where it is not
- **Good:** spam/phishing (>0.98), clear intent or department routing, outage/urgency, topic classification with few options.
- **False positives:** a spam/phishing `noul` can fire on legitimate text (in tests, a real outage complaint got spam=0.85). Do not auto-drop on spam alone. Cross-check with the department/intent answer, or require ≥0.95.
- **Weak:** subtle yes/no judgments (in tests it missed an explicit "or I cancel" churn threat), held-out moderation (~0.53), programming-language detection (near chance), many options.
- Keep `choice` under ~20 options, because options share a ~192-token budget.
- The English checkpoint truncates silently at 512 tokens. For long text use `--model multilingual` (1024 tokens).
- Probabilities ship over-confident. Calibrate on your own labeled data before automating decisions.

## Common mistakes
| Mistake | Fix |
|---|---|
| No options for a "which X?" question | Quick mode becomes `noul`. Pass options. |
| Overlapping option descriptions (e.g. "pricing" under both billing and sales) | Make the options mutually exclusive. Overlap gives confident misroutes (0.9999 to the wrong one). |
| Reading `.choice` without the gate | Check `answer_confidence` first (step 4) |
| One call per question | Use `--json` with every question in one call |
| Cold calls in a loop | Start `--serve` first |
| `CERTIFICATE_VERIFY_FAILED` (Zscaler VPN) | `laya-ask` loads `~/Desktop/laya/bundle.pem` automatically; for raw `laya`, export `SSL_CERT_FILE` to that file |
| Server 500 "inference failed" | The routed checkpoint isn't loaded or downloaded. Pass `--model`, or restart `--serve` (it loads english and multilingual). |
