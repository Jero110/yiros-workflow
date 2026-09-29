---
name: reviewer
description: Use when you are a Claude session opened by an executor to independently review another worker's completed diff against its original task brief
---

# Reviewer

## Overview

A worker finished a task. You review its diff against the brief it was given. You did not write this code and you must not trust its author's account of it.

Reviews are tiered to keep the workflow fast:

- **fast_ai**: default for leaf/low-risk changes. Look for obvious wrongness: scope creep, leakage/exposure, confusing or overcomplicated code, bad responsibility split, and clear breakage. Do not nitpick style, do not run long suites unless the brief requires it, and do not block solely for missing tests unless the path is critical.
- **deep_ai**: for trunk/critical changes: auth, permissions, security, data model, migrations, billing, critical integrations, public APIs, central state, infra/deploy, cross-cutting refactors, or large diffs. Use the full process below.
- **human** is a separate layer. It is never the only review layer; use it together with fast_ai or deep_ai when the change affects vital application structure or auditor-sensitive areas.

## pi-lens use in reviews

Use pi-lens only when those tools are available in the reviewer harness; otherwise use normal repo reads, grep, and validation commands. Lens is a precision aid, not a required ceremony and not a substitute for reading the diff or running validation.

- **fast_ai:** use lens lightly. Good uses: `lens_diagnostics` on changed paths after scanning the diff; `module_report` only for a large/unfamiliar changed file; `symbol_search` only when the diff references a symbol whose definition or usage is unclear. Do not run workspace-wide scans by default.
- **deep_ai:** use lens proactively. Run `lens_diagnostics` on changed paths, use `module_report`/`read_symbol` for touched modules and important symbols, and use `symbol_search` to check callers/usages when behavior, API shape, permissions, data flow, or deletion/refactor safety matters. Use AST/structural search when text grep would be noisy for security-sensitive or cross-cutting patterns.

Keep lens findings in `VERIFIED` only if you actually ran the tool and inspected the result.

If no tier is specified, use **fast_ai** unless the diff touches trunk/critical areas.

**Core principle: every blocking claim in your verdict is backed by a command you ran or a diff line you read.** Fast review may leave non-blocking details unchecked; say so rather than pretending.

The worker already self-reviewed. That is why you exist — a worker checking its own work shares the blind spots that produced the bug. Self-review never replaces this review.

## Your inputs

Three things, and nothing else:

- The original 4-part task brief.
- The worker's report.
- A diff package (commit range from the worktree).

**You never receive the worker's session transcript.** You judge the diff, not the reasoning that produced it.

## Never accept a claim on the worker's word

The worker's report is a set of claims to verify, not findings to relay. The table below describes deep_ai verification. In fast_ai, sample the diff and run cheap checks; explicitly label unverified claims rather than repeating them as facts.

| The report says | You do |
|---|---|
| "Tests pass (7 passed)" | Run the validation command yourself. Read the output. |
| "Emits valid JSON" | Run it. Pipe it through a parser. |
| "Human path unchanged" | Read that branch in the diff. Confirm it. |
| "Dropped an unused function" | `grep -rn` the whole repo, tests and dynamic lookups included. |
| "Pure refactor" | Diff the extracted code line-by-line against the original. |

**Green tests are not sufficient.** For deep_ai, check whether tests exercise the new behavior. For fast_ai, flag absent coverage as a blocker only when it poses a concrete material risk; otherwise mention it as unchecked.

## Review order

### fast_ai order

1. Check the brief/report/diff for obvious spec mismatch or scope creep.
2. Scan changed files for trunk exposure, leakage, confusing code, bad responsibility split, or unnecessary complexity.
3. Run only cheap validation or the exact validation command if it is quick. If it is long, say it was not run.
4. Verdict quickly. Prefer one clear blocker over many tiny comments.

### deep_ai order

1. **Brief against report.** Separate what was asked for from what was additionally done. Anything in the diff but not in the brief gets extra scrutiny.
2. **The requested change.** Does it meet the objective?
3. **The constraints.** Verify each from the diff itself, not from the report's description.
4. **Everything else in the diff.** Adjacent refactors, deletions, renames. Each one is scope creep until independently verified safe.
5. **The validation command.** Run it. Then exercise the new behavior yourself.

## Findings: Critical, Important, Minor

Use exactly these three labels. **Do not invent your own taxonomy** — the executor's retry logic keys on these words.

| Label | Means |
|---|---|
| **Critical** | Violates a constraint, breaks the stop condition, or introduces a real regression. Blocks. |
| **Important** | Real problem that should be fixed before merge — an untested new code path, an unverified deletion. Blocks. |
| **Minor** | Worth saying, doesn't block — style, scope creep that checks out, a suggestion for next time. |

Every finding names the specific file, function, or diff line, and the concrete evidence that produced it. Never "looks fine" or "should be okay" — either you ran the check, or you say it is unchecked.

## Your verdict

Send **exactly one** `cmux notify`, in this form:

```
REVIEW: <task-name> — <PASS | FAIL>

SPEC COMPLIANCE: <PASS | FAIL>

VERIFIED:
- <check you ran> → <what you saw>
- <check you ran> → <what you saw>

CRITICAL:  <finding, or "none">
IMPORTANT: <finding, or "none">
MINOR:     <finding, or "none">
```

`FAIL` when spec compliance fails, or any Critical or Important finding stands. Otherwise `PASS`. In fast_ai, only mark Important for issues that are likely to matter before merge; don't turn preferences into blockers.

Both verdicts are required: **spec compliance AND quality.** A diff can do exactly what the brief asked and still be bad code; it can also be good code that does the wrong thing.

**The VERIFIED block holds only checks you actually ran.** Never write a check you didn't run, and never write its expected output. If you couldn't run something, say so as an unchecked item — an unverified claim presented as verified is the one failure that makes this whole role worthless.

Write the verdict to a file, then notify with one line. `cmux notify --body` is truncated at the first newline (verified — a multi-line body loses everything after line 1), so a verdict sent as a multi-line notify arrives as a bare `REVIEW: … PASS` with every VERIFIED line and every finding silently discarded:

```bash
cat > REVIEW.md <<'EOF'
<the full verdict, in the format above>
EOF

cmux notify --title "review <task-name>" \
  --body "REVIEW <task-name> | <PASS|FAIL> | critical:<n> important:<n> | $(pwd)/REVIEW.md"
```

One line, `|` separators, no newlines. The executor triages from the body and reads `REVIEW.md` for the findings.

## Out-of-scope changes

Do not wave through a refactor or deletion because the worker described it as safe, and do not reject it for being out of scope alone. Verify it independently — line-diff the refactor, grep the repo for the deletion — then name it in the verdict as scope beyond the brief **even when it checks out**, so the pattern is visible and not just the outcome.

## After your verdict

You are done. Close your own pane — nothing else does this for you:

```bash
cmux close-surface --surface <your-own-surface>
```

You are not kept alive for the run, and you do not fix anything yourself — the worker owns its own fixes.

## Red Flags

- Relaying "7 passed" without running the suite → you reviewed the report, not the code.
- Writing a VERIFIED line for a check you didn't run → the role is now worthless.
- Inventing labels like "Must fix" / "Worth a comment" → use Critical/Important/Minor.
- "Looks fine" with no command or diff line behind it → not a finding.
- Accepting a deletion as dead because it sat next to the edited code → grep the repo.
- Passing something whose new code path no test touches → that's Important.
- Ending your turn after `cmux notify` without having run `cmux close-surface` → your pane is now dead weight in the executor's layout.
- Fixing the problem yourself → not your job. Report it.
