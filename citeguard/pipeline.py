"""End-to-end pipeline wiring markers -> references -> corpus -> similarity
-> report together. This is the module the CLI (and library users) call
into directly.
"""

from __future__ import annotations

from typing import Dict, List

from .corpus import Source, load_corpus
from .markers import Claim, extract_claims
from .references import ReferenceEntry, parse_references, references_by_key
from .report import Finding, generate_report
from .similarity import score_claim_against_passages


def build_findings(
    document_text: str,
    references_text: str,
    source_dir: str,
) -> List[Finding]:
    """Run the full citeguard pipeline and return a list of Finding records
    (unsorted; citeguard.report.generate_report sorts them).
    """
    claims: List[Claim] = extract_claims(document_text)
    ref_entries: List[ReferenceEntry] = parse_references(references_text)
    refs_by_key: Dict[str, ReferenceEntry] = references_by_key(ref_entries)
    corpus: Dict[str, Source] = load_corpus(source_dir)

    findings: List[Finding] = []
    for claim in claims:
        keys = claim.marker.keys or ["?"]
        for key in keys:
            ref = refs_by_key.get(key)
            if ref is None:
                findings.append(
                    Finding(
                        claim=claim,
                        reference_key=key,
                        reference_text=None,
                        result=None,
                        note=f"No matching reference-list entry found for key '{key}'.",
                    )
                )
                continue

            source = corpus.get(ref.key)
            if source is None or not source.passages:
                findings.append(
                    Finding(
                        claim=claim,
                        reference_key=ref.key,
                        reference_text=ref.raw_text,
                        result=None,
                        note=f"No source text file found (or file is empty) for key '{ref.key}'.",
                    )
                )
                continue

            result = score_claim_against_passages(claim.sentence, source.passages)
            findings.append(
                Finding(
                    claim=claim,
                    reference_key=ref.key,
                    reference_text=ref.raw_text,
                    result=result,
                )
            )
    return findings


def run(document_text: str, references_text: str, source_dir: str, document_name: str = "document") -> str:
    """Run the pipeline end-to-end and return the rendered Markdown report."""
    findings = build_findings(document_text, references_text, source_dir)
    return generate_report(findings, document_name=document_name)
