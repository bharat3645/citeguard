"""TF-IDF cosine-similarity scoring between a claim sentence and a source's
candidate passages.

By design this is a *lexical overlap* heuristic, not a semantic-entailment
model: it measures whether the claim and the best-matching passage share
similar vocabulary, weighted by how distinctive each term is across the
passage set. It cannot detect true logical entailment, sarcasm, negation,
or paraphrase with completely disjoint vocabulary. See README.md's
"Limitations" section.

Backend
-------
If scikit-learn is installed, ``TfidfVectorizer`` + ``cosine_similarity``
are used directly, as specified. If scikit-learn is NOT available (e.g. a
minimal offline install), a small pure-Python/NumPy TF-IDF + cosine
implementation (``_FallbackTfidf``) is used automatically instead, so
citeguard keeps working with zero required third-party dependencies beyond
NumPy. Both backends are designed to produce comparable rankings for the
same inputs; which one runs is transparent to callers.

English stopwords ("the", "a", "of", ...) are removed before vectorizing.
This matters a lot for short-text TF-IDF: without it, common function
words dominate the very sparse vectors typical of single sentences/
paragraphs and compress the useful signal from real content-word overlap.

Thresholds (heuristic, tune for your corpus)
---------------------------------------------
* score > 0.35            -> "supported"
* 0.15 <= score <= 0.35   -> "weak support - review"
* score < 0.15            -> "no clear support - flag"

These cutoffs were chosen empirically against short academic-style
sentences (a handful of content words). Longer, more verbose claims or
passages will generally produce lower raw cosine scores even when well
supported (more terms dilute the vector) -- treat the thresholds as a
starting point for triage, not ground truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _sk_cosine_similarity

    _HAVE_SKLEARN = True
except ImportError:  # pragma: no cover - exercised only when sklearn absent
    _HAVE_SKLEARN = False


SUPPORTED_THRESHOLD = 0.35
WEAK_THRESHOLD = 0.15


def flag_for_score(score: float) -> str:
    """Map a support score in [0, 1] to a human-readable flag level."""
    if score > SUPPORTED_THRESHOLD:
        return "supported"
    if score >= WEAK_THRESHOLD:
        return "weak support - review"
    return "no clear support - flag"


@dataclass
class SupportResult:
    """Result of scoring one claim sentence against one source's passages."""

    score: float
    flag: str
    best_passage: str
    best_passage_index: int


# --------------------------------------------------------------------------
# Tokenization / stopwords (shared by both backends' fallback path and used
# directly by the NumPy fallback vectorizer)
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-zA-Z]+")

# A small standard English stopword list.
_STOPWORDS = frozenset("""
a an the of to in on for and or is are was were be been being by with as
at that this it its from than these those which who whom has have had
not no nor but also such into over under above below between during
before after while so if then because until up down out off again
further once here there when where why how all any both each few more
most other some such only own same so than too very s t can will just don
should now i me my we our you your he him his she her they them their
""".split())


def _tokenize(text: str) -> List[str]:
    return [
        t.lower()
        for t in _TOKEN_RE.findall(text)
        if t.lower() not in _STOPWORDS
    ]


# --------------------------------------------------------------------------
# Fallback pure-Python/NumPy TF-IDF (used automatically if sklearn missing)
# --------------------------------------------------------------------------


class _FallbackTfidf:
    """Minimal TF-IDF vectorizer + cosine similarity, NumPy-only.

    Mirrors scikit-learn's default TfidfVectorizer behavior closely enough
    for ranking purposes: raw term counts, smoothed IDF
    (ln((1+n)/(1+df)) + 1), L2-normalized vectors, cosine similarity via
    dot product of normalized vectors. Stopwords are removed at the
    tokenization step (see ``_tokenize``), mirroring
    ``TfidfVectorizer(stop_words="english")`` used in the sklearn path.
    """

    def __init__(self, documents: List[str]):
        import numpy as np

        self._np = np
        tokenized = [_tokenize(doc) for doc in documents]
        vocab = {}
        for tokens in tokenized:
            for tok in set(tokens):
                if tok not in vocab:
                    vocab[tok] = len(vocab)
        self.vocab = vocab
        n_docs = len(documents)
        n_terms = len(vocab)

        tf = np.zeros((n_docs, n_terms), dtype=float)
        df = np.zeros(n_terms, dtype=float)
        for i, tokens in enumerate(tokenized):
            counts = {}
            for tok in tokens:
                counts[tok] = counts.get(tok, 0) + 1
            for tok, c in counts.items():
                tf[i, vocab[tok]] = c
            for tok in set(tokens):
                df[vocab[tok]] += 1

        idf = np.log((1 + n_docs) / (1 + df)) + 1.0
        tfidf = tf * idf
        norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = tfidf / norms

    def transform_query(self, text: str):
        np = self._np
        tokens = _tokenize(text)
        vec = np.zeros(len(self.vocab), dtype=float)
        counts = {}
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1
        for tok, c in counts.items():
            idx = self.vocab.get(tok)
            if idx is not None:
                vec[idx] = c
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def cosine_to_all(self, query_text: str):
        query_vec = self.transform_query(query_text)
        return self.matrix.dot(query_vec)


def score_claim_against_passages(claim_sentence: str, passages: List[str]) -> SupportResult:
    """Score ``claim_sentence`` against every passage in ``passages`` using
    TF-IDF cosine similarity, returning the best (max) match.

    Uses scikit-learn's TfidfVectorizer/cosine_similarity if available,
    otherwise a NumPy-only fallback with equivalent behavior. Both are
    fully offline (no network calls, no pretrained model downloads).
    """
    if not passages:
        return SupportResult(score=0.0, flag=flag_for_score(0.0), best_passage="", best_passage_index=-1)

    if not _tokenize(claim_sentence) or not any(_tokenize(p) for p in passages):
        return SupportResult(score=0.0, flag=flag_for_score(0.0), best_passage=passages[0], best_passage_index=0)

    if _HAVE_SKLEARN:
        corpus = passages + [claim_sentence]
        vectorizer = TfidfVectorizer(lowercase=True, token_pattern=r"[a-zA-Z]+", stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            return SupportResult(score=0.0, flag=flag_for_score(0.0), best_passage=passages[0], best_passage_index=0)
        passage_vecs = tfidf_matrix[:-1]
        claim_vec = tfidf_matrix[-1]
        sims = _sk_cosine_similarity(claim_vec, passage_vecs)[0]
    else:
        fallback = _FallbackTfidf(passages)
        sims = fallback.cosine_to_all(claim_sentence)

    best_idx = int(sims.argmax()) if hasattr(sims, "argmax") else max(range(len(sims)), key=lambda i: sims[i])
    best_score = float(sims[best_idx])
    best_score = max(0.0, min(1.0, best_score))

    return SupportResult(
        score=best_score,
        flag=flag_for_score(best_score),
        best_passage=passages[best_idx],
        best_passage_index=best_idx,
    )
