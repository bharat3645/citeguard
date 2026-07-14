import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.pipeline import build_findings, run


DOCUMENT_TEXT = (
    "Global temperatures have risen sharply due to greenhouse gas emissions [1]. "
    "Ocean current patterns have also shifted in recent decades [2]. "
    "Unrelated claim about stock markets rallying appears here [3]."
)

REFERENCES_TEXT = (
    "[1] A. Smith, \"Greenhouse Gas Emissions and Warming,\" 2020.\n"
    "[2] B. Jones, \"Ocean Current Shifts,\" 2019.\n"
    "[3] C. Lee, \"Some Unrelated Reference,\" 2021.\n"
)


def _write_sources(tmp_path):
    (tmp_path / "1.txt").write_text(
        "Global temperatures have risen due to greenhouse gas emissions from fossil fuels.",
        encoding="utf-8",
    )
    (tmp_path / "2.txt").write_text(
        "The study analyzed ocean current patterns in the North Atlantic over decades.",
        encoding="utf-8",
    )
    (tmp_path / "3.txt").write_text(
        "Photosynthesis converts light energy into chemical energy in plant cells.",
        encoding="utf-8",
    )


def test_build_findings_end_to_end(tmp_path):
    _write_sources(tmp_path)
    findings = build_findings(DOCUMENT_TEXT, REFERENCES_TEXT, str(tmp_path))
    assert len(findings) == 3
    by_key = {f.reference_key: f for f in findings}
    assert by_key["1"].result.flag == "supported"
    assert by_key["2"].result.flag == "supported"
    assert by_key["3"].result.flag == "no clear support - flag"


def test_build_findings_missing_reference_is_reported(tmp_path):
    _write_sources(tmp_path)
    findings = build_findings(
        "A claim with an unresolvable citation [99].", REFERENCES_TEXT, str(tmp_path)
    )
    assert len(findings) == 1
    assert findings[0].result is None
    assert "no matching reference" in findings[0].note.lower()


def test_run_produces_markdown_report(tmp_path):
    _write_sources(tmp_path)
    report = run(DOCUMENT_TEXT, REFERENCES_TEXT, str(tmp_path), document_name="sample.txt")
    assert report.startswith("# citeguard Report: sample.txt")
    assert "no clear support - flag" in report


def test_cli_end_to_end_writes_report_file(tmp_path):
    _write_sources(tmp_path)
    doc_file = tmp_path / "doc.txt"
    refs_file = tmp_path / "refs.txt"
    out_file = tmp_path / "report.md"
    doc_file.write_text(DOCUMENT_TEXT, encoding="utf-8")
    refs_file.write_text(REFERENCES_TEXT, encoding="utf-8")

    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            sys.executable, "-m", "citeguard.cli",
            "--document", str(doc_file),
            "--references", str(refs_file),
            "--sources", str(tmp_path),
            "--output", str(out_file),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "citeguard Report" in content
