# Brief: book-hands-on-ml

## Subtask: book-hands-on-ml
**Mechanism:** pane
**Harness:** claude-code
**Model:** sonnet (executor override: user asked for a lighter model than Opus)
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-hands-on-ml/` exists for "Hands-On Machine Learning with Scikit-Learn, Keras and TensorFlow" (Géron, 510 pp, `~/books-src/book-hands-on-ml.pdf`; outline has Part I fundamentals, chapters 1–9, and Part II neural networks and deep learning), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Cover **all** chapters present in the PDF (user said consider everything for now); if the PDF holds fewer chapters than the full book, record the actual last chapter in `meta.json`.
Constraints: only touch `home/.agents/skills/book-hands-on-ml/` and `home/.claude/skills/book-hands-on-ml`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-hands-on-ml` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
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

- You are worker `book-hands-on-ml` (cmux surface:120). Use the `worker` skill for the report contract (REPORT.md + one-line `cmux notify`; stay in session afterwards). Peers: book-ddia=surface:106, book-genai-services-fastapi=surface:108, book-hands-on-llms=surface:112, book-building-microservices=surface:116 (executor=surface:95). Cross-worker messages must start with `[worker <name> asks]`; questions only, never file access.
- Your worktree: `/Users/jeronimo.deli/workflow/.worktrees/book-hands-on-ml` (branch `book-hands-on-ml`). Work only there. Do not commit or push anything.
- `home/.agents/skills/book-sources` and `home/.agents/skills/book-to-skill` in your worktree are **symlinks to the shared foundation in the primary checkout** (not committed, by user instruction). Use them; never edit, move or delete them. If `verify_pages.py` itself looks wrong, tell the executor (NEEDS_CONTEXT or CONCERN), do not patch it.
- book-to-skill: read `home/.agents/skills/book-to-skill/SKILL.md` and follow it non-interactively with these answers: Full Conversion; BOOK_TYPE=technical; DEPTH=reference; skill name `book-hands-on-ml`; SKILLS_HOME=`/Users/jeronimo.deli/workflow/.worktrees/book-hands-on-ml/home/.agents/skills`; skip its `~/.claude/skills` symlink step (make the relative repo symlink from the contract instead); skip the publish-to-GitHub step; do not stop at its cost-estimate confirmation, proceed. The plan's budgets (SKILL.md ≤ ~4k tokens, chapter files ≤ ~1.2k) override book-to-skill's defaults.
- Extraction: run `~/books-src/.tools/extract.sh ~/books-src/book-hands-on-ml.pdf ~/books-src/.work/book-hands-on-ml` in the background (redirect to `~/books-src/.work/book-hands-on-ml.log`). It wraps book-to-skill's `scripts/extract.py --mode technical` with a CA bundle for this machine's Zscaler TLS proxy; without it Docling cannot fetch its models and silently falls back to pdftotext. Docling models are already cached. Confirm `~/books-src/.work/book-hands-on-ml/metadata.json` says `"extraction_method": "docling"`. If Docling crashes or takes > ~75 min on this book, `B2S_MODE=text ~/books-src/.tools/extract.sh ...` is the fallback; record the mode actually used in `meta.json` and as a CONCERN.
- Keep `full_text.txt`, helper scripts and scratch files under `~/books-src/.work/book-hands-on-ml/`, never in the repo. Python only via `uv run [--with pypdf] python3 -I <script>`.
- Page ranges: read the PDF outline with pypdf (`reader.outline`, `reader.get_destination_page_number(...) + 1` = 1-based PDF page). `sources.json` has page counts and outline status.
- REPORT.md goes at `/Users/jeronimo.deli/workflow/.worktrees/book-hands-on-ml/REPORT.md` and must include the items from step 5 of the Common worker contract (token sizes, chapter count, pass rate with the verify output, 3 retrieval questions with cited answers confirmed by `pages.py`, overlaps, problems). Also end your final turn with the same report as plain text.
- Write chapter content from the extracted book text (Docling full_text.txt read in chunks, or pages.py for a range), never from memory of the book. Every claim, number and example must be traceable to the cited pages.
- Keep scratch files under ~/books-src/.work/book-hands-on-ml/ only (never under .worktrees/ or elsewhere in the repo).
- First, reply exactly: ACK book-hands-on-ml
