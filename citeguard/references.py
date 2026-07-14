"""Reference-list ("References" / "Bibliography" section) parsing.

Given the raw text of a document's reference list, this module parses it
into a list of ReferenceEntry(key, raw_text) records whose keys are
generated with the *same* normalization rules used by
:mod:`citeguard.markers`, so that a claim's citation marker keys
(e.g. "12" or "smith2020") can be looked up directly against the parsed
reference list.

Supported input conventions
----------------------------
1. Numbered entries, one per line or wrapped across lines, e.g.::

       [1] A. Smith, "A Study of Things," Journal of Things, 2020.
       [2] B. Jones and C. Lee, "Another Study," 2019.

   or the same without brackets::

       1. A. Smith, "A Study of Things," Journal of Things, 2020.

2. Author-year (unnumbered) entries, one per blank-line-separated block,
   author surname + year used as the key::

       Smith, A. (2020). A Study of Things. Journal of Things.

       Jones, B., & Lee, C. (2019). Another Study.

The parser auto-detects which convention is in use per entry: if a line/
block starts with a bracketed or dotted number, it is treated as numeric;
otherwise the leading "Surname" + a 4-digit year is used to build an
author-year key consistent with ``citeguard.markers._author_year_keys``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

_YEAR_RE = re.compile(r"\d{4}[a-z]?")

_NUMBERED_LINE_RE = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s*(.+)$")


@dataclass
class ReferenceEntry:
    """A single parsed reference-list entry."""

    key: str
    raw_text: str
    style: str  # "numeric" or "author-year"


def _author_year_key_from_entry(text: str) -> str:
    """Derive an author-year key from a reference entry's raw text using the
    same normalization as citeguard.markers._author_year_keys: lowercase
    first-author surname concatenated with the first 4-digit year found.
    """
    year_match = _YEAR_RE.search(text)
    year = year_match.group(0) if year_match else ""
    head = text[: year_match.start()] if year_match else text
    # First author surname is generally the first comma-delimited token,
    # possibly followed by initials -- take the first alphabetic run.
    first_token = re.split(r"[,;]", head.strip())[0]
    first_token = re.split(r"\s+(?:and|&)\s+", first_token)[0]
    surname = re.sub(r"[^a-zA-Z]", "", first_token).lower()
    return f"{surname}{year}"


def _split_blocks(raw_text: str) -> List[str]:
    """Split raw reference-section text into candidate entry blocks.

    Strategy: first split the whole text on blank lines (paragraph breaks).
    Each resulting chunk is then handled one of two ways:

    * If the chunk's first line matches the numbered-entry pattern, the
      chunk may contain *multiple* numbered entries packed together with no
      blank lines between them (the common case for numbered reference
      lists) -- so it is further split at each numbered-line boundary
      within the chunk, with any following non-numbered lines treated as
      wrapped continuation text of the preceding entry.
    * Otherwise the whole chunk is treated as a single (author-year style)
      entry, with internal newlines collapsed to spaces.

    This two-level approach correctly handles reference lists that mix
    numbered and author-year entries separated by blank lines (e.g. a
    numbered list followed by a blank-line-separated author-year entry
    that was added later), which a single global "numbered vs. not" switch
    would otherwise mis-split.
    """
    blank_blocks = re.split(r"\n\s*\n", raw_text.strip())
    blocks: List[str] = []
    for chunk in blank_blocks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        if _NUMBERED_LINE_RE.match(lines[0]):
            numbered_starts = [i for i, ln in enumerate(lines) if _NUMBERED_LINE_RE.match(ln)]
            for idx, start in enumerate(numbered_starts):
                end = numbered_starts[idx + 1] if idx + 1 < len(numbered_starts) else len(lines)
                block_lines = lines[start:end]
                block = "\n".join(block_lines).strip()
                if block:
                    blocks.append(block)
        else:
            blocks.append(chunk.replace("\n", " "))
    return blocks


def parse_references(raw_text: str) -> List[ReferenceEntry]:
    """Parse a references/bibliography section's raw text into a list of
    :class:`ReferenceEntry` objects.
    """
    entries: List[ReferenceEntry] = []
    for block in _split_blocks(raw_text):
        collapsed = re.sub(r"\s+", " ", block).strip()
        m = _NUMBERED_LINE_RE.match(block.splitlines()[0]) if block else None
        if m:
            num = m.group(1) or m.group(2)
            rest = m.group(3)
            # Re-attach any wrapped continuation lines.
            remaining_lines = block.splitlines()[1:]
            full_text = " ".join([rest] + [ln.strip() for ln in remaining_lines]).strip()
            full_text = re.sub(r"\s+", " ", full_text)
            entries.append(ReferenceEntry(key=num, raw_text=full_text, style="numeric"))
        else:
            key = _author_year_key_from_entry(collapsed)
            entries.append(ReferenceEntry(key=key, raw_text=collapsed, style="author-year"))
    return entries


def references_by_key(entries: List[ReferenceEntry]) -> dict:
    """Convenience: build a {key: ReferenceEntry} lookup dict."""
    return {e.key: e for e in entries}
