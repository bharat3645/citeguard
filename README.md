# citeguard

**An offline citation-claim support verifier.** citeguard checks whether a
citation placed next to a claim in a document is actually supported by the
text of the source it points to — and flags citations that look "padded,"
misquoted, or (increasingly) hallucinated by AI-assisted writing tools.

```
$ citeguard --document paper.txt --references refs.txt --sources ./sources/
```

## The problem

Citations are supposed to be verifiable evidence: "X is true [12]" should
mean that source 12 actually supports X. In practice this link quietly
breaks all the time:

- **Citation padding** — a source is cited because it's topically adjacent
  or because "something needs to go here," not because it supports the
  specific claim.
- **Misquotes / over-extrapolation** — a source shows a modest effect and
  the citing sentence claims something much stronger.
- **AI-assisted hallucinated relevance** — LLM drafting tools are
  increasingly used to write literature sections, and they are known to
  attach plausible-sounding but unsupported citations to claims.

Manually re-reading every cited source next to every claim that cites it is
extremely tedious, so in practice it mostly doesn't happen — reviewers
check citation *format*, not citation *substance*. citeguard automates the
first pass: it re-reads every cited source for you and tells you which
citation-claim pairs look suspicious enough to deserve a human's attention.

## Why this is unique

citeguard is not a plagiarism checker and not a citation-format linter:

| Tool type | Checks | Does NOT check |
|---|---|---|
| Plagiarism checker (Turnitin, etc.) | Whether *your text* copies *someone else's text* | Whether your citations support your claims |
| Citation-format linter (BibTeX/CSL tools) | Whether citations are *formatted* correctly (style, punctuation, field completeness) | Whether the citation is *substantively* correct |
| **citeguard** | Whether the *content* of the cited source actually supports the *specific claim* next to the citation marker | Formatting, plagiarism, grammar |

It also runs **fully offline**: the entire scoring pipeline is classical
TF-IDF + cosine similarity (`scikit-learn`), not a hosted embedding or LLM
API. No document text or source text ever leaves the machine — which
matters for pre-publication academic work, confidential reports, and
anything under an NDA. (An *optional* LLM layer can generate richer
natural-language explanations of a flag if you provide an API key, but the
core detection pipeline never requires it.)

## How it works (architecture)

```
 document.txt          references.txt         sources/ (one .txt per source)
      |                        |                          |
      v                        v                          v
 citeguard.markers      citeguard.references        citeguard.corpus
 extract_claims()       parse_references()          load_corpus()
 (marker + sentence)    (key -> raw ref text)        (key -> passages)
      |                        |                          |
      +------------------------+--------------------------+
                               |
                               v
                     citeguard.pipeline.build_findings()
                     resolve marker -> reference -> source passages
                               |
                               v
                     citeguard.similarity.score_claim_against_passages()
                     TF-IDF cosine similarity, max over passages
                               |
                               v
                     citeguard.report.generate_report()
                     Markdown, sorted worst-support-first
```

1. **`citeguard.markers`** — regex-based extraction of citation markers
   (numeric `[12]` / `[12, 14]` / `[3-5]`, and author-year
   `(Smith et al., 2020)` / `(Smith & Jones, 2019)` / `(Smith, 2020; Jones, 2021)`),
   paired with the sentence each marker appears in (the "claim"), using a
   dependency-free regex sentence splitter. This is deliberately the
   module with the most invested effort and the most documented
   limitations — see the docstring in `citeguard/markers.py`.
2. **`citeguard.references`** — parses a References/Bibliography section
   into `{key, raw_text}` entries, auto-detecting numbered vs. author-year
   style per entry (so a document can mix both conventions), using the
   *same* key-normalization rules as the marker extractor so markers and
   references line up automatically.
3. **`citeguard.corpus`** — loads a directory of plain-text source files,
   paragraph-splits each into candidate passages. See "Source file
   convention" below.
4. **`citeguard.similarity`** — TF-IDF vectorizes the claim sentence and
   every passage in the cited source, takes the max cosine similarity as
   the support score. Uses `scikit-learn`'s `TfidfVectorizer` when
   available; falls back automatically to a small NumPy-only TF-IDF
   implementation if `scikit-learn` isn't installed, so the tool degrades
   gracefully rather than hard-failing.
5. **`citeguard.report`** — renders a Markdown report, sorted
   worst-support-first, so the riskiest citations are reviewed first.
6. **`citeguard.llm`** — optional `explain_flag()` layer; deterministic
   templated explanation offline, real Anthropic API call if you supply a
   client / set `ANTHROPIC_API_KEY`.

### Source file convention

Each source file's reference key comes from its filename, with one
override:

- **Filename-as-key (default):** `12.txt` → key `"12"`; `smith2020.txt` →
  key `"smith2020"`.
- **Explicit key line (override):** if the file's *first line* is exactly
  `KEY: <key>`, that key is used instead and the line is stripped before
  paragraph-splitting. Useful when a natural filename doesn't match the
  citation key.

Passages are paragraph-split (blank-line separated); single newlines
within a paragraph are treated as soft-wrapping and joined with a space.

### Support-score thresholds

