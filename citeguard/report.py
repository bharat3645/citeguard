"""Markdown report generation.

Produces a human-readable Markdown report listing every extracted claim,
its citation marker, the reference it resolved to (if any), the computed
support score/flag, the claim sentence, and the best-matching passage from
the cited source -- sorted worst-support-first so the riskiest citations
surface at the top for human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .markers import Claim
from .similarity import SupportResult


@dataclass
class Finding:
    """One fully-resolved claim+citation+score record, ready for reporting."""

    claim: Claim
    reference_key: Optional[str]
    reference_text: Optional[str]
    result: Optional[SupportResult]
    note: Optional[str] = None  # e.g. "reference not found", "source file missing"


_FLAG_EMOJI = {
    "supported": "OK",
    "weak support - review": "WEAK",
    "no clear support - flag": "FLAG",
}


def _sort_key(f: Finding):
    # Findings with no score (unresolved references) sort to the very top
    # as well, since a missing/unmatched reference is itself worth review.
    if f.result is None:
        return -1.0
    return f.result.score


def generate_report(findings: List[Finding], document_name: str = "document") -> str:
    """Render a list of :class:`Finding` records into a Markdown report
    string, sorted worst-support-first.
    """
    ordered = sorted(findings, key=_sort_key)

    lines: List[str] = []
    lines.append(f"# citeguard Report: {document_name}")
    lines.append("")
    lines.append(
        "This report lists every citation marker found in the document, "
        "paired with the sentence it was attached to (the *claim*), and a "
        "TF-IDF lexical-similarity support score against the cited source's "
        "text. **This is a heuristic screening tool, not an automated "
        "integrity judgment** -- low scores mean \"a human should look at "
        "this,\" not \"this is misconduct.\" See the project README for "
        "methodology and limitations."
    )
    lines.append("")

    total = len(ordered)
    n_flag = sum(1 for f in ordered if f.result and f.result.flag == "no clear support - flag")
    n_weak = sum(1 for f in ordered if f.result and f.result.flag == "weak support - review")
    n_ok = sum(1 for f in ordered if f.result and f.result.flag == "supported")
    n_unresolved = sum(1 for f in ordered if f.result is None)

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total citation-claim pairs checked: **{total}**")
    lines.append(f"- Flagged (no clear support): **{n_flag}**")
    lines.append(f"- Weak support (review recommended): **{n_weak}**")
    lines.append(f"- Supported: **{n_ok}**")
    if n_unresolved:
        lines.append(f"- Unresolved (reference or source text missing): **{n_unresolved}**")
    lines.append("")
    lines.append("Findings below are sorted **worst-support-first**.")
    lines.append("")
    lines.append("---")
    lines.append("")

    for i, f in enumerate(ordered, start=1):
        marker = f.claim.marker
        lines.append(f"## {i}. Citation marker `{marker.raw}` ({marker.style})")
        lines.append("")
        ref_desc = f.reference_key or ", ".join(marker.keys) or "(unresolved)"
        lines.append(f"- **Reference key:** `{ref_desc}`")
        if f.reference_text:
            lines.append(f"- **Reference:** {f.reference_text}")
        if f.result is not None:
            lines.append(f"- **Support score:** {f.result.score:.3f}")
            lines.append(f"- **Flag:** {_FLAG_EMOJI.get(f.result.flag, f.result.flag)} -- {f.result.flag}")
        if f.note:
            lines.append(f"- **Note:** {f.note}")
        lines.append("")
        lines.append("**Claim sentence:**")
        lines.append("")
        lines.append(f"> {f.claim.sentence}")
        lines.append("")
        if f.result is not None and f.result.best_passage:
            lines.append("**Best-matching passage in cited source:**")
            lines.append("")
            lines.append(f"> {f.result.best_passage}")
            lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
