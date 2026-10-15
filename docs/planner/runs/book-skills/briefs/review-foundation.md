# Review brief: book-skills foundation tooling (tier: deep_ai)

You are an independent reviewer (load the `reviewer` skill if available). Read-only: do NOT edit any file. Report findings only.

Context: 16 per-book agent skills are being generated from PDFs. Every book's pass/fail depends on this shared tooling, so review it adversarially.

Files under review (primary checkout /Users/jeronimo.deli/workflow, uncommitted by design):
- home/.agents/skills/book-sources/pages.py
- home/.agents/skills/book-sources/verify_pages.py
- home/.agents/skills/book-sources/sources.json
- home/.agents/skills/book-sources/README.md
- ~/books-src/.tools/extract.sh (machine-local wrapper around book-to-skill's extractor; adds a CA bundle for a Zscaler TLS proxy)

Spec (what they must do), from docs/planner/plans/2026-10-05-book-skills.md "Shared foundation":
- pages.py <slug> <from> <to>: prints text of PDF pages from..to (1-based, inclusive), path from sources.json; errors clearly on bad slug/range.
- verify_pages.py <skill-dir>: parses every `## <Section> (PDF pp. a–b)` heading in chapters/*.md, extracts PDF pages a..b, checks the section title (normalized, fuzzy tolerant of hyphenation and case) appears in that range; pass/fail per citation + overall pass rate; exit 0 only if rate >= 95%. Must normalize whitespace (one PDF, book-agentic-design-patterns, extracts one word per line).
- Both use pypdf via `uv run --with pypdf python3 -I`.

Check especially: false PASSes (title too short/generic such as "Summary" or "Introduction" passing anywhere; fuzzy threshold too loose; numbering-stripping variants too permissive), false FAILs (en dash vs hyphen, `p.` vs `pp.`, headings with markdown/links/code, curly quotes, ligatures), regex edge cases, off-by-one page handling, exit codes, performance on a 1108-page book. Run the scripts yourself, e.g.:
  cd /Users/jeronimo.deli/workflow && uv run --with pypdf python3 -I home/.agents/skills/book-sources/pages.py book-ddia 25 26
  Build small fixtures under /tmp (a dir named after a slug, with chapters/*.md) and run verify_pages.py on them. PDFs are in ~/books-src/<slug>.pdf. Outline helper: pypdf reader.outline.
Python only via `uv run ... python3 -I`; never pip/bare python.

End your turn with a plain-text report:
VERDICT: PASS | PASS_WITH_NITS | FAIL
FINDINGS: numbered, each with severity (blocker/major/minor), file:line, concrete failing input, and suggested fix.
