# Manuscript Assembly Guide

**Reference**: This file is referenced from CLAUDE.md
**When to use**: After Stage 06 analysis complete

---

## When User Says "Complete Manuscript" or "Prepare for Submission"

Use the **meta-manuscript-assembly** skill (`~/.claude/skills/meta-manuscript-assembly/SKILL.md`):

**Triggers**:

- "complete the manuscript"
- "prepare for journal submission"
- "create publication tables"
- "assemble figures for submission"
- "ready to submit"

**5-Phase Workflow**:

1. **Quarto Manuscript Setup** (30 min)
   - Create Quarto document structure (`index.qmd`)
   - Configure YAML frontmatter with bibliography
   - Set output formats: HTML, PDF, DOCX
   - Output directory: `07_manuscript/output/`

2. **Content Writing with Citation Keys** (2-3 hours)
   - Write sections in Quarto markdown
   - Use citation keys: `[@smith2020]` or `@smith2020`
   - Embed figures: `![Caption](figures/figure1.png){#fig-pcr}`
   - Embed tables: `@tbl-characteristics` with Quarto tables
   - Cross-reference: `@fig-pcr`, `@tbl-efficacy`

3. **Figure Assembly** (1-2 hours)
   - Use R for all plot generation (ggplot2, forest plots, etc.)
   - Export from R using `ggsave()` with `dpi=300`
   - Use R packages for multi-panel assembly (patchwork, cowplot)
   - Export to `07_manuscript/figures/` at 300 DPI
   - Add professional panel labels (A, B, C) in R
   - Reference in Quarto: `![Figure 1](figures/figure1.png){#fig-1}`

4. **Tables Integration** (1-2 hours)
   - Generate tables in R using `gt` + `flextable` (see `06_analysis/07_export_tables.R`)
   - Export as PNG, HTML, and DOCX via `gtsave()` and `save_as_docx()`
   - Reference PNG images in `tables.qmd` as standalone images:

     ```markdown
     ## Table 1. Trial Characteristics {#tbl-characteristics}

     ![](tables/table1_characteristics.png){width=100%}
     ```

   - Why PNG? Consistent rendering across all output formats, publication-quality formatting

5. **Sync & Render** (30 min)
   - Use Makefile to sync from `06_analysis/` and render:
     ```bash
     cd 07_manuscript/
     make sync     # Copy figures + table PNGs from 06_analysis
     make docx     # Render Word (tables as embedded PNG images)
     make html     # Render self-contained HTML
     make pdf      # Render PDF via Typst
     make          # All of the above
     ```
   - Outputs: `index.html`, `index.pdf`, `index.docx`

6. **References** (30 min)
   - Create `references.bib` with all citations
   - Configure CSL style (e.g., `apa.csl`, `american-medical-association.csl`, `lancet.csl`)

7. **Quality Assurance** (30-60 min)
   - Verify all citations resolved
   - Check figure/table cross-references
   - Validate output formats
   - PRISMA 2020 checklist

**Expected output**: Multi-format manuscript (HTML/PDF/DOCX) in 6-8 hours

**Alternative skill for figure assembly only**: Use **scientific-figure-assembly** skill when user says:

- "combine plots into figure"
- "create multi-panel figure"
- "add panel labels"
- "assemble figures at 300 DPI"

---

## Quarto Manuscript Structure

### Required Files

```
07_manuscript/
├── index.qmd                 # Main manuscript (includes all sections)
├── 00_abstract.qmd           # Abstract
├── 01_introduction.qmd       # Introduction
├── 02_methods.qmd            # Methods
├── 03_results.qmd            # Results
├── 04_discussion.qmd         # Discussion
├── tables.qmd                # Tables (standalone PNG images)
├── figures_legends.qmd       # Figure legends with embedded PNGs
├── Makefile                  # Sync + render automation
├── references.bib            # BibTeX bibliography
├── style.csl                 # Citation style (AMA, Lancet, etc.)
├── figures/                  # ← Synced from 06_analysis/figures/
│   ├── figure1_efs_forest.png
│   ├── figure2_os_forest.png
│   └── ...
├── tables/                   # ← Synced from 06_analysis/tables/
│   ├── table1_characteristics.png
│   ├── table2_rob2.png
│   └── ...
├── index.html                # Rendered HTML (self-contained)
├── index.pdf                 # Rendered PDF (via Typst)
└── index.docx                # Rendered Word (tables as PNG)
```

### Build & Sync from 06_analysis

The Makefile syncs analysis outputs before rendering:

