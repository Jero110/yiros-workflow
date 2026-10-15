# book-skills — Planner Plan

**Project name:** book-skills
**Planned:** 2026-10-05
**Spec:** `docs/planner/specs/2026-10-05-book-skills-design.md` (read it first; this plan only splits it into contracts)

## Goal
Turn 16 technical books into 16 lean per-book agent skills using `virgiliojr94/book-to-skill` as the extractor, each with verifiable section-level page citations (PDF page numbers). Phase 1 only: stop after the 16 and report. Thematic consolidation (Phase 2) is planned separately with the user.

## User decisions / hard constraints
- One skill per book first; reduce later from the output (Phase 2, not in this run).
- Use `book-to-skill` as designed (technical mode, Docling). Do not rewrite its extraction by hand.
- Citations at section level with PDF page ranges; printed-page offset recorded per book in that skill's `meta.json`.
- Lean: `SKILL.md` ≤ ~4k tokens, chapter files ≤ ~1.2k tokens. Never load a whole book into context.
- Skills live in the repo: `home/.agents/skills/<slug>/`, relative symlink `home/.claude/skills/<slug>` → `../../.agents/skills/<slug>`.
- PDFs live outside the repo in `~/books-src/<slug>.pdf`. No PDFs or full-text copies in the repo.
- All workers on Opus (Harness `claude-code`). Python only via `uv run python3 -I <script>`; never `pip`, bare `python`/`python3`, or `conda`.
- Out of scope: Generative AI Solutions on Google Cloud, Hundred-Page ML Book, Cpp Software Design.
- Do not commit or push. The repo will be made private by the user; the executor leaves work in worktrees and reports.

## Planner assumptions / flexible approach
- Run 3–4 workers at a time (Docling is CPU heavy, ~1.5 s/page). Executor may adjust the batch size.
- Order big books (AI Engineering 1108 pp, DDIA 613 pp, GenAI Design Patterns 694 pp, FastAPI 644 pp, Hands-On LLMs 598 pp) into the first batches so they finish while small ones run.
- If a book's PDF outline is missing or wrong, the worker builds ranges from the book's TOC page plus heading search.

## Scope
In:
- Shared foundation (below), 16 per-book skills, per-book review, final Phase 1 report.

Out:
- Merging or reducing skills, thematic cross-book skills, search index, editing other skills, git commits/pushes.

## Revisión humana / Human approval checklist
- [ ] The 16 books and slugs below are right (nothing missing, nothing extra).
- [ ] Opus for every worker is acceptable cost-wise (16 workers, several long Docling runs).
- [ ] Executor stops after Phase 1 and reports; no consolidation.
- [ ] Repo is made private before anything is pushed.

## Shared foundation (executor builds this directly in the primary checkout, before dispatching any worker)
1. Install `book-to-skill` into `home/.agents/skills/book-to-skill/` (clone `https://github.com/virgiliojr94/book-to-skill` or `npx skills add virgiliojr94/book-to-skill`), relative symlink in `home/.claude/skills/`. Run its `--check`; if Docling is missing, install it with `uv` in a project-local env, not globally. Record which extractors work.
2. Create `~/books-src/` and download the 16 PDFs as `<slug>.pdf` (public URL pattern: `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t`; the Building Microservices PDF is copied from `~/Desktop/Building Microservices Designing Fine-Grained Systems 2nd By Sam Newman.pdf`). Verify each is a valid PDF and has the expected page count (see table).
3. Create `home/.agents/skills/book-sources/` containing:
   - `sources.json`: per slug → title, author, local path (`~/books-src/<slug>.pdf`), page count, outline status.
   - `pages.py <slug> <from> <to>`: prints the text of PDF pages `from..to` (1-based, inclusive) of that book, reading the path from `sources.json`; errors clearly on bad slug/range.
   - `verify_pages.py <skill-dir>`: parses every `## <Section> (PDF pp. a–b)` heading in the skill's `chapters/*.md`, extracts PDF pages a..b, checks the section title (normalized, fuzzy tolerant of hyphenation and case) appears within that range; prints pass/fail per citation and an overall pass rate; exit code 0 only if pass rate ≥ 95%.
   - Both scripts use `pypdf` via `uv run --with pypdf python3 -I`.
