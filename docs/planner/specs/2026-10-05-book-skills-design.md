# Book skills — Design Spec

**Date:** 2026-10-05
**Status:** draft, pending user review

## Goal

Turn 16 technical books (AI, agents, ML, system design) into agent skills that give cutting-edge context on how to design and execute systems, with **traceable answers**: every claim an agent makes from a book must be citable as book + chapter + section + PDF pages, so architectures are not invented and the user can go read the source and learn.

Skills must be **lean and usable**: no full book is ever loaded into context.

## Approach (user-chosen)

1. **Phase 1 (this run):** one skill per book, produced with `virgiliojr94/book-to-skill` as the extractor, run as designed (technical mode / Docling). Then a traceability layer is added on top.
2. **Phase 2 (planned separately, after Phase 1):** given the 16 per-book skills, decide with the user how many thematic skills to keep or merge, and how. Not part of this run.

## Hard constraints (user decisions)

- Per-book skills first; reduce later based on the output.
- Citations at **section level with page ranges**, using the **PDF page number** (easiest to verify). The offset to printed pages is recorded per book (`printed = pdf - offset`).
- Lean: a skill never loads a whole book. Chapter files load on demand.
- Skills live inside this repo (`home/.agents/skills/<slug>/`, symlinked from `home/.claude/skills/<slug>`). The user will make the repo private.
- Source PDFs stay **outside the repo** in a stable local folder (`~/books-src/`).
- Workers run on Opus. Python via `uv` (never `pip`, `python`, `python3` bare, or `conda`; run scripts with `uv run python3 -I`).
- Out of scope: Generative AI Solutions on Google Cloud, The Hundred-Page ML Book, Cpp Software Design.

## Books (16)

Download URL pattern (public, no auth): `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t`

