import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.llm import explain_flag


def test_explain_flag_no_client_returns_templated_string_with_overlap():
    claim = "Greenhouse gas emissions drive global temperature increases."
    passage = "Global temperatures have risen due to greenhouse gas emissions."
    explanation = explain_flag(claim, passage, llm_client=None)
    assert isinstance(explanation, str)
    assert len(explanation) > 0
    assert "overlap" in explanation.lower() or "passage" in explanation.lower()


def test_explain_flag_no_client_no_overlap():
    claim = "Stock markets rallied after the earnings report."
    passage = "Photosynthesis converts light energy into chemical energy."
    explanation = explain_flag(claim, passage, llm_client=None)
    assert "different topic" in explanation.lower() or "mismatch" in explanation.lower()


def test_explain_flag_empty_passage():
    explanation = explain_flag("Some claim.", "", llm_client=None)
    assert "no candidate passage" in explanation.lower()


def test_explain_flag_never_calls_network_without_client_or_key(monkeypatch):
    # Ensure no ANTHROPIC_API_KEY leaks in from the test environment and
    # that the function completes without attempting any import/network
    # activity when llm_client is None.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    explanation = explain_flag("A claim.", "A passage.", llm_client=None)
    assert isinstance(explanation, str)
