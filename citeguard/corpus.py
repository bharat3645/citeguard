"""Source-corpus loader.

Loads a directory of plain-text source files and splits each into candidate
"passages" (paragraphs) that a claim sentence can be compared against.

Filename convention
--------------------
Each source file's *reference key* (the same key produced by
``citeguard.references.parse_references`` / ``citeguard.markers``) is taken
from the file's name, stem, minus extension, using one of two conventions
(checked in this order):

1. **Explicit key file**: if the file's first line is exactly
   ``KEY: <key>`` (case-insensitive, e.g. ``KEY: smith2020`` or
   ``KEY: 12``), that key is used and the ``KEY:`` line is stripped before
   paragraph-splitting.
2. **Filename-as-key** (default / fallback): the file's stem (name without
   extension) is used verbatim as the key. E.g. ``12.txt`` -> key ``"12"``;
   ``smith2020.txt`` -> key ``"smith2020"``.

This lets you organize a source directory either as ``12.txt``,
``13.txt``, ... (numeric style) or ``smith2020.txt``, ``jones2019.txt``,
... (author-year style), matching whichever citation style the document
under review uses. Both conventions can be mixed in the same directory.

Paragraph splitting: passages are separated by one or more blank lines.
Single newlines within a paragraph are treated as soft-wrapped text and
joined with a space.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

_KEY_LINE_RE = re.compile(r"^\s*KEY:\s*(.+?)\s*$", re.IGNORECASE)


@dataclass
class Source:
    """A single loaded source document."""

    key: str
    path: str
    passages: List[str] = field(default_factory=list)


def _split_paragraphs(text: str) -> List[str]:
    blocks = re.split(r"\n\s*\n", text.strip())
    passages = []
    for block in blocks:
        collapsed = re.sub(r"\s+", " ", block).strip()
        if collapsed:
            passages.append(collapsed)
    return passages


def load_source_file(path: Path) -> Source:
    """Load a single source text file into a :class:`Source`."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    lines = raw.splitlines()
    key = path.stem
    body = raw
    if lines:
        m = _KEY_LINE_RE.match(lines[0])
        if m:
            key = m.group(1).strip()
            body = "\n".join(lines[1:])
    passages = _split_paragraphs(body)
    return Source(key=key, path=str(path), passages=passages)


def load_corpus(directory: str) -> Dict[str, Source]:
    """Load every ``*.txt`` file in ``directory`` into a {key: Source} dict.

    Non-``.txt`` files are ignored. If two files resolve to the same key,
    the later one (alphabetical filename order) wins and a warning-style
    note is not raised here -- callers can inspect the returned dict size
    vs. file count if they want to detect collisions.
    """
    corpus: Dict[str, Source] = {}
    dir_path = Path(directory)
    for file_path in sorted(dir_path.glob("*.txt")):
        source = load_source_file(file_path)
        corpus[source.key] = source
    return corpus