4. Smoke test the foundation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/pages.py book-ddia 1 2` prints text; `verify_pages.py` runs on a tiny hand-made fixture.

Books (slug → Drive ID → pages): book-ddia 1fIdC6c7ovRb16hrjuGKNue6yf4h3WVHe (613); book-philosophy-software-design 17PkwmFBdwbNXZqDOc5QaU2rfkTctZdRp (188); book-building-microservices (Desktop PDF); book-data-eng-design-patterns 1C9THorBpVAKM737XE6BKuimZlUCEYGbJ (375); book-mastering-api-architecture 1FrWMP23OGzZZ-TwDLsWTN72GDrR2yP6J (289); book-genai-services-fastapi 1n1OGUd3hv7nGe32T3lOoNtk3khZWVJZM (644); book-ai-engineering 1jTN5B6JSHY1-BJVoTr_MMvLjsTEUHP8F (1108); book-genai-design-patterns 1pRfQVMbG3_UfjeOqAvgei_EsdhcA01At (694); book-hands-on-llms 1Y0OqKsle6Xjno6OTmODjGJGZ457NFGah (598); book-agentic-design-patterns 1fLqr9M74EtUbmnElBgf3GjesDSPSF-2d (482); book-building-ai-agents 1prw3gVaUxRdHhM_bO7WIb28DSvNqSu1i (355); book-hands-on-ml 1pevOX-xV36ih3iD-I5FCa41-tqjz3RNf (510); book-ml-design-patterns 1frtkoC8fQTTLD6msxbQDti0HHNDM3dOI (408); book-designing-ml-systems 1729N5cFXij5hFcK1mGYxTheTcBGPTxx1 (389); book-practical-mlops 1-qNjrzgpSl9c1QqiA6X9RfIbdXRdzHzE (461); book-ml-engineering-python 1K3D7DYoj9R7QorXOk63PvzcISYZ1DxJU (239).

## Review guidance
- Every book skill: validation-only (`verify_pages.py` + budgets) plus fast_ai review (3 retrieval questions with verifiable citations).
- Foundation tooling (`pages.py`, `verify_pages.py`): deep_ai review, because every book's pass/fail depends on it.
- Human: the final Phase 1 report.

## Common worker contract (applies to each Subtask below; each subtask repeats what it needs)

Procedure for the worker, in its own worktree, for its one book:
1. Run `book-to-skill` on `~/books-src/<slug>.pdf` with skill name `<slug>`, technical mode, output root = `<worktree>/home/.agents/skills` (not the live `~/.agents/skills`); skip its automatic `~/.claude` symlink and instead create the relative symlink `home/.claude/skills/<slug>` → `../../.agents/skills/<slug>` inside the worktree. Docling runs for minutes: run it in the background with long timeouts.
2. Traceability layer: add `Source: <slug> · ch N · PDF pp. a–b` at the top of every chapter file and `## <Section title> (PDF pp. a–b)` to every section; add the chapter index with ranges and a short "how to cite / read more with `pages.py`" note to `SKILL.md`; write `<slug>/meta.json` with `printed_offset` (printed page = PDF page − offset; find it by comparing a known printed page number to its PDF index) and the extraction mode used.
3. Budgets: `SKILL.md` ≤ ~4k tokens (~3,000 words), chapter files ≤ ~1.2k tokens (~900 words) unless clearly denser; no long raw passages.
4. Run `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/<slug>`; fix until pass rate ≥ 95% or list unresolved failures honestly.
5. Report to the executor: token sizes, chapter count, pass rate, 3 retrieval questions with their cited answers, overlaps noticed with other books, and any problems. Do not commit or push.

---