```
06_analysis/                    07_manuscript/
├── figures/*.png    ──cp──→   ├── figures/*.png
├── tables/*.png     ──cp──→   ├── tables/*.png
└── tables/*.csv     ──cp──→   └── tables/*.csv
```

**Sync direction is one-way**: always regenerate from R scripts in `06_analysis/`, never edit PNGs in `07_manuscript/` directly. Re-run `make sync` after any analysis update.

### Quarto YAML Frontmatter

```yaml
---
title: "Your Meta-Analysis Title"
format:
  html:
    toc: true
    toc-depth: 3
    number-sections: true
    embed-resources: true # Self-contained HTML
  docx:
    toc: true
    number-sections: true # Tables render as embedded PNG images
  typst:
    toc: true
    number-sections: true
    columns: 1
    margin:
      x: 1in
      y: 1in
    papersize: us-letter
    mainfont: "New Computer Modern"
    fontsize: 11pt
bibliography: references.bib
csl: american-medical-association.csl # or lancet.csl, vancouver.csl
---
```

**Format notes**:

- **HTML**: `embed-resources: true` makes a single self-contained file
- **DOCX**: Tables appear as PNG images (no editable cells, but consistent formatting)
- **Typst**: Recommended over LaTeX for PDF (faster, cleaner output)

### Citation Examples

**In-text citations**:

```markdown
Previous studies [@smith2020; @jones2021] demonstrated...
According to @brown2019, the effect was...
Multiple trials [@keynote522; @impassion031; @geparnuevo] showed...
```

**Rendered as**:

- Previous studies (Smith et al., 2020; Jones et al., 2021) demonstrated...
- According to Brown (2019), the effect was...
- Multiple trials (Schmid et al., 2020; Mittendorf et al., 2020; ...) showed...

### Figure Integration

**Quarto syntax**:

```markdown
![Pathologic complete response rates. Forest plot showing risk ratios with 95% confidence intervals for the primary outcome across 5 randomized controlled trials (N=2402 patients). I²=0%, p=0.0015.](figures/figure1_pcr.png){#fig-pcr width=100%}

As shown in @fig-pcr, the addition of ICI to chemotherapy...
```

**Multi-panel figures**:

```markdown
![Efficacy outcomes. (A) Pathologic complete response; (B) Event-free survival; (C) Overall survival. All panels show forest plots with 95% CI.](figures/figure1_efficacy.png){#fig-efficacy}
```

### Table Integration

**Option 1: Standalone PNG images (Recommended for DOCX)**:

Generate tables in R with `gt` + `flextable`, export as PNG. Reference in `tables.qmd`:

```markdown
## Table 1. Trial Characteristics {#tbl-characteristics}

![](tables/table1_characteristics.png){width=100%}
```

The R export script (`06_analysis/07_export_tables.R`) produces 3 formats per table:

```r
library(gt); library(flextable)

export_table <- function(gt_tbl, ft_tbl, basename, vwidth = 800) {
  gt_tbl %>% gtsave(paste0("tables/", basename, ".html"))
  gt_tbl %>% gtsave(paste0("tables/", basename, ".png"), vwidth = vwidth)
  save_as_docx(ft_tbl, path = paste0("tables/", basename, ".docx"))
}
```

**Why PNG tables?**

- Consistent rendering across HTML, PDF, and DOCX
- Publication-quality formatting (colors, bold, footnotes) via `gt`
- No Quarto rendering issues with complex tables
- Single source of truth: R script generates everything

**Option 2: Quarto native tables** (good for simple tables):

```markdown
| Trial        | N    | ICI Regimen           | Control | pCR (ICI) | pCR (Control) |
| ------------ | ---- | --------------------- | ------- | --------- | ------------- |
| KEYNOTE-522  | 1174 | Pembrolizumab + chemo | Chemo   | 64.8%     | 51.2%         |
| IMpassion031 | 455  | Atezolizumab + chemo  | Chemo   | 57.6%     | 41.1%         |

: Trial Characteristics {#tbl-characteristics}

Reference in text: @tbl-characteristics shows...
```

**Option 3: Include external markdown**:

```markdown
{{< include tables/table1_characteristics.md >}}
```

**Option 4: Dynamic tables from R**:

````markdown
```{r}
#| label: tbl-efficacy
#| tbl-cap: "Efficacy outcomes summary"

library(knitr)
kable(efficacy_data)
```
````

### Cross-References

```markdown
As shown in @fig-pcr and @tbl-characteristics, the results...
See supplementary @fig-forest-pdl1 for subgroup analysis...
The safety profile (@tbl-safety) was acceptable...
```

