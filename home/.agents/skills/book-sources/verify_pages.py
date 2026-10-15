"""Check that every cited section range in a book skill points at real PDF pages.

Usage: uv run --with pypdf python3 -I verify_pages.py <skill-dir> [--min-rate 0.95]

Parses every `## <Section title> (PDF pp. a–b)` (or `(PDF p. a)`) heading in
<skill-dir>/chapters/*.md, extracts PDF pages a..b of the book, and checks the
section title appears within that range. Short or generic titles ("Summary")
must appear as a heading line of their own; longer ones may appear anywhere in
the range. Matching ignores case, whitespace
(including one-word-per-line extraction), hyphenation, punctuation and
ligatures, and falls back to a fuzzy match for small extraction differences.

The book is found by the skill directory name (the slug) in sources.json, or
by `slug` in <skill-dir>/meta.json. Exits 0 only if the pass rate is at least
--min-rate (default 0.95) and there is at least one citation.
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

SOURCES = Path(__file__).resolve().parent / "sources.json"

HEADING = re.compile(
    r"^#{2,6}\s+(?P<title>.+?)\s*\(\s*PDF\s+pp?\.\s*(?P<a>\d+)\s*(?:[–—-]\s*(?P<b>\d+))?\s*\)\s*$"
)
# Leading "1.2", "Chapter 3:", "Pattern 7:", "Appendix A." style numbering.
NUMBERING = re.compile(
    r"^(?:(?:chapter|part|pattern|appendix|section)\s+[\w.]+\s*[:.\-–—]?\s*|[\d.]+\s+|[A-Z]\.\s+)",
    re.IGNORECASE,
)
FUZZY_MIN = 0.88
# Titles this short (compacted) or this generic would match almost any page as a
# substring, so they must appear as a heading line of their own instead.
SHORT_TITLE = 14
GENERIC = {
    "summary", "introduction", "conclusion", "conclusions", "overview", "data",
    "references", "furtherreading", "keytakeaways", "exercises", "background",
    "example", "examples", "solution", "problem", "tradeoffs", "tradeoffsandalternatives",
    "whyitworks", "codeexample", "practicalapplications", "atglance", "ataglance",
}
# Compacted "chapter6", "part2", "pattern12", "appendixa", "31" prefixes on a PDF line.
LINE_NUMBERING = re.compile(r"^(?:(?:chapter|part|pattern|appendix|section)(?:\d+|[a-z](?=[a-z]{4}))|\d+)")
CITATION_HINT = re.compile(r"^#{2,6}\s.*\(\s*PDF\b", re.IGNORECASE)


def compact(text):
    """Lowercase alphanumerics only: removes whitespace, hyphenation, punctuation."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("­", "").replace("&", "and")
    text = re.sub(r"-\s*\n\s*", "", text)
    return re.sub(r"[^0-9a-z]+", "", text.lower())


def clean_title(title):
    title = re.sub(r"[*_`]", "", title)
    title = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", title)
    return title.strip()


def title_variants(title):
    title = clean_title(title)
    variants = [title]
    stripped = NUMBERING.sub("", title).strip()
    if stripped and stripped != title:
        variants.append(stripped)
    # "Title: Subtitle" headings: the PDF often prints only the first part.
    for sep in (":", " — ", " – "):
        if sep in stripped:
            head = stripped.split(sep, 1)[0].strip()
            if len(compact(head)) >= 8:
                variants.append(head)
    out = []
    for v in variants:
        c = compact(v)
        if c and c not in out:
            out.append(c)
    return out


def fuzzy_found(needle, hay):
    """Best similarity of needle against any same-length window of hay."""
    n = len(needle)
    if n < 6 or len(hay) < n:
        return 0.0
    best = 0.0
    anchors = {needle[:3], needle[-3:]}
    for i in range(len(hay) - n + 1):
        if hay[i : i + 3] not in anchors and hay[i + n - 3 : i + n] not in anchors:
            continue
        r = SequenceMatcher(None, needle, hay[i : i + n], autojunk=False).ratio()
        if r > best:
            best = r
            if best >= 0.99:
                break
    return best


