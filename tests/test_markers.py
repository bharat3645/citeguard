import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.markers import (
    Claim,
    extract_claims,
    find_citation_markers,
    split_sentences,
)


def test_split_sentences_basic():
    text = "This is sentence one. This is sentence two! Is this sentence three?"
    sents = split_sentences(text)
    assert [s.text for s in sents] == [
        "This is sentence one.",
        "This is sentence two!",
        "Is this sentence three?",
    ]


def test_split_sentences_protects_et_al_abbreviation():
    text = "The result was confirmed by Smith et al. in a follow-up study. It held up."
    sents = split_sentences(text)
    assert len(sents) == 2
    assert sents[0].text.startswith("The result was confirmed by Smith et al.")
    assert sents[1].text == "It held up."


def test_split_sentences_protects_dr_abbreviation():
    text = "Dr. Jones disagrees with the consensus view. She published a rebuttal."
    sents = split_sentences(text)
    assert len(sents) == 2
    assert sents[0].text == "Dr. Jones disagrees with the consensus view."


def test_split_sentences_empty_text():
    assert split_sentences("") == []
    assert split_sentences("   ") == []


def test_find_numeric_markers_single():
    text = "Emissions have risen sharply [12]."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].style == "numeric"
    assert markers[0].keys == ["12"]


def test_find_numeric_markers_multiple_in_one_bracket():
    text = "This is well established [12, 14]."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].keys == ["12", "14"]


def test_find_numeric_markers_range():
    text = "See prior work [3-5] for details."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].keys == ["3", "4", "5"]


def test_find_author_year_marker_et_al():
    text = "This was shown previously (Smith et al., 2020)."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].style == "author-year"
    assert markers[0].keys == ["smith2020"]


def test_find_author_year_marker_ampersand():
    text = "Two authors reported this (Smith & Jones, 2019)."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].keys == ["smith2019"]


def test_find_author_year_marker_and_word():
    text = "As shown by (Smith and Jones, 2019), the effect is real."
    markers = find_citation_markers(text)
    assert len(markers) == 1
    assert markers[0].keys == ["smith2019"]


def test_find_multiple_markers_mixed_styles_in_one_sentence():
    text = "Multiple lines of evidence [1] support this (Smith et al., 2020)."
    markers = find_citation_markers(text)
    assert len(markers) == 2
    styles = {m.style for m in markers}
    assert styles == {"numeric", "author-year"}


def test_extract_claims_pairs_marker_with_containing_sentence():
    text = (
        "Climate change is accelerating rapidly [1]. "
        "Some argue otherwise (Smith et al., 2020). "
        "Multiple studies confirm this trend [2, 3]."
    )
    claims = extract_claims(text)
    assert len(claims) == 3
    assert claims[0].sentence == "Climate change is accelerating rapidly [1]."
    assert claims[1].sentence == "Some argue otherwise (Smith et al., 2020)."
    assert claims[2].sentence == "Multiple studies confirm this trend [2, 3]."
    assert claims[2].marker.keys == ["2", "3"]


def test_extract_claims_multiple_citations_same_sentence_each_get_own_claim():
    text = "This is supported by both prior work [1] and later confirmation [2] in the same sentence."
    claims = extract_claims(text)
    assert len(claims) == 2
    assert claims[0].sentence == claims[1].sentence
    assert claims[0].marker.raw != claims[1].marker.raw


def test_extract_claims_no_markers_returns_empty():
    text = "This sentence has no citations at all."
    assert extract_claims(text) == []


def test_extract_claims_trailing_marker_without_terminal_punctuation():
    text = "This is the last sentence with a trailing marker [9]"
    claims = extract_claims(text)
    assert len(claims) == 1
    assert "[9]" in claims[0].sentence
