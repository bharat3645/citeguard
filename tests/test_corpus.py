import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from citeguard.corpus import load_corpus, load_source_file


def test_load_corpus_filename_as_key(tmp_path):
    (tmp_path / "12.txt").write_text(
        "First paragraph about climate change.\n\nSecond paragraph about oceans.",
        encoding="utf-8",
    )
    corpus = load_corpus(str(tmp_path))
    assert "12" in corpus
    assert corpus["12"].passages == [
        "First paragraph about climate change.",
        "Second paragraph about oceans.",
    ]


def test_load_corpus_explicit_key_line(tmp_path):
    (tmp_path / "source_a.txt").write_text(
        "KEY: smith2020\nThis is the actual body paragraph text.",
        encoding="utf-8",
    )
    corpus = load_corpus(str(tmp_path))
    assert "smith2020" in corpus
    assert corpus["smith2020"].passages == ["This is the actual body paragraph text."]


def test_load_corpus_ignores_non_txt_files(tmp_path):
    (tmp_path / "12.txt").write_text("Paragraph one.", encoding="utf-8")
    (tmp_path / "notes.md").write_text("Should be ignored.", encoding="utf-8")
    corpus = load_corpus(str(tmp_path))
    assert list(corpus.keys()) == ["12"]


def test_load_source_file_joins_soft_wrapped_lines(tmp_path):
    path = tmp_path / "13.txt"
    path.write_text(
        "This paragraph wraps\nacross two lines.\n\nA second paragraph here.",
        encoding="utf-8",
    )
    source = load_source_file(path)
    assert source.passages[0] == "This paragraph wraps across two lines."
    assert source.passages[1] == "A second paragraph here."
