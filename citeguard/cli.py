"""citeguard command-line interface.

Usage
-----
    citeguard --document paper.txt --references refs.txt --sources ./sources/ -o report.md

All processing is local: no network access is made anywhere in this path.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import run


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="citeguard",
        description=(
            "citeguard: offline citation-claim support verifier. Checks whether "
            "citations in a document text are actually supported by the source "
            "text they point to, using TF-IDF lexical-similarity scoring."
        ),
    )
    parser.add_argument(
        "--document", "-d", required=True, type=str,
        help="Path to a plain-text file containing the document body (with inline citation markers).",
    )
    parser.add_argument(
        "--references", "-r", required=True, type=str,
        help="Path to a plain-text file containing the References/Bibliography section.",
    )
    parser.add_argument(
        "--sources", "-s", required=True, type=str,
        help="Path to a directory of plain-text source files (one per reference; see README for filename convention).",
    )
    parser.add_argument(
        "--output", "-o", type=str, default=None,
        help="Path to write the Markdown report to. If omitted, the report is printed to stdout.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    document_path = Path(args.document)
    references_path = Path(args.references)
    sources_dir = Path(args.sources)

    for p, label in [(document_path, "document"), (references_path, "references")]:
        if not p.is_file():
            print(f"error: {label} file not found: {p}", file=sys.stderr)
            return 2
    if not sources_dir.is_dir():
        print(f"error: sources directory not found: {sources_dir}", file=sys.stderr)
        return 2

    document_text = document_path.read_text(encoding="utf-8", errors="replace")
    references_text = references_path.read_text(encoding="utf-8", errors="replace")

    report_md = run(
        document_text=document_text,
        references_text=references_text,
        source_dir=str(sources_dir),
        document_name=document_path.name,
    )

    if args.output:
        Path(args.output).write_text(report_md, encoding="utf-8")
        print(f"Report written to {args.output}")
    else:
        print(report_md)

    return 0


if __name__ == "__main__":
    sys.exit(main())
