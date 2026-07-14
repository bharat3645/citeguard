import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.references import parse_references, references_by_key


NUMERIC_REFS = """[1] A. Smith, "A Study of Climate Trends," Journal of Climate, 2020.
[2] B. Jones and C. Lee, "Ocean Currents in the North Atlantic,"
Ocean Science, 2019.
[3] D. Kim, "Coral Reef Decline," Marine Biology, 2021.
"""

AUTHOR_YEAR_REFS = """Smith, A. (2020). A Study of Climate Trends. Journal of Climate.

Jones, B., & Lee, C. (2019). Ocean Currents in the North Atlantic. Ocean Science.

Kim, D. (2021). Coral Reef Decline. Marine Biology.
"""


def test_parse_numeric_references_basic():
    entries = parse_references(NUMERIC_REFS)
    assert [e.key for e in entries] == ["1", "2", "3"]
    assert all(e.style == "numeric" for e in entries)
    assert "Smith" in entries[0].raw_text
    assert "2020" in entries[0].raw_text


def test_parse_numeric_references_reattaches_wrapped_lines():
    entries = parse_references(NUMERIC_REFS)
    assert "Ocean Currents in the North Atlantic" in entries[1].raw_text
    assert "Ocean Science" in entries[1].raw_text
    assert "\n" not in entries[1].raw_text


def test_parse_author_year_references_basic():
    entries = parse_references(AUTHOR_YEAR_REFS)
    keys = [e.key for e in entries]
    assert keys == ["smith2020", "jones2019", "kim2021"]
    assert all(e.style == "author-year" for e in entries)


def test_references_by_key_lookup():
    entries = parse_references(NUMERIC_REFS)
    by_key = references_by_key(entries)
    assert by_key["2"].raw_text.startswith("B. Jones")


def test_parse_references_keys_match_marker_extraction_convention():
    entries = parse_references("Smith, A., Doe, J. (2020). Some Title. Some Journal.")
    assert entries[0].key == "smith2020"