### Rendering Commands

**Using Makefile (recommended)** — syncs from `06_analysis` before rendering:

```bash
cd projects/<project>/07_manuscript

make          # Sync + render all (HTML + PDF + DOCX)
make sync     # Copy latest figures/tables from 06_analysis
make html     # Sync + render HTML
make pdf      # Sync + render PDF via Typst
make docx     # Sync + render DOCX (tables as PNG images)
make clean    # Remove generated outputs
make view     # Render HTML + open in browser
```

**Direct Quarto commands** (no auto-sync):

```bash
quarto render index.qmd --to html
quarto render index.qmd --to typst   # PDF via Typst
quarto render index.qmd --to docx
```

**Preview while editing**:

```bash
quarto preview index.qmd
```

---

## Success Metrics

### Publication-Ready Manuscript Definition

A manuscript is "publication-ready" when:

- ✅ All sections complete (Abstract through Discussion)
- ✅ Word count within journal target ±10%
- ✅ All tables formatted and integrated in Quarto
- ✅ All figures assembled at 300 DPI with captions
- ✅ All references in `references.bib` with DOIs
- ✅ All citations use `[@key]` format (no manual numbering)
- ✅ All cross-references work (`@fig-*`, `@tbl-*`)
- ✅ Renders successfully to HTML, PDF, and DOCX
- ✅ Output files in `07_manuscript/output/`
- ✅ PRISMA 2020 checklist 27/27 items
- ✅ No placeholders (TBD, TODO, [ref needed])

**Time from "data extraction complete" → "publication-ready"**: 10-14 hours with skills

---

## Common Pitfalls to Avoid

Based on actual project experience:

### Tables

❌ **Don't**: Create tables in Word or markdown manually
✅ **Do**: Generate in R with `gt` + `flextable`, export as PNG

- Reason: Publication-quality formatting, consistent across all output formats, reproducible

❌ **Don't**: Edit table PNGs in `07_manuscript/tables/` directly
✅ **Do**: Edit R scripts in `06_analysis/`, re-export, then `make sync`

- Reason: Single source of truth, one-way sync from analysis to manuscript

❌ **Don't**: Embed calculations in tables
✅ **Do**: Calculate in R, export formatted results via `gt`

- Reason: Prevents transcription errors, reproducible

### Figures

❌ **Don't**: Manually combine figures in PowerPoint
✅ **Do**: Use R packages (patchwork, cowplot) for multi-panel figures

- Reason: Reproducible, maintains quality, saves 1-2 hours

❌ **Don't**: Export at default DPI
✅ **Do**: Always specify `dpi=300` in R ggsave

```r
# Example: Export high-resolution figure
ggsave("figures/figure1.png", width=10, height=8, dpi=300)
```

- Reason: Journals reject <300 DPI figures

❌ **Don't**: Use Python for plotting (legacy approach)
✅ **Do**: Use R for all statistical plots and figure assembly

- Reason: Better integration with meta-analysis workflow, publication-quality defaults

### References

❌ **Don't**: Format references manually
✅ **Do**: Use BibTeX + Pandoc/Zotero

- Reason: 50%+ time savings, prevents errors

❌ **Don't**: Insert citations during writing
✅ **Do**: Use placeholders [1], [2], format later

- Reason: Faster writing flow, easier reordering

---

## Version Control Best Practices

### Git Commit Strategy for Manuscripts

**Granular commits** (recommended):

```bash
# After completing each section
git add 07_manuscript/00_abstract.md
git commit -m "Complete abstract (396 words)"

git add 07_manuscript/01_introduction.md
git commit -m "Complete introduction (689 words)"

# After completing each table
git add 07_manuscript/tables/Table1_*.md
git commit -m "Add Table 1: Trial Characteristics (5 RCTs)"

# After figure assembly
git add 07_manuscript/figures/Figure1_*.png
git commit -m "Assemble Figure 1: 3-panel efficacy (300 DPI)"
```

**Benefits**:

- Easy to rollback specific sections
- Clear progress tracking
- Facilitates collaboration

**Batch commit** (alternative):

```bash
# After completing entire manuscript
git add 07_manuscript/
git commit -m "Complete manuscript for Lancet Oncology submission

- 5 sections (4,921 words)
- 7 tables (main + supplementary)
- 5 figures (300 DPI, multi-panel)
- 31 references (BibTeX)
- Ready for submission

Co-Authored-By: Claude <noreply@anthropic.com>"
```
