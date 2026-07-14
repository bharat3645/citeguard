# citeguard Report: document.txt

This report lists every citation marker found in the document, paired with the sentence it was attached to (the *claim*), and a TF-IDF lexical-similarity support score against the cited source's text. **This is a heuristic screening tool, not an automated integrity judgment** -- low scores mean "a human should look at this," not "this is misconduct." See the project README for methodology and limitations.

## Summary

- Total citation-claim pairs checked: **6**
- Flagged (no clear support): **1**
- Weak support (review recommended): **0**
- Supported: **5**

Findings below are sorted **worst-support-first**.

---

## 1. Citation marker `(Nguyen et al., 2021)` (author-year)

- **Reference key:** `nguyen2021`
- **Reference:** Nguyen, T., Park, S., & Ibrahim, K. (2021). Marine Heatwave Frequency Under a Warming Climate. Climate Dynamics.
- **Support score:** 0.000
- **Flag:** FLAG -- no clear support - flag

**Claim sentence:**

> Meanwhile,
quarterly earnings for major technology firms exceeded analyst expectations
in the same period [3], a trend some commentators have controversially
attributed to consumer sentiment shifts (Nguyen et al., 2021).

**Best-matching passage in cited source:**

> We analyze forty years of sea surface temperature records and find a statistically significant increase in the frequency and duration of marine heatwave events. Warming ocean temperatures are strongly associated with more frequent extreme thermal anomalies affecting marine ecosystems.

---

## 2. Citation marker `(Nguyen et al., 2021)` (author-year)

- **Reference key:** `nguyen2021`
- **Reference:** Nguyen, T., Park, S., & Ibrahim, K. (2021). Marine Heatwave Frequency Under a Warming Climate. Climate Dynamics.
- **Support score:** 0.422
- **Flag:** OK -- supported

**Claim sentence:**

> Some researchers have also linked rising temperatures to
increased frequency of marine heatwaves (Nguyen et al., 2021).

**Best-matching passage in cited source:**

> We analyze forty years of sea surface temperature records and find a statistically significant increase in the frequency and duration of marine heatwave events. Warming ocean temperatures are strongly associated with more frequent extreme thermal anomalies affecting marine ecosystems.

---

## 3. Citation marker `[3]` (numeric)

- **Reference key:** `3`
- **Reference:** T. Byrne, "Consumer Electronics Market Analysis," Tech Business Review, 2022.
- **Support score:** 0.430
- **Flag:** OK -- supported

**Claim sentence:**

> Meanwhile,
quarterly earnings for major technology firms exceeded analyst expectations
in the same period [3], a trend some commentators have controversially
attributed to consumer sentiment shifts (Nguyen et al., 2021).

**Best-matching passage in cited source:**

> Quarterly filings from major consumer electronics manufacturers show revenue growth of 8-12% year over year, exceeding average analyst forecasts. Strong demand for premium smartphone models was cited as the primary driver in earnings calls.

---

## 4. Citation marker `[2]` (numeric)

- **Reference key:** `2`
- **Reference:** R. Osei, "Shifting Ocean Current Patterns in the North Atlantic," Ocean Science Quarterly, 2019.
- **Support score:** 0.463
- **Flag:** OK -- supported

**Claim sentence:**

> Independent analyses of ocean buoy data confirm that current
patterns in the North Atlantic have shifted measurably over the last three
decades [2].

**Best-matching passage in cited source:**

> Using thirty years of ocean buoy telemetry, we document measurable shifts in current patterns within the North Atlantic subtropical gyre. These shifts correlate with changes in wind stress and surface temperature gradients across the basin.

---

## 5. Citation marker `[4]` (numeric)

- **Reference key:** `4`
- **Reference:** P. Adeyemi, "Sea Surface Temperature and Coral Bleaching Frequency," Marine Ecology Letters, 2021.
- **Support score:** 0.474
- **Flag:** OK -- supported

**Claim sentence:**

> Coral bleaching
events have become more frequent as sea surface temperatures rise [4].

**Best-matching passage in cited source:**

> Field surveys across the Great Barrier Reef and Caribbean reef systems recorded a marked increase in coral bleaching events between 2015 and 2021. Elevated sea surface temperature was the strongest predictor of bleaching severity across all surveyed sites.

---

## 6. Citation marker `[1]` (numeric)

- **Reference key:** `1`
- **Reference:** J. Alvarez, "Greenhouse Gas Emissions and Global Temperature Trends," Journal of Climate Science, 2020.
- **Support score:** 0.572
- **Flag:** OK -- supported

**Claim sentence:**

> Global average temperatures have increased by more than 1.1 degrees Celsius
since the pre-industrial era, primarily driven by human greenhouse gas
emissions [1].

**Best-matching passage in cited source:**

> This paper analyzes global temperature records from 1880 to 2020. We find that average surface temperatures have risen by approximately 1.1 degrees Celsius relative to the pre-industrial baseline. The dominant driver of this warming trend is anthropogenic greenhouse gas emissions, particularly carbon dioxide and methane released from fossil fuel combustion and industrial activity.

---
