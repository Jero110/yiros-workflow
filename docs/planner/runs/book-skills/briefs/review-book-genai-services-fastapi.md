# Review brief: book-genai-services-fastapi (tier: fast_ai)

You are an independent reviewer (load the `reviewer` skill if available). Read-only: do NOT edit any file. Report only.

Worker output to review: worktree `/Users/jeronimo.deli/workflow/.worktrees/book-genai-services-fastapi`, files `home/.agents/skills/book-genai-services-fastapi/` and symlink `home/.claude/skills/book-genai-services-fastapi`. The worker's own report: `/Users/jeronimo.deli/workflow/.worktrees/book-genai-services-fastapi/REPORT.md`. Its task brief: `/Users/jeronimo.deli/workflow/docs/planner/runs/book-skills/briefs/book-genai-services-fastapi.md`. The PDF: `~/books-src/book-genai-services-fastapi.pdf` (never load it whole).

Run from the worktree root (Python only via uv; never pip/bare python):
1. `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-genai-services-fastapi` → must exit 0 (≥95%).
2. Budgets: `wc -w home/.agents/skills/book-genai-services-fastapi/SKILL.md` ≤ ~3,000 words; each `chapters/*.md` ≤ ~900 words unless clearly denser. `readlink home/.claude/skills/book-genai-services-fastapi` = `../../.agents/skills/book-genai-services-fastapi`. `meta.json` has `printed_offset` and the extraction mode. `git status` shows no commits beyond the base, and no PDFs or full-text dumps in the repo.
3. Grounding (most important): pick 3 retrieval questions of your own (not the worker's) that a user might ask ("where does the book explain X?"). Answer each only from the skill (SKILL.md → the right chapter file), then confirm the cited range with `uv run --with pypdf python3 -I home/.agents/skills/book-sources/pages.py book-genai-services-fastapi <a> <b>`: the claim must be in those pages. Also spot-check 5 specific claims (numbers, names, definitions) from random chapter files against the cited pages; flag anything not supported by the book text (invented content is a blocker).
4. Check that the brief's book-specific asks are met (e.g. patterns.md index, reference files, snippets, skipped appendices).

End your turn with a plain-text report:
VERDICT: PASS | PASS_WITH_NITS | FAIL
RETRIEVAL: your 3 questions, the cited ranges, confirmed yes/no
SPOT-CHECKS: 5 claims, supported yes/no
FINDINGS: numbered, severity (blocker/major/minor), file:line, evidence, suggested fix.