| Score | Flag |
|---|---|
| `> 0.35` | supported |
| `0.15 – 0.35` | weak support — review |
| `< 0.15` | no clear support — flag |

These are heuristic starting points tuned against short academic-style
sentences, not calibrated ground truth — see **Limitations** below.

## Install

```bash
git clone https://github.com/bharat3645/citeguard.git
cd citeguard
pip install -r requirements.txt
pip install -e .          # installs the `citeguard` CLI entry point
```

Requires Python 3.8+. Only `scikit-learn` and `numpy` are required for the
core pipeline; `anthropic` is optional (only needed for the real-LLM path
of `explain_flag`).

## Usage

```bash
citeguard --document examples/document.txt \
          --references examples/references.txt \
          --sources examples/sources \
          --output report.md
```

Or as a library:

```python
from citeguard.pipeline import run

report_md = run(
    document_text=open("examples/document.txt").read(),
    references_text=open("examples/references.txt").read(),
    source_dir="examples/sources",
)
print(report_md)
```

The `examples/` directory in this repo contains a small worked example
(`document.txt`, `references.txt`, `sources/`) with a deliberately planted
citation-padding case: `(Nguyen et al., 2021)` is cited once legitimately
(next to a claim about marine heatwave frequency, which the source
actually discusses) and once illegitimately (reused next to an unrelated
claim about technology-sector earnings). Running citeguard against it
produces, among others:

```
## 1. Citation marker `(Nguyen et al., 2021)` (author-year)

- **Reference key:** `nguyen2021`
- **Reference:** Nguyen, T., Park, S., & Ibrahim, K. (2021). Marine Heatwave
  Frequency Under a Warming Climate. Climate Dynamics.
- **Support score:** 0.000
- **Flag:** FLAG -- no clear support - flag

**Claim sentence:**

> ...quarterly earnings for major technology firms exceeded analyst
> expectations in the same period [3], a trend some commentators have
> controversially attributed to consumer sentiment shifts (Nguyen et al.,
> 2021).

**Best-matching passage in cited source:**

> We analyze forty years of sea surface temperature records and find a
> statistically significant increase in the frequency and duration of
> marine heatwave events...
```

...while the *legitimate* use of the same citation two sentences earlier
scores 0.422 ("supported"). This is exactly the pattern citeguard is built
to surface: the same reference, reused, only one use actually backed by
the source. See `examples/report.md` for the full generated report.

## Running the tests

```bash
pip install -r requirements.txt
pytest
```

All tests run fully offline (no network calls) and cover: marker
extraction (both citation styles, multi-citation sentences, edge cases),
reference-list parsing (numeric, author-year, and mixed lists), TF-IDF
similarity scoring (verifying score direction on synthetic
supported-vs-unrelated fixtures), report generation, and an
end-to-end CLI run via `subprocess`.

## Limitations

**citeguard is a heuristic screening tool, not a fact-checker.** Please
read this section before relying on its output for anything important.

- **TF-IDF cosine similarity measures lexical overlap, not entailment.**
  A claim can be well-supported by a passage that shares almost no
  vocabulary with it (paraphrase, synonyms, translated terminology) — this
  will produce a false "no clear support" flag. Conversely, a passage can
  share substantial vocabulary with a claim while actually contradicting
  it, negating it, or discussing a superficially similar but distinct
  point — this will produce a false "supported" score. citeguard cannot
  detect negation, sarcasm, or logical entailment.
- **Sentence-boundary detection is a simple regex heuristic**, not a
  trained NLP model. It handles common abbreviations (`et al.`, `Dr.`,
  `e.g.`, single-letter initials) but will occasionally mis-split on
  abbreviations it doesn't recognize, or on unusual punctuation. See
  `citeguard/markers.py` for the exact rules and known edge cases.
  Because a "claim" is defined as "the sentence containing the marker,"
  a mis-split sentence boundary can pull in too much or too little
  context, which will skew the score for that claim.
- **Short-text TF-IDF is sensitive to corpus size and vocabulary size.**
  Scores are not calibrated probabilities; they are relative rankings
  useful for triage, and the suggested thresholds (0.35 / 0.15) are
  starting points, not validated cutoffs. Longer or more technical
  passages/claims will generally need re-tuned thresholds.
  Re-run against your own known-good and known-bad citation examples
  before trusting the default thresholds for a new domain.
- **This tool does NOT make automated integrity judgments.** A low score
  means "a human should look at this pairing," never "this citation is
  fraudulent" or "this author did something wrong." Legitimate reasons for
  low scores include paraphrase, table/figure-only support (no prose
  passage to match against), and non-English source excerpts. Please treat
  every flagged item as a candidate for manual review, not a verdict.
- **The optional LLM explanation layer** (`citeguard.llm.explain_flag`)
  is not part of the offline guarantee: without a client/API key it
  returns a deterministic templated explanation (this is the only path
  covered by the test suite); with a key, it calls the Anthropic API and
  inherits all the usual caveats of LLM-generated text (potential
  hallucination, non-determinism, and it sends claim/passage text to a
  third-party API — do not enable it for confidential material).

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Bharat Singh Parihar.
