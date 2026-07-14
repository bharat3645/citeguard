"""citeguard: offline citation-claim support verifier.

citeguard checks whether a citation placed next to a claim in a document is
actually supported by the text of the source it points to. It does this with
classic, fully-offline NLP (TF-IDF + cosine similarity) rather than calling
out to any external API or LLM for the core scoring path.

See README.md for the full problem statement, architecture, and limitations.
"""

__version__ = "0.1.0"
