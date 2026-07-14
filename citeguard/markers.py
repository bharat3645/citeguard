"""Citation-marker extraction and claim-sentence isolation.

This module finds citation markers in a body of running text and, for each
marker, extracts the sentence that contains it (the "claim"). Two citation
styles are supported out of the box:

* Numeric bracket style:   [12], [12, 14], [3-5]
* Author-year style:       (Smith et al., 2020), (Smith & Jones, 2019),
                            (Smith and Jones, 2019, 2021)

Design notes / limitations
---------------------------
Sentence-boundary detection is done with a simple regex-based splitter, not a
full NLP sentence tokenizer (no spaCy/nltk dependency -- keeps the tool
offline and fast). This is a deliberate trade-off:

* It splits on '.', '!', or '?' followed by whitespace and a capital
  letter / opening quote, while trying to protect common abbreviations
  (et al., e.g., i.e., Dr., Fig., single-letter initials like J.) from being
  treated as sentence boundaries.
* It will still occasionally mis-split on abbreviations it does not know
  about, or fail to split when a sentence legitimately ends right before a
  capitalized abbreviation. For academic prose (the target use case) this
  is a reasonable approximation, not a guarantee.
* It does not handle nested quotations, footnote-style superscript markers,
  or citation markers that span a sentence boundary with full accuracy.

If you need bullet-proof sentence segmentation, swap ``split_sentences`` for
a proper tokenizer (e.g. nltk.sent_tokenize or a spaCy pipeline) -- the rest
of the pipeline only depends on getting a list of Sentence spans back.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

# --------------------------------------------------------------------------
# Sentence splitting
# --------------------------------------------------------------------------

_ABBREVIATIONS = [
    "et al", "e.g", "i.e", "cf", "vs", "etc",
    "Dr", "Mr", "Mrs", "Ms", "Prof", "Fig", "fig", "eq", "Eq",
    "No", "Vol", "pp", "p",
]

_PLACEHOLDER = "\x00"


def _protect_abbreviations(text: str) -> str:
    protected = text
    for abbr in _ABBREVIATIONS:
        pattern = re.compile(re.escape(abbr) + r"\.", re.IGNORECASE)
        protected = pattern.sub(lambda m: m.group(0)[:-1] + _PLACEHOLDER, protected)
    return protected


def _restore_abbreviations(text: str) -> str:
    return text.replace(_PLACEHOLDER, ".")


_SENTENCE_BOUNDARY_RE = re.compile(
    r'(?<=[.!?])\s+(?=(?:[A-Z0-9"‘’“”(\[]|$))'
)


@dataclass
class Sentence:
    """A sentence with its character offsets in the original text."""

    text: str
    start: int
    end: int


def split_sentences(text: str) -> List[Sentence]:
    """Split ``text`` into sentences using a simple, dependency-free regex
    heuristic. See the module docstring for known limitations.
    """
    if not text or not text.strip():
        return []

    working = _protect_abbreviations(text)

    sentences: List[Sentence] = []
    pos = 0
    for match in _SENTENCE_BOUNDARY_RE.finditer(working):
        boundary = match.start()
        chunk = working[pos:boundary]
        if chunk.strip():
            lstripped_len = len(chunk) - len(chunk.lstrip())
            real_start = pos + lstripped_len
            real_text = _restore_abbreviations(chunk.strip())
            real_end = real_start + len(chunk.strip())
            sentences.append(Sentence(text=real_text, start=real_start, end=real_end))
        pos = match.end()

    tail = working[pos:]
    if tail.strip():
        lstripped_len = len(tail) - len(tail.lstrip())
        real_start = pos + lstripped_len
        real_text = _restore_abbreviations(tail.strip())
        real_end = real_start + len(tail.strip())
        sentences.append(Sentence(text=real_text, start=real_start, end=real_end))

    return sentences


# --------------------------------------------------------------------------
# Citation marker extraction
# --------------------------------------------------------------------------

_NUMERIC_MARKER_RE = re.compile(r"\[\s*\d+(?:\s*[-,]\s*\d+)*\s*\]")

_AUTHOR_YEAR_MARKER_RE = re.compile(
    r"""\(
        [A-Z][A-Za-z\-']+
        (?:\s*(?:,|&|and|et\ al\.?)\s*[A-Za-z\-'.]*)*
        ,?\s*
        \d{4}[a-z]?
        (?:\s*,\s*\d{4}[a-z]?)*
        (?:\s*;\s*[A-Z][A-Za-z\-'.]+(?:\s*(?:,|&|and|et\ al\.?)\s*[A-Za-z\-'.]*)*,?\s*\d{4}[a-z]?)*
        \)""",
    re.VERBOSE,
)


@dataclass
class CitationMarker:
    """A single citation marker found in the text."""

    raw: str
    style: str  # "numeric" or "author-year"
    keys: List[str]
    start: int
    end: int


def _numeric_keys(raw: str) -> List[str]:
    inner = raw.strip("[] ")
    keys: List[str] = []
    for part in inner.split(","):
        part = part.strip()
        if "-" in part:
            lo, _, hi = part.partition("-")
            if lo.strip().isdigit() and hi.strip().isdigit():
                keys.extend(str(n) for n in range(int(lo), int(hi) + 1))
                continue
        if part.isdigit():
            keys.append(part)
    return keys


_AUTHOR_YEAR_SPLIT_RE = re.compile(r"\s*;\s*")
_YEAR_RE = re.compile(r"\d{4}[a-z]?")


def _author_year_keys(raw: str) -> List[str]:
    inner = raw.strip("() ")
    keys: List[str] = []
    for clause in _AUTHOR_YEAR_SPLIT_RE.split(inner):
        clause = clause.strip()
        if not clause:
            continue
        years = _YEAR_RE.findall(clause)
        first_year_match = _YEAR_RE.search(clause)
        author_part = clause[: first_year_match.start()] if first_year_match else clause
        first_author = re.split(r"\s*(?:,|&|and|et al\.?)\s*", author_part)[0].strip()
        first_author = first_author.rstrip(",").strip()
        surname_norm = re.sub(r"[^a-zA-Z]", "", first_author).lower()
        for year in years or [""]:
            keys.append(f"{surname_norm}{year}")
    return keys


def find_citation_markers(text: str) -> List[CitationMarker]:
    """Find all citation markers (numeric-bracket and author-year style) in
    ``text``, returned in order of appearance with character offsets.
    """
    markers: List[CitationMarker] = []

    for m in _NUMERIC_MARKER_RE.finditer(text):
        markers.append(
            CitationMarker(
                raw=m.group(0),
                style="numeric",
                keys=_numeric_keys(m.group(0)),
                start=m.start(),
                end=m.end(),
            )
        )

    for m in _AUTHOR_YEAR_MARKER_RE.finditer(text):
        markers.append(
            CitationMarker(
                raw=m.group(0),
                style="author-year",
                keys=_author_year_keys(m.group(0)),
                start=m.start(),
                end=m.end(),
            )
        )

    markers.sort(key=lambda mk: mk.start)
    return markers


# --------------------------------------------------------------------------
# Claim extraction: pairing each marker with its containing sentence
# --------------------------------------------------------------------------


@dataclass
class Claim:
    """A citation marker plus the sentence it was found in."""

    marker: CitationMarker
    sentence: str
    sentence_start: int
    sentence_end: int


def extract_claims(text: str) -> List[Claim]:
    """Find every citation marker in ``text`` and pair it with the sentence
    that contains it. If multiple markers fall in the same sentence, one
    Claim is produced per marker (they share the sentence text) since each
    marker may cite a different, independently-checkable source.
    """
    sentences = split_sentences(text)
    markers = find_citation_markers(text)

    claims: List[Claim] = []
    for marker in markers:
        containing = None
        for sent in sentences:
            if sent.start <= marker.start < sent.end + 1:
                containing = sent
                break
        if containing is None:
            candidates = [s for s in sentences if s.start <= marker.start]
            containing = candidates[-1] if candidates else Sentence(text.strip(), 0, len(text))

        claims.append(
            Claim(
                marker=marker,
                sentence=containing.text,
                sentence_start=containing.start,
                sentence_end=containing.end,
            )
        )
    return claims
