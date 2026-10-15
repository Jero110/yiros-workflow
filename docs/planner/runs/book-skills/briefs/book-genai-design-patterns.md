# Brief: book-genai-design-patterns

## Subtask: book-genai-design-patterns
**Mechanism:** pane
**Harness:** claude-code
**Model:** sonnet (executor override: user asked for a lighter model than Opus)
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-genai-design-patterns/` exists for "Generative AI Design Patterns" (Lakshmanan and Hapke, 694 pp, `~/books-src/book-genai-design-patterns.pdf`, outline with 10 chapters: controlling content style, adding knowledge (two chapters), extending model capabilities, improving reliability, enabling agents to take action, addressing constraints, setting safeguards, composable agentic workflows), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Each pattern is a section, so the per-section ranges are the point; keep a `patterns.md` index listing every pattern with its range.
Constraints: only touch `home/.agents/skills/book-genai-design-patterns/` and `home/.claude/skills/book-genai-design-patterns`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-genai-design-patterns` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Common worker contract (applies to each Subtask below; each subtask repeats what it needs)

Procedure for the worker, in its own worktree, for its one book:
1. Run `book-to-skill` on `~/books-src/<slug>.pdf` with skill name `<slug>`, technical mode, output root = `<worktree>/home/.agents/skills` (not the live `~/.agents/skills`); skip its automatic `~/.claude` symlink and instead create the relative symlink `home/.claude/skills/<slug>` → `../../.agents/skills/<slug>` inside the worktree. Docling runs for minutes: run it in the background with long timeouts.
2. Traceability layer: add `Source: <slug> · ch N · PDF pp. a–b` at the top of every chapter file and `## <Section title> (PDF pp. a–b)` to every section; add the chapter index with ranges and a short "how to cite / read more with `pages.py`" note to `SKILL.md`; write `<slug>/meta.json` with `printed_offset` (printed page = PDF page − offset; find it by comparing a known printed page number to its PDF index) and the extraction mode used.
3. Budgets: `SKILL.md` ≤ ~4k tokens (~3,000 words), chapter files ≤ ~1.2k tokens (~900 words) unless clearly denser; no long raw passages.
4. Run `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/<slug>`; fix until pass rate ≥ 95% or list unresolved failures honestly.
5. Report to the executor: token sizes, chapter count, pass rate, 3 retrieval questions with their cited answers, overlaps noticed with other books, and any problems. Do not commit or push.

---

## Executor run notes (environment facts; the contract above still binds)

- You are worker `book-genai-design-patterns` (cmux surface:107). Use the `worker` skill for the report contract (REPORT.md + one-line `cmux notify`; stay in session afterwards). Peers: book-ai-engineering=surface:105, book-ddia=surface:106, book-genai-design-patterns=surface:107, book-genai-services-fastapi=surface:108 (executor=surface:95). Cross-worker messages must start with `[worker <name> asks]`; questions only, never file access.
- Your worktree: `/Users/jeronimo.deli/workflow/.worktrees/book-genai-design-patterns` (branch `book-genai-design-patterns`). Work only there. Do not commit or push anything.
- `home/.agents/skills/book-sources` and `home/.agents/skills/book-to-skill` in your worktree are **symlinks to the shared foundation in the primary checkout** (not committed, by user instruction). Use them; never edit, move or delete them. If `verify_pages.py` itself looks wrong, tell the executor (NEEDS_CONTEXT or CONCERN), do not patch it.
- book-to-skill: read `home/.agents/skills/book-to-skill/SKILL.md` and follow it non-interactively with these answers: Full Conversion; BOOK_TYPE=technical; DEPTH=reference; skill name `book-genai-design-patterns`; SKILLS_HOME=`/Users/jeronimo.deli/workflow/.worktrees/book-genai-design-patterns/home/.agents/skills`; skip its `~/.claude/skills` symlink step (make the relative repo symlink from the contract instead); skip the publish-to-GitHub step; do not stop at its cost-estimate confirmation, proceed. The plan's budgets (SKILL.md ≤ ~4k tokens, chapter files ≤ ~1.2k) override book-to-skill's defaults.
- Extraction: run `~/books-src/.tools/extract.sh ~/books-src/book-genai-design-patterns.pdf ~/books-src/.work/book-genai-design-patterns` in the background (redirect to `~/books-src/.work/book-genai-design-patterns.log`). It wraps book-to-skill's `scripts/extract.py --mode technical` with a CA bundle for this machine's Zscaler TLS proxy; without it Docling cannot fetch its models and silently falls back to pdftotext. Docling models are already cached. Confirm `~/books-src/.work/book-genai-design-patterns/metadata.json` says `"extraction_method": "docling"`. If Docling crashes or takes > ~75 min on this book, `B2S_MODE=text ~/books-src/.tools/extract.sh ...` is the fallback; record the mode actually used in `meta.json` and as a CONCERN.
- Keep `full_text.txt`, helper scripts and scratch files under `~/books-src/.work/book-genai-design-patterns/`, never in the repo. Python only via `uv run [--with pypdf] python3 -I <script>`.
- Page ranges: read the PDF outline with pypdf (`reader.outline`, `reader.get_destination_page_number(...) + 1` = 1-based PDF page). `sources.json` has page counts and outline status.
- REPORT.md goes at `/Users/jeronimo.deli/workflow/.worktrees/book-genai-design-patterns/REPORT.md` and must include the items from step 5 of the Common worker contract (token sizes, chapter count, pass rate with the verify output, 3 retrieval questions with cited answers confirmed by `pages.py`, overlaps, problems). Also end your final turn with the same report as plain text.
- First, reply exactly: ACK book-genai-design-patterns
