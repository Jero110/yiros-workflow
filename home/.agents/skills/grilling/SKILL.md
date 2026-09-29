---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **interactive single-question rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Choose the single highest-leverage frontier question, ask only that one, give your recommended answer, then wait for the user's answer before asking the next question. Do **not** dump the whole frontier at once unless the user explicitly asks for a batch.

Format each turn like so:

```
**Q<n> - <question title>**
<question body, concise, with options if useful>

Recommended: <your recommended answer>
```

After each answer, reshape the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next highest-leverage single question. A question whose answer depends on another question still open belongs to a later turn, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