## Subtask: book-ddia
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-ddia/` exists as a book-to-skill output for "Designing Data-Intensive Applications" (Kleppmann, 613 pp, `~/books-src/book-ddia.pdf`, outline with Parts I–III and 12 chapters), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above.
Constraints: only touch `home/.agents/skills/book-ddia/` and `home/.claude/skills/book-ddia`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-ddia` exits 0 (pass rate ≥ 95%); `wc -w home/.agents/skills/book-ddia/SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations that `pages.py book-ddia <a> <b>` confirms.
Stop condition: validation passes, or after one honest fix iteration the remaining failures are listed in the report; report sent.
Cross-refs: none.

---

## Subtask: book-philosophy-software-design
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-philosophy-software-design/` exists for "A Philosophy of Software Design" (Ousterhout, 188 pp, `~/books-src/book-philosophy-software-design.pdf`, outline with 21 numbered chapters plus Summary of Design Principles and Summary of Red Flags), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Keep the two summary lists (principles, red flags) as their own reference files, since they are the book's most reusable content.
Constraints: only touch `home/.agents/skills/book-philosophy-software-design/` and `home/.claude/skills/book-philosophy-software-design`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-philosophy-software-design` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-building-microservices
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-building-microservices/` exists for "Building Microservices, 2nd edition" (Sam Newman, `~/books-src/book-building-microservices.pdf`, copied from Desktop), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. First check whether the PDF has an internal outline; if not, build ranges from the book's TOC page plus heading search and say so in `meta.json`.
Constraints: only touch `home/.agents/skills/book-building-microservices/` and `home/.claude/skills/book-building-microservices`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-building-microservices` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-data-eng-design-patterns
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-data-eng-design-patterns/` exists for "Data Engineering Design Patterns" (2025, 375 pp, `~/books-src/book-data-eng-design-patterns.pdf`, outline with chapters 1–10: ingestion, error management, idempotency, data value, data flow, security, storage, quality, observability, plus Appendix Summary of Patterns), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Keep the Appendix pattern summary as its own reference file.
Constraints: only touch `home/.agents/skills/book-data-eng-design-patterns/` and `home/.claude/skills/book-data-eng-design-patterns`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-data-eng-design-patterns` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-mastering-api-architecture
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-mastering-api-architecture/` exists for "Mastering API Architecture" (289 pp, `~/books-src/book-mastering-api-architecture.pdf`, 4 parts, 10 chapters: design/build/specify APIs, testing, API gateways, service mesh, deploying/releasing, threat modeling, authN/authZ, redesigning to API-driven architectures, evolving to cloud platforms), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above.
Constraints: only touch `home/.agents/skills/book-mastering-api-architecture/` and `home/.claude/skills/book-mastering-api-architecture`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-mastering-api-architecture` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-genai-services-fastapi
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-genai-services-fastapi/` exists for "Building Generative AI Services with FastAPI" (644 pp, `~/books-src/book-genai-services-fastapi.pdf`, 3 parts, 12 chapters: FastAPI, model serving, type-safe services, concurrency, real-time streaming, databases, auth, securing, optimizing, testing, deployment), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. This book is code-heavy: keep one instructive snippet per chapter with exact indentation.
Constraints: only touch `home/.agents/skills/book-genai-services-fastapi/` and `home/.claude/skills/book-genai-services-fastapi`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-genai-services-fastapi` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-ai-engineering
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-ai-engineering/` exists for "AI Engineering: Building Applications with Foundation Models" (Chip Huyen, 1108 pp, `~/books-src/book-ai-engineering.pdf`, outline with 10 chapters: intro, foundation models, evaluation methodology, evaluate AI systems, prompt engineering, RAG and agents, finetuning, dataset engineering, inference optimization, architecture and user feedback), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. This is the longest book: Docling will take ~25+ minutes; run in background and poll. Chapters are long: split a chapter into several files if one file would exceed the budget.
Constraints: only touch `home/.agents/skills/book-ai-engineering/` and `home/.claude/skills/book-ai-engineering`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-ai-engineering` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-genai-design-patterns
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-genai-design-patterns/` exists for "Generative AI Design Patterns" (Lakshmanan and Hapke, 694 pp, `~/books-src/book-genai-design-patterns.pdf`, outline with 10 chapters: controlling content style, adding knowledge (two chapters), extending model capabilities, improving reliability, enabling agents to take action, addressing constraints, setting safeguards, composable agentic workflows), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Each pattern is a section, so the per-section ranges are the point; keep a `patterns.md` index listing every pattern with its range.
Constraints: only touch `home/.agents/skills/book-genai-design-patterns/` and `home/.claude/skills/book-genai-design-patterns`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-genai-design-patterns` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-hands-on-llms
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-hands-on-llms/` exists for "Hands-On Large Language Models" (Alammar and Grootendorst, 598 pp, `~/books-src/book-hands-on-llms.pdf`, outline with 3 parts and 12 chapters: tokens and embeddings, inside LLMs, classification, clustering, prompt engineering, advanced generation, semantic search and RAG, multimodal, embedding models, finetuning), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Code-heavy: keep one instructive snippet per chapter.
Constraints: only touch `home/.agents/skills/book-hands-on-llms/` and `home/.claude/skills/book-hands-on-llms`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-hands-on-llms` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-agentic-design-patterns
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-agentic-design-patterns/` exists for "Agentic Design Patterns: A Hands-On Guide to Building Intelligent Systems" (Antonio Gulli, 482 pp, `~/books-src/book-agentic-design-patterns.pdf`), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. **This PDF has no internal outline.** Its first page is a table of contents with per-chapter page counts (Part One: chapters 1–7 prompt chaining, routing, parallelization, reflection, tool use, planning, multi-agent; Part Two: 8–11 memory, learning and adaptation, MCP, goal setting; Part Three: 12–14 exception handling, human-in-the-loop, RAG; Part Four: 15–21 A2A, resource-aware optimization, reasoning techniques, guardrails, evaluation, prioritization, exploration; Appendices A–G). Build the PDF page ranges by locating each chapter heading in the text and cross-checking against those page counts; record `outline: toc-derived` in `meta.json`. Text extracted from this PDF is split one word per line, so normalize whitespace before searching headings.
Constraints: only touch `home/.agents/skills/book-agentic-design-patterns/` and `home/.claude/skills/book-agentic-design-patterns`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-agentic-design-patterns` exits 0 (the verifier must normalize whitespace); `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: if whitespace normalization is missing from `verify_pages.py`, tell the executor; it is a foundation fix, not a per-book edit.

