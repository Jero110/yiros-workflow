# book-sources

Shared data and tools for the `book-*` skills. Not a skill itself (no `SKILL.md`).

- `sources.json`: per book slug, the title, author, local PDF path (`~/books-src/<slug>.pdf`, outside the repo), PDF page count and whether the PDF has an outline. Read-only for the book skills.
- `pages.py <slug> <from> <to>`: prints the text of PDF pages `from..to` (1-based, inclusive). Use it to read past a skill's summary into the actual book.
- `verify_pages.py <skill-dir>`: checks every `## <Section> (PDF pp. a–b)` heading in `<skill-dir>/chapters/*.md` against the PDF. Exits 0 when at least 95% of the citations match.

Both scripts need `pypdf`:

```bash
uv run --with pypdf python3 -I home/.agents/skills/book-sources/pages.py book-ddia 174 176
uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-ddia
```

Page numbers are PDF page indexes. Each book skill's `meta.json` has `printed_offset` (printed page = PDF page − offset).
