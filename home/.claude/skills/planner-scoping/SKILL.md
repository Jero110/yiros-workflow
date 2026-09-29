---
name: planner-scoping
description: Use only from inside `planner`'s Step 1, when the user picks "brainstorm" over "grilling". Explores intent, requirements, and design for a multi-subtask run, ending in a written spec — then hands off to `planner`'s own Step 2, never to `writing-plans`. Do not invoke standalone; use `superpowers:brainstorming` for that.
---

# Planner Scoping (brainstorm path)

Forked from `superpowers:brainstorming`, for one reason: that skill's own hard gate says its *only* architectural-path exit is `writing-plans` — a single-session step-by-step implementation plan. `planner` needs a different terminal state: a scoped spec handed to its own Step 2 (independence check), which produces per-subtask dispatch contracts, not implementation steps. Same questioning process, different destination.

Help turn the idea into a fully formed spec through natural collaborative dialogue — same rigor as `superpowers:brainstorming`, same three-path classification, same approval gates. The only thing forked is where it lands at the end.

<HARD-GATE>
Do NOT invoke `writing-plans`, do NOT write any code, do NOT scaffold a project, and do NOT take any implementation action from inside this skill. The only next step out of here, ever, is back to `planner`'s Step 2. This applies to EVERY path below.
</HARD-GATE>

## Three Paths

Before your first question, classify the request and say the classification out loud — "this looks bounded, so I'll present a short design here rather than write a spec" — so your human partner can override it:

- **Spike** — a feasibility question whose output is an answer, not a multi-subtask run. If a request turns out to be this simple, that's a sign `planner` wasn't the right skill to begin with — say so and drop back to just answering the question, no dispatch plan needed.
- **Bounded** — a well-scoped change to code that already exists in this repo, with an existing flow to modify. Ask the clarifying questions that matter, present a short design in chat, get approval. If it's genuinely this small and doesn't split into 2+ independent subtasks, that's also a sign this didn't need `planner` — flag it and let the user decide whether to just do it directly instead.
- **Architectural** — new projects, new subsystems, changes that restructure how components fit together. This is the expected path for most `planner` runs, since a fresh multi-subtask build is exactly what lands here. Follow the full process: questions, approaches, sectioned design, written spec — then **return to `planner` Step 2**, not `writing-plans`.

When in doubt between two paths, take the heavier one. The ratchet is one-way: hidden complexity discovered mid-task upgrades the path — stop, say so, and step up. Nothing downgrades mid-task.

## Anti-Pattern: "Too Simple To Need Approval"

Every path ends with your human partner approving your intent before you hand off to `planner` Step 2. The design may be two sentences in chat, but you MUST present it and get approval first.

## Checklist

Classify first, announce the path, then complete each item in order.

**Spike:** present the question, get a nod, investigate cheaply, report a recommendation — then tell the user this didn't need `planner` after all.

**Bounded:** explore project context → ask clarifying questions one at a time → present short design in chat → get explicit approval → hand off to `planner` Step 2 if it still turns out to have 2+ independent subtasks; otherwise flag that `planner` wasn't needed.

**Architectural:**
1. **Explore project context** — check files, docs, recent commits
2. **Ask clarifying questions** — one at a time, understand purpose/constraints/success criteria
3. **Propose 2-3 approaches** — with trade-offs and your recommendation
4. **Present design** — in sections scaled to their complexity, get user approval after each section
5. **Write design doc** — save to `docs/planner/specs/YYYY-MM-DD-<topic>-design.md` (user preference for spec location overrides this default) and commit
6. **Spec self-review** — placeholder scan, internal consistency, scope check, ambiguity check; fix inline
7. **User reviews written spec** — ask user to review the spec file before proceeding
8. **Hand off to `planner` Step 2** — independence check, using this spec as the source of subtask boundaries. Do NOT invoke `writing-plans` or any implementation skill.

## The Process

**Understanding the idea:**

- Check out the current project state first (files, docs, recent commits)
- Before asking detailed questions, assess scope: if the request describes multiple independent subsystems, flag this immediately — this is exactly the shape `planner` exists for, so keep going rather than treating it as a reason to decompose further at this stage. `planner`'s own Step 2 is where subtask boundaries get formalized.
- Ask questions one at a time to refine the idea
- Prefer multiple choice questions when possible, but open-ended is fine too
- Only one question per message — if a topic needs more exploration, break it into multiple questions
- Focus on understanding: purpose, constraints, success criteria

**Exploring approaches:**

- Propose 2-3 different approaches with trade-offs
- Present options conversationally with your recommendation and reasoning
- Lead with your recommended option and explain why
- YAGNI ruthlessly — remove unnecessary features from every approach and design

**Presenting the design:**

- Once you believe you understand what you're building, present the design
- Scale each section to its complexity: a few sentences if straightforward, up to 200-300 words if nuanced
- Ask after each section whether it looks right so far
- Cover: architecture, components, data flow, error handling, testing
- Be ready to go back and clarify if something doesn't make sense

**Design for isolation and clarity:**

- Break the system into smaller units that each have one clear purpose, communicate through well-defined interfaces, and can be understood and tested independently — this maps directly onto `planner` Step 2's independence check, so keep it in mind while designing, not just while planning dispatch
- For each unit: what does it do, how do you use it, what does it depend on?
- Can someone understand what a unit does without reading its internals? If not, the boundaries need work — and they'll need work again when `planner` tries to turn them into subtask contracts.

## After the Design

**Documentation:**

- Write the validated design (spec) to `docs/planner/specs/YYYY-MM-DD-<topic>-design.md`
- Commit the design document to git

**Spec Self-Review:**

1. **Placeholder scan:** any "TBD", "TODO", incomplete sections, or vague requirements? Fix them.
2. **Internal consistency:** do any sections contradict each other?
3. **Scope check:** does this decompose cleanly into independent subtasks, or is it actually one tightly-coupled unit? If the latter, flag it — `planner`'s own "When NOT to Use" gate may mean this doesn't need dispatch at all.
4. **Ambiguity check:** could any requirement be interpreted two different ways? If so, pick one and make it explicit.

Fix any issues inline. No need to re-review — just fix and move on.

**User Review Gate:**

> "Spec written and committed to `<path>`. Please review it and let me know if you want changes before I continue into `planner`'s subtask planning."

Wait for the user's response. If they request changes, make them and re-run the spec review loop. Only proceed once the user approves.

**Hand-off:**

- Return control to `planner` Step 2 (independence check) using this spec as the scope reference.
- Do NOT invoke `writing-plans`. Do NOT invoke any implementation skill. The next artifact is `planner`'s own dispatch plan (`docs/planner/plans/YYYY-MM-DD-<project>.md`), not an implementation plan document.

## Red Flags

- Invoking `writing-plans` from inside this skill → that skill produces a single-session implementation plan; `planner` needs per-subtask dispatch contracts instead. Always hand off to `planner` Step 2.
- Treating "spec written" as the finish line → the finish line is `planner`'s dispatch plan; the spec is an input to Step 2, not the deliverable.
- Skipping the user review gate on the spec because the design "felt" approved during presentation → the written spec still needs its own explicit review pass.
