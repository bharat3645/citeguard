import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.markers import CitationMarker, Claim
from citeguard.report import Finding, generate_report
from citeguard.similarity import SupportResult


def _make_finding(raw_marker, score, sentence="A claim sentence.", best_passage="A passage."):
    marker = CitationMarker(raw=raw_marker, style="numeric", keys=["1"], start=0, end=len(raw_marker))
    claim = Claim(marker=marker, sentence=sentence, sentence_start=0, sentence_end=len(sentence))
    result = SupportResult(
        score=score,
        flag="supported" if score > 0.35 else ("weak support - review" if score >= 0.15 else "no clear support - flag"),
        best_passage=best_passage,
        best_passage_index=0,
    )
    return Finding(claim=claim, reference_key="1", reference_text="Some Reference, 2020.", result=result)


def test_report_sorts_worst_support_first():
    findings = [
        _make_finding("[1]", 0.9, sentence="High support claim."),
        _make_finding("[2]", 0.05, sentence="Low support claim."),
        _make_finding("[3]", 0.5, sentence="Medium-high support claim."),
    ]
    report = generate_report(findings, document_name="test.txt")

    idx_low = report.index("Low support claim.")
    idx_medium = report.index("Medium-high support claim.")
    idx_high = report.index("High support claim.")
    assert idx_low < idx_medium < idx_high


def test_report_contains_summary_counts():
    findings = [
        _make_finding("[1]", 0.9),
        _make_finding("[2]", 0.05),
        _make_finding("[3]", 0.2),
    ]
    report = generate_report(findings, document_name="test.txt")
    assert "Total citation-claim pairs checked: **3**" in report
    assert "Flagged (no clear support): **1**" in report
    assert "Weak support (review recommended): **1**" in report
    assert "Supported: **1**" in report


def test_report_includes_claim_and_best_passage_text():
    findings = [_make_finding("[1]", 0.1, sentence="The sky is green.", best_passage="The sky is blue.")]
    report = generate_report(findings)
    assert "The sky is green." in report
    assert "The sky is blue." in report


def test_report_handles_unresolved_findings_without_crashing():
    from citeguard.markers import CitationMarker, Claim

    marker = CitationMarker(raw="[99]", style="numeric", keys=["99"], start=0, end=4)
    claim = Claim(marker=marker, sentence="An orphaned citation claim.", sentence_start=0, sentence_end=10)
    finding = Finding(claim=claim, reference_key="99", reference_text=None, result=None, note="No matching reference found.")
    report = generate_report([finding])
    assert "No matching reference found." in report
    assert "An orphaned citation claim." in report
