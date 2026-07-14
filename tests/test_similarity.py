import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.similarity import flag_for_score, score_claim_against_passages


PASSAGES = [
    "Global temperatures have risen due to greenhouse gas emissions from fossil fuel combustion.",
    "Photosynthesis converts light energy into chemical energy in plant cells.",
]


def test_supported_claim_scores_higher_than_unrelated_claim():
    claim_supported = (
        "Greenhouse gas emissions from burning fossil fuels are the primary "
        "driver of global temperature increases."
    )
    claim_unrelated = (
        "Quarterly revenue growth exceeded analyst expectations for the "
        "technology sector."
    )

    result_supported = score_claim_against_passages(claim_supported, PASSAGES)
    result_unrelated = score_claim_against_passages(claim_unrelated, PASSAGES)

    assert result_supported.score > result_unrelated.score
    assert result_supported.flag == "supported"
    assert result_unrelated.flag == "no clear support - flag"


def test_best_passage_is_the_topically_relevant_one():
    claim = "Rising CO2 emissions from burning fossil fuels drive global warming."
    result = score_claim_against_passages(claim, PASSAGES)
    assert result.best_passage == PASSAGES[0]


def test_empty_passages_yields_zero_score_and_flag():
    result = score_claim_against_passages("Any claim text.", [])
    assert result.score == 0.0
    assert result.flag == "no clear support - flag"
    assert result.best_passage_index == -1


def test_flag_thresholds():
    assert flag_for_score(0.9) == "supported"
    assert flag_for_score(0.36) == "supported"
    assert flag_for_score(0.35) == "weak support - review"
    assert flag_for_score(0.2) == "weak support - review"
    assert flag_for_score(0.15) == "weak support - review"
    assert flag_for_score(0.1) == "no clear support - flag"
    assert flag_for_score(0.0) == "no clear support - flag"


def test_score_is_bounded_between_zero_and_one():
    claim = "Identical text used as both claim and passage for a sanity check."
    result = score_claim_against_passages(claim, [claim])
    assert 0.0 <= result.score <= 1.0
    # Identical text should be a very strong (near-maximal) match.
    assert result.score > 0.9


def test_claim_or_passages_with_no_alphabetic_tokens_does_not_crash():
    result = score_claim_against_passages("1234 5678", ["9999", "!!!"])
    assert result.score == 0.0
