"""Print the text of PDF pages <from>..<to> (1-based, inclusive) of a book.

Usage: uv run --with pypdf python3 -I pages.py <slug> <from> <to>

The PDF path comes from sources.json next to this script. Page numbers are
PDF page indexes (what a PDF viewer shows), not printed page numbers; see the
book skill's meta.json `printed_offset` (printed = pdf - offset).
"""

import json
import os
import sys
from pathlib import Path

SOURCES = Path(__file__).resolve().parent / "sources.json"


def load_sources():
    with open(SOURCES, encoding="utf-8") as f:
        return json.load(f)


def book_path(slug):
    sources = load_sources()
    if slug not in sources:
        sys.exit(f"error: unknown slug {slug!r}; known: {', '.join(sorted(sources))}")
    path = Path(os.path.expanduser(sources[slug]["path"]))
    if not path.is_file():
        sys.exit(f"error: PDF for {slug} not found at {path}")
    return path


def main(argv):
    if len(argv) != 4:
        sys.exit("usage: pages.py <slug> <from> <to>")
    slug = argv[1]
    try:
        first, last = int(argv[2]), int(argv[3])
    except ValueError:
        sys.exit("error: <from> and <to> must be integers")

    from pypdf import PdfReader

    reader = PdfReader(str(book_path(slug)))
    total = len(reader.pages)
    if first < 1 or last < first or last > total:
        sys.exit(f"error: bad range {first}-{last}; {slug} has PDF pages 1-{total}")

    for n in range(first, last + 1):
        print(f"===== {slug} · PDF p. {n} =====")
        print(reader.pages[n - 1].extract_text() or "")


if __name__ == "__main__":
    main(sys.argv)