| Slug | Title | Drive ID / path | Outline in PDF |
|---|---|---|---|
| book-ddia | Designing Data-Intensive Applications (Kleppmann) | 1fIdC6c7ovRb16hrjuGKNue6yf4h3WVHe | yes |
| book-philosophy-software-design | A Philosophy of Software Design (Ousterhout) | 17PkwmFBdwbNXZqDOc5QaU2rfkTctZdRp | yes |
| book-building-microservices | Building Microservices, 2nd ed. (Newman) | `~/Desktop/Building Microservices Designing Fine-Grained Systems 2nd By Sam Newman.pdf` (also now in Drive System Design/General) | check |
| book-data-eng-design-patterns | Data Engineering Design Patterns (2025) | 1C9THorBpVAKM737XE6BKuimZlUCEYGbJ | yes |
| book-mastering-api-architecture | Mastering API Architecture | 1FrWMP23OGzZZ-TwDLsWTN72GDrR2yP6J | yes |
| book-genai-services-fastapi | Building Generative AI Services with FastAPI | 1n1OGUd3hv7nGe32T3lOoNtk3khZWVJZM | yes |
| book-ai-engineering | AI Engineering (Huyen) | 1jTN5B6JSHY1-BJVoTr_MMvLjsTEUHP8F | yes (1108 pp) |
| book-genai-design-patterns | Generative AI Design Patterns | 1pRfQVMbG3_UfjeOqAvgei_EsdhcA01At | yes |
| book-hands-on-llms | Hands-On Large Language Models (Alammar) | 1Y0OqKsle6Xjno6OTmODjGJGZ457NFGah | yes |
| book-agentic-design-patterns | Agentic Design Patterns (Gulli) | 1fLqr9M74EtUbmnElBgf3GjesDSPSF-2d | **no** (use the book's own TOC page + page counts) |
| book-building-ai-agents | Building Applications with AI Agents | 1prw3gVaUxRdHhM_bO7WIb28DSvNqSu1i | yes |
| book-hands-on-ml | Hands-On Machine Learning (Géron) | 1pevOX-xV36ih3iD-I5FCa41-tqjz3RNf | yes |
| book-ml-design-patterns | Machine Learning Design Patterns | 1frtkoC8fQTTLD6msxbQDti0HHNDM3dOI | yes |
| book-designing-ml-systems | Designing Machine Learning Systems (Huyen) | 1729N5cFXij5hFcK1mGYxTheTcBGPTxx1 | yes |
| book-practical-mlops | Practical MLOps | 1-qNjrzgpSl9c1QqiA6X9RfIbdXRdzHzE | yes |
| book-ml-engineering-python | Machine Learning Engineering with Python | 1K3D7DYoj9R7QorXOk63PvzcISYZ1DxJU | yes |

## Components

### 1. Shared foundation (built first, in the primary checkout, before any worker)

- Install `book-to-skill` (`npx skills add virgiliojr94/book-to-skill` or clone) into `home/.agents/skills/book-to-skill/`, symlink into `home/.claude/skills/`. Run its `--check` to see which extractors are available (pdftotext, Docling).
- `~/books-src/`: all 16 PDFs, named `<slug>.pdf`.
- `home/.agents/skills/book-sources/` (not a skill to trigger; shared data + tools), containing:
  - `sources.json`: per slug → title, author, local path, page count, outline status. Written once by the foundation and read-only for workers (avoids merge conflicts). The per-book `printed_offset` lives in each skill's own `<slug>/meta.json`, written by that book's worker.
  - `pages.py <slug> <from> <to>`: prints text of PDF pages `from..to` of that book (reads `~/books-src/<slug>.pdf` via `sources.json`). This is how an agent gets detail without loading the book.
  - `verify_pages.py <skill-dir>`: for every cited section range in the skill's chapter files, extracts those PDF pages and checks the section title appears within the range; prints pass/fail per citation and an overall pass rate.
- Per-book worker contracts depend on these, so they are not parallelized with the workers.

### 2. Per-book skill (one worker per book, Opus)

- Run `book-to-skill` on `~/books-src/<slug>.pdf` with name `<slug>`, technical mode. Output: `SKILL.md` (~4k tokens), `chapters/chNN-*.md` (~1k tokens each), `glossary.md`, `patterns.md`, `cheatsheet.md`.
- **Traceability layer** added by the same worker:
  - Every chapter file begins with `Source: <slug> · ch N · PDF pp. a–b` (printed = pdf − offset from `sources.json`).
  - Every section heading in a chapter file carries its range: `## <Section title> (PDF pp. a–b)`.
  - `SKILL.md` has a chapter index with the same ranges and a short "how to cite and how to read more" note pointing to `pages.py`.
  - Page ranges come from the PDF outline (`pypdf`); for Agentic Design Patterns, from the book's TOC page and per-chapter page counts, confirmed by heading search.
- Lean budget: `SKILL.md` ≤ ~4k tokens, each chapter file ≤ ~1.2k tokens unless the chapter is clearly denser. No long raw passages (book-to-skill rule).

### 3. Reviewer

Independent review of each completed book skill against this spec: run `verify_pages.py`, check token budgets, and ask 3 retrieval questions per book ("where does the book explain X?") answered from the skill with citations that must verify against the PDF.

## Success criteria per book

- `verify_pages.py` pass rate ≥ 95% (failures listed and explained).
- Budgets met.
- 3/3 retrieval questions answered with a verifiable citation.
- Skill is symlinked into `home/.claude/skills/` and appears as a skill.

## Checkpoint (end of Phase 1)

The executor stops after all 16 and reports per book: token sizes, chapter count, verify pass rate, retrieval results, overlaps with other books (RAG, MLOps, evaluation), and any problems. **No consolidation happens in this run.** The user and planner decide Phase 2 from that report.

## Risks

- Docling is slow (~1.5 s/page; AI Engineering is 1108 pages) and CPU heavy: run a small number of workers at a time with long timeouts, in the background.
- A PDF that fails extraction (scanned, corrupt) is reported, not worked around by inventing content.
- Books are copyrighted; the repo must be private before pushing. `scripts/check-public.sh` and the `public-safety` workflow may flag the new files once the repo is private; the worker should not weaken them, only report.
- No PDFs or full-text copies go into the repo.

## Out of scope

Thematic consolidation (Phase 2), Google Cloud / Hundred-Page / C++ books, a search index service, and editing the user's other skills.
