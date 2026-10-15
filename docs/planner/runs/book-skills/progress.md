# book-skills run ledger
plan docs/planner/plans/2026-10-05-book-skills.md  executor surface:95 workspace:7
foundation book-to-skill@e180fc4 installed (uv .venv, docling OK via ~/books-src/.tools/extract.sh Zscaler CA bundle)  20:15
foundation 16 PDFs in ~/books-src, sources.json, pages.py, verify_pages.py smoke-tested  20:15
ASSUMED: no commits at all (user + plan) -> foundation left uncommitted in primary checkout; worktrees get absolute symlinks to book-sources/ and book-to-skill/; .worktrees/ ignored via .git/info/exclude
ASSUMED: Docling behind Zscaler needs CA bundle (certifi + keychain roots) at ~/books-src/.tools/ca-bundle.pem; workers use extract.sh wrapper
ASSUMED: authors in sources.json for some books filled from executor knowledge (Konieczny, Gough/Bryant/Auburn, Parandeh, Albada, McMahon)
ASSUMED: briefs = plan contract verbatim + "Executor run notes" (env facts: wrapper, symlinks, book-to-skill non-interactive answers DEPTH=reference)
USER: mid-run asked for a lighter model than Opus -> all workers now sonnet (claude-code). Opus batch-1 panes closed before any work  20:16
dispatched review-foundation pi/gpt-5.5 surface:109 (deep_ai, different provider from Claude-built tooling) 20:17
dispatched book-ai-engineering .worktrees/book-ai-engineering sonnet 20:17
dispatched book-ddia .worktrees/book-ddia sonnet 20:17
dispatched book-genai-design-patterns .worktrees/book-genai-design-patterns sonnet 20:17
dispatched book-genai-services-fastapi .worktrees/book-genai-services-fastapi sonnet 20:17
review-foundation FAIL (2 findings: generic-title false PASS, silent unparseable citations) -> fixed in place + line-numbering tolerance; sent back for re-check 20:21
notify book-ddia DONE_WITH_CONCERNS (wrote chapters from memory, docling text unused) -> sent back to ground in extracted text (retry 1) 20:21
review-foundation PASS (re-check) -> reviewer pane closed 20:21
ASSUMED/NOTE: executor skill's RPC param workspaceId is wrong; cmux needs workspace_id (else acts on the selected workspace)
notify book-genai-design-patterns DONE_WITH_CONCERNS 54/54 (offset assumed 12, partial grounding audit) 20:25
dispatched review-book-genai-design-patterns pi/gpt-5.5 surface:111 fast_ai 20:25
dispatched book-hands-on-llms .worktrees/book-hands-on-llms surface:112 sonnet 20:25
notify book-ai-engineering DONE_WITH_CONCERNS 143/143 (no printed page numbers -> offset 0) queued for review 20:26
notify book-genai-services-fastapi DONE_WITH_CONCERNS 56/56 (snippets partly reconstructed, offset 22 unverified) queued for review 20:27
review book-genai-design-patterns PASS (3/3 retrieval, 5/5 spot-checks) -> worker+reviewer panes closed 20:27
dispatched review-book-ai-engineering pi/gpt-5.5 surface:115 20:28
dispatched book-building-microservices .worktrees/book-building-microservices surface:116 sonnet 20:28
notify book-ddia regrounded 54/54 but chapters 735-1822 words -> asked to trim to <=1200 20:28
notify book-ddia trimmed (<=1186 words/chapter, 54/54) queued for review 20:30
review book-ai-engineering PASS (3/3, 5/5) -> panes closed 20:30
dispatched review-book-genai-services-fastapi pi/gpt-5.5 surface:119 20:30
dispatched book-hands-on-ml .worktrees/book-hands-on-ml surface:120 sonnet 20:30
USER: 'no gastes tokens en reviewers' -> AI reviews dropped; remaining books validation-only (executor runs val.sh). review-book-genai-services-fastapi pane closed before it started 20:31
val book-genai-services-fastapi PASS 56/56 (validation-only) -> pane closed 20:31
val book-ddia PASS 54/54 (validation-only) -> pane closed 20:31
dispatched book-agentic-design-patterns .worktrees/book-agentic-design-patterns surface:124 sonnet 20:31
val book-hands-on-llms PASS 182/182 -> pane closed 20:32
dispatched book-ml-design-patterns .worktrees/book-ml-design-patterns surface:126 sonnet 20:32
