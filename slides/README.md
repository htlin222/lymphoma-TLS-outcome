# 5-minute talk slides — Lymphoma TLS outcome

A 10-slide reveal.js deck for a 5-minute conference talk on the rapid evidence synthesis at `projects/lymphoma-tls-outcome/`.

## Live URL

<https://htlin222.github.io/lymphoma-TLS-outcome/>

## What's in the deck

IMRaD compression for a clinician (heme-onc) audience:

1. Title + the bedside question
2. Why this question (gap in the literature)
3. Methods (rapid review framing, soft-pedalled)
4. Six-study characteristics table
5. Headline forest plot (Pool F minus Alavi, OR 3.31)
6. The catch — fragility of the pooled estimate, GRADE VERY LOW
7. Spontaneous vs treatment-induced TLS — different diseases
8. Bedside summary (4 clinical scenarios)
9. What this synthesis does NOT cover (ICI, CAR-T, BCL-2)
10. Take-homes + repo link

Each slide has a one-sentence speaker note for 5-minute pacing (press `s` for presenter view).

## Build locally

```bash
quarto render index.qmd
open _site/index.html
```

## Publish to GitHub Pages

```bash
quarto publish gh-pages
```

(One-time. Creates / updates the `gh-pages` branch and pushes. GitHub auto-serves from there.)

## Critical files

- `index.qmd` — the slides themselves
- `_quarto.yml` — revealjs project config
- `custom.scss` — minimal palette (clinical-presentation aesthetic)
- `figures/` — local copies of forest plots from `projects/lymphoma-tls-outcome/06_analysis/figures_v2/`

## Source manuscript

`projects/lymphoma-tls-outcome/07_manuscript/manuscript.qmd` (v3, post Round 2 peer review)
