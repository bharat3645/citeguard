"""Optional LLM-backed explanation layer.

``explain_flag`` produces a short, human-readable explanation of *why* a
claim/citation pair was flagged. Without an LLM client (the default, and
the only path exercised by the test suite), it returns a deterministic
templated explanation derived from simple lexical-overlap statistics --
still fully offline, no network call, no API key required.

If an Anthropic client is supplied (or ``ANTHROPIC_API_KEY`` is set and the
optional ``anthropic`` package is installed), a real call is made to get a
richer, model-generated explanation. This path is real integration code,
but it is NOT part of the offline guarantee/test suite: citeguard's core
scoring and reporting never require it.
"""

from __future__ import annotations

import os
import re
from typing import Optional

_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "is",
    "are", "was", "were", "be", "been", "by", "with", "as", "at", "that",
    "this", "it", "its", "from", "than", "these", "those", "which", "who",
    "has", "have", "had", "not", "but", "also", "such",
}


def _content_words(text: str) -> set:
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 2}


def _templated_explanation(claim: str, best_passage: str) -> str:
    claim_words = _content_words(claim)
    passage_words = _content_words(best_passage)
    overlap = claim_words & passage_words
    claim_only = claim_words - passage_words

    if not best_passage.strip():
        return (
            "No candidate passage was available from the cited source, so "
            "no lexical overlap could be computed. Flag for manual review."
        )

    if overlap:
        shared = ", ".join(sorted(overlap)[:6])
        missing = ", ".join(sorted(claim_only)[:6]) if claim_only else "none notably"
        return (
            f"The cited passage shares some vocabulary with the claim "
            f"(overlapping terms: {shared}), but overall lexical overlap is "
            f"low. Terms emphasized in the claim but largely absent from the "
            f"passage: {missing}. Low lexical overlap suggests the source "
            f"may discuss a related but distinct topic -- the citation "
            f"should be checked manually for whether it actually supports "
            f"this specific claim."
        )

    claim_terms = ", ".join(sorted(claim_only)[:6]) if claim_only else "the claim's key terms"
    return (
        f"The cited passage does not share any of the claim's key content "
        f"words ({claim_terms}). The passage appears to discuss a different "
        f"topic than what the claim asserts -- low lexical overlap suggests "
        f"a possible citation mismatch. This is a heuristic signal, not "
        f"proof of an incorrect citation; please verify manually."
    )


def explain_flag(claim: str, best_passage: str, llm_client=None) -> str:
    """Return a short explanation of why a claim/citation pair was flagged.

    Parameters
    ----------
    claim:
        The claim sentence extracted from the document.
    best_passage:
        The best-matching passage found in the cited source.
    llm_client:
        Optional pre-constructed Anthropic client (``anthropic.Anthropic()``
        instance) or any object exposing a compatible
        ``messages.create(...)`` method. If ``None`` and no
        ``ANTHROPIC_API_KEY`` environment variable is set (or the optional
        ``anthropic`` package is not installed), a deterministic templated
        explanation is returned instead -- this is the path exercised by
        the test suite and requires no network access.
    """
    client = llm_client
    if client is None and os.environ.get("ANTHROPIC_API_KEY"):
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic()
        except ImportError:
            client = None

    if client is None:
        return _templated_explanation(claim, best_passage)

    # Real LLM integration path (not exercised offline / in CI).
    prompt = (
        "You are assisting a researcher in reviewing a citation. "
        "A claim in a paper and the best-matching passage from the cited "
        "source are given below. In 2-3 sentences, explain whether the "
        "passage plausibly supports the claim, and if not, what the "
        "passage actually discusses instead.\n\n"
        f"Claim: {claim}\n\n"
        f"Best-matching passage from cited source: {best_passage}\n"
    )
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        # Anthropic SDK responses expose content as a list of blocks.
        content = getattr(response, "content", None)
        if content and hasattr(content[0], "text"):
            return content[0].text.strip()
        return str(response)
    except Exception as exc:  # pragma: no cover - network/SDK errors
        return (
            f"[LLM explanation unavailable ({exc.__class__.__name__}); "
            "falling back to templated explanation] "
            + _templated_explanation(claim, best_passage)
        )