---

## Subtask: book-building-ai-agents
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-building-ai-agents/` exists for "Building Applications with AI Agents: Designing and Implementing Multiagent Systems" (355 pp, `~/books-src/book-building-ai-agents.pdf`, 13 chapters: intro to agents, designing agent systems, UX, tool use, orchestration, knowledge and memory, learning, one agent to many, validation and measurement, monitoring in production, improvement loops, protecting agentic systems, human-agent collaboration), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above.
Constraints: only touch `home/.agents/skills/book-building-ai-agents/` and `home/.claude/skills/book-building-ai-agents`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-building-ai-agents` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-hands-on-ml
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-hands-on-ml/` exists for "Hands-On Machine Learning with Scikit-Learn, Keras and TensorFlow" (Géron, 510 pp, `~/books-src/book-hands-on-ml.pdf`; outline has Part I fundamentals, chapters 1–9, and Part II neural networks and deep learning), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Cover **all** chapters present in the PDF (user said consider everything for now); if the PDF holds fewer chapters than the full book, record the actual last chapter in `meta.json`.
Constraints: only touch `home/.agents/skills/book-hands-on-ml/` and `home/.claude/skills/book-hands-on-ml`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-hands-on-ml` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-ml-design-patterns
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-ml-design-patterns/` exists for "Machine Learning Design Patterns" (Lakshmanan, Robinson, Munn, O'Reilly 2020, 408 pp, `~/books-src/book-ml-design-patterns.pdf`, outline with 8 chapters: need for patterns, data representation, problem representation, model training, resilient serving, reproducibility, responsible AI, connected patterns), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Each pattern is a section; keep a `patterns.md` index of all 30 patterns with their ranges.
Constraints: only touch `home/.agents/skills/book-ml-design-patterns/` and `home/.claude/skills/book-ml-design-patterns`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-ml-design-patterns` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-designing-ml-systems
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-designing-ml-systems/` exists for "Designing Machine Learning Systems" (Chip Huyen, 389 pp, `~/books-src/book-designing-ml-systems.pdf`, outline with 11 chapters: overview, ML systems design intro, data engineering fundamentals, training data, feature engineering, model development and offline evaluation, deployment and prediction service, distribution shifts and monitoring, continual learning and test in production, infrastructure and tooling for MLOps, human side of ML), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above.
Constraints: only touch `home/.agents/skills/book-designing-ml-systems/` and `home/.claude/skills/book-designing-ml-systems`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-designing-ml-systems` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-practical-mlops
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-practical-mlops/` exists for "Practical MLOps: Operationalizing Machine Learning Models" (Gift and Deza, 461 pp, `~/books-src/book-practical-mlops.pdf`, outline with 12 chapters: intro, foundations, containers and edge, continuous delivery, AutoML and KaizenML, monitoring and logging, MLOps for AWS, Azure, GCP, interoperability, CLI tools and microservices, case studies, plus appendices), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. The appendices on careers, remote work and VC thinking are not needed; skip them and say so in the report.
Constraints: only touch `home/.agents/skills/book-practical-mlops/` and `home/.claude/skills/book-practical-mlops`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-practical-mlops` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Subtask: book-ml-engineering-python
**Mechanism:** pane
**Harness:** claude-code
**Model:** opus
**Review stack:** validation-only + fast_ai

Objective: `home/.agents/skills/book-ml-engineering-python/` exists for "Machine Learning Engineering with Python" (Andrew McMahon, Packt, 239 pp, `~/books-src/book-ml-engineering-python.pdf`, outline with 3 sections and 8 chapters: intro to ML engineering, ML development process, model factory, packaging, deployment patterns and tools, scaling up, example ML microservice, example ETL ML use case), with section-level PDF page citations, `meta.json`, symlink in `home/.claude/skills/`, per the Common worker contract above. Code-heavy: keep one instructive snippet per chapter.
Constraints: only touch `home/.agents/skills/book-ml-engineering-python/` and `home/.claude/skills/book-ml-engineering-python`; do not edit `book-sources/` or other skills; no PDFs in the repo; no commit/push; `uv` only.
Validation: `uv run --with pypdf python3 -I home/.agents/skills/book-sources/verify_pages.py home/.agents/skills/book-ml-engineering-python` exits 0; `wc -w .../SKILL.md` ≤ ~3,000 words; 3 retrieval questions answered with citations confirmed by `pages.py`.
Stop condition: validation passes, or after one honest fix iteration remaining failures are listed; report sent.
Cross-refs: none.

---

## Final report (executor, after all 16 workers and reviews)

Deliver to the user a single table per book: token sizes (`SKILL.md`, average chapter), chapter count, verify pass rate, retrieval results, overlaps noticed with other books, problems. Stop there; no consolidation.