def resolve_slug(skill_dir):
    meta = skill_dir / "meta.json"
    if meta.is_file():
        try:
            slug = json.loads(meta.read_text(encoding="utf-8")).get("slug")
            if slug:
                return slug
        except json.JSONDecodeError:
            pass
    return skill_dir.name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_dir")
    ap.add_argument("--min-rate", type=float, default=0.95)
    args = ap.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    chapters = sorted((skill_dir / "chapters").glob("*.md"))
    if not chapters:
        sys.exit(f"error: no chapters/*.md under {skill_dir}")

    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    slug = resolve_slug(skill_dir)
    if slug not in sources:
        sys.exit(f"error: slug {slug!r} not in {SOURCES}")
    pdf = Path(os.path.expanduser(sources[slug]["path"]))
    if not pdf.is_file():
        sys.exit(f"error: PDF for {slug} not found at {pdf}")

    from pypdf import PdfReader

    reader = PdfReader(str(pdf))
    total = len(reader.pages)
    cache = {}

    def page(n):
        """(compacted page text, compacted non-empty lines) for PDF page n."""
        if n not in cache:
            raw = reader.pages[n - 1].extract_text() or ""
            lines = [c for c in (compact(l) for l in raw.splitlines()) if c]
            cache[n] = (compact(raw), lines)
        return cache[n]

    def heading_line(needle, a, b):
        """True if the needle is a line of its own, or 2-6 consecutive lines
        joined (wrapped headings, one-word-per-line extraction)."""
        for n in range(a, b + 1):
            lines = page(n)[1]
            for i in range(len(lines)):
                joined = ""
                for j in range(i, min(i + 6, len(lines))):
                    joined += lines[j]
                    if needle in (joined, LINE_NUMBERING.sub("", joined)):
                        return True
                    if len(joined) >= len(needle):
                        break
        return False

    passed = failed = 0
    missing_source = []
    for ch in chapters:
        lines = ch.read_text(encoding="utf-8").splitlines()
        if not any(l.startswith("Source:") for l in lines[:5]):
            missing_source.append(ch.name)
        for lineno, line in enumerate(lines, 1):
            m = HEADING.match(line.strip())
            if not m:
                if CITATION_HINT.match(line.strip()):
                    failed += 1
                    print(f"FAIL {ch.name}:{lineno}: unparseable citation, use '(PDF pp. a–b)' | {line.strip()}")
                continue
            title = m.group("title")
            a = int(m.group("a"))
            b = int(m.group("b") or a)
            where = f"{ch.name}:{lineno}"
            if a < 1 or b < a or b > total:
                failed += 1
                print(f"FAIL {where} pp. {a}-{b}: bad range (book has 1-{total}) | {title}")
                continue
            variants = title_variants(title)
            if any(heading_line(v, a, b) for v in variants):
                passed += 1
                print(f"PASS {where} pp. {a}-{b} (heading) | {title}")
                continue
            if all(len(v) < SHORT_TITLE or v in GENERIC for v in variants):
                failed += 1
                print(f"FAIL {where} pp. {a}-{b}: short/generic title not found as a heading line | {title}")
                continue
            hay = "".join(page(n)[0] for n in range(a, b + 1))
            variants = [v for v in variants if len(v) >= SHORT_TITLE and v not in GENERIC]
            if any(v in hay for v in variants):
                passed += 1
                print(f"PASS {where} pp. {a}-{b} | {title}")
                continue
            score = max(fuzzy_found(v, hay) for v in variants)
            if score >= FUZZY_MIN:
                passed += 1
                print(f"PASS {where} pp. {a}-{b} (fuzzy {score:.2f}) | {title}")
            else:
                failed += 1
                print(f"FAIL {where} pp. {a}-{b} (best {score:.2f}) | {title}")

    total_cites = passed + failed
    rate = passed / total_cites if total_cites else 0.0
    if missing_source:
        print(f"WARN no 'Source:' line in first 5 lines: {', '.join(missing_source)}")
    print(f"RESULT {slug}: {passed}/{total_cites} citations pass ({rate:.1%}); threshold {args.min_rate:.0%}")
    sys.exit(0 if total_cites and rate >= args.min_rate else 1)


if __name__ == "__main__":
    main()
