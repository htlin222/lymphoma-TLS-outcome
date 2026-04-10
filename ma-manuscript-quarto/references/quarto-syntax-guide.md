# Quarto Syntax Guide for Meta-Analysis Manuscripts

Quick reference for writing `.qmd` manuscript files in the meta-pipe pipeline.
Based on official Quarto documentation (v1.4+).

---

## Project Configuration (`_quarto.yml`)

Place at the root of `07_manuscript/`:

```yaml
project:
  type: manuscript
  output-dir: _output

manuscript:
  article: index.qmd
  meca-bundle: true # JATS/MECA submission bundle

format:
  pdf:
    documentclass: article
    papersize: letter
    geometry:
      - margin=1in
    fontsize: 11pt
    linestretch: 2
    number-sections: true
    toc: false
    keep-tex: true
    fig-pos: "H"
    fig-dpi: 300
    fig-cap-location: bottom
    tbl-cap-location: top
  html:
    toc: true
    toc-depth: 3
    number-sections: true
  docx:
    number-sections: true
  jats: default

bibliography: references.bib
csl: style.csl
```

### Metadata Hierarchy

1. **Document YAML** (highest priority) -- frontmatter in each `.qmd`
2. **`_metadata.yml`** -- directory-level defaults
3. **`_quarto.yml`** (lowest) -- project-level defaults

Objects/arrays are **merged** across levels, not overwritten.

---

## Document Frontmatter (`index.qmd`)

```yaml
---
title: "Meta-analysis Manuscript Title"
author:
  - name: "First Author"
    affiliations:
      - name: "University Hospital"
        department: "Department of Medicine"
    orcid: "0000-0000-0000-0000"
    corresponding: true
    email: "author@example.com"
  - name: "Second Author"
    affiliations:
      - name: "Research Institute"
date: last-modified
abstract: |
  Background: ...
  Methods: ...
  Results: ...
  Conclusions: ...
keywords: [meta-analysis, systematic review, PRISMA]
---
```

---

## Cross-References

### Mandatory Prefixes

| Element  | Label Prefix | Example Label            |
| -------- | ------------ | ------------------------ |
| Figure   | `fig-`       | `{#fig-forest}`          |
| Table    | `tbl-`       | `{#tbl-characteristics}` |
| Section  | `sec-`       | `{#sec-methods}`         |
| Equation | `eq-`        | `{#eq-regression}`       |

### Rules

- Labels must be **lowercase**
- Use **hyphens** as separators (not underscores): `fig-forest-plot` not `fig_forest_plot`
- Prefixes are **mandatory** -- Quarto ignores labels without them
- Requires `number-sections: true` for section cross-refs

### Reference Syntax

```markdown
@fig-forest --> "Figure 1"
@tbl-characteristics --> "Table 1"
@sec-methods --> "Section 2"
@eq-regression --> "Equation 1"

[-@fig-forest] --> "1" (number only, no prefix)
[Fig. @fig-forest] --> "Fig. 1" (custom prefix)
[@fig-a; @fig-b; @fig-c] --> "Figures 1, 2, 3"
```

---

## Figures

### Basic Figure with Cross-Reference

```markdown
![Forest plot of primary outcome](figures/forest-primary.png){#fig-forest width=80%}

As shown in @fig-forest, the pooled effect...
```

### Figure Attributes

```markdown
![Caption](path.png){#fig-label width=80% fig-align="center" fig-alt="Alt text description"}
```

- `width`: `80%`, `300`, `4in`
- `fig-align`: `left`, `center` (default), `right`
- `fig-alt`: accessibility text (always include)
- `fig-pos`: `H` (here), `h`, `t` (top), `b` (bottom), `p` (page)

### Subfigures (Multi-Panel)

```markdown
::: {#fig-panels layout-ncol=2}

![Overall survival](figures/forest-os.png){#fig-forest-os}

![Progression-free survival](figures/forest-pfs.png){#fig-forest-pfs}

Forest plots by outcome
:::
```

Reference: `@fig-panels` (main), `@fig-forest-os` (subfigure A).

### Custom Layout

```markdown
::: {layout="[[1,1], [1]]"}
![Plot A](a.png)

![Plot B](b.png)

![Plot C](c.png)
:::
```

Negative values create spacing: `layout="[[40,-20,40], [100]]"`.

---

## Tables

### Pipe Table with Cross-Reference

```markdown
| Study      |   N |   RR (95% CI)    | Weight |
| ---------- | --: | :--------------: | -----: |
| Smith 2020 | 150 | 1.23 (0.95-1.60) |    22% |
| Jones 2021 | 200 | 1.45 (1.10-1.91) |    35% |

: Study characteristics {#tbl-characteristics}
```

Alignment: `:---` left, `---:` right, `:---:` center.

### Grid Table (for complex content)

```markdown
+-----------+----------+--------------------+
| Study | N | Key Findings |
+===========+==========+====================+
| Smith | 150 | - RR 1.23 |
| 2020 | | - p = 0.03 |
+-----------+----------+--------------------+
```

Grid tables support multi-line cells, lists, and code blocks.

### Column Widths

```markdown
: Caption {#tbl-data tbl-colwidths="[30,20,30,20]"}
```

### Subtables

```markdown
::: {#tbl-panel layout-ncol=2}

| Col A | Col B |
| ----- | ----- |
| 1     | 2     |

: RCTs {#tbl-rcts}

| Col A | Col B |
| ----- | ----- |
| 3     | 4     |

: Observational {#tbl-obs}

Studies by design
:::
```

### Caption Location

Set globally in YAML: `tbl-cap-location: top` (default) or per-table.

---

## Citations and Bibliography

### Citation Syntax

```markdown
[@smith2020] # Parenthetical: (Smith, 2020)
@smith2020 # In-text: Smith (2020)
[-@smith2020] # Suppress author: (2020)
[@smith2020; @jones2021] # Multiple
[@smith2020, pp. 33-35] # With locator
[see @smith2020; also @jones2021] # Prefix/suffix
```

### Bibliography Placement

By default, references appear at the end. To control placement:

```markdown
## References {.unnumbered}

::: {#refs}
:::
```

### Include Uncited References

```yaml
nocite: |
  @item1, @item2
```

### CSL Styles

**Pipeline default**: AMA (American Medical Association) — superscript numbered citations.

```yaml
csl: american-medical-association.csl
```

For alternative journals, override with the target journal CSL:

```yaml
csl: the-lancet.csl    # Lancet family
csl: jama.csl          # JAMA family (also uses AMA style)
csl: the-new-england-journal-of-medicine.csl  # NEJM (Vancouver-like)
```

Find styles at the [CSL Project repository](https://github.com/citation-style-language/styles) or [Zotero Style Repository](https://www.zotero.org/styles).

**See also**: `references/academic-writing-style.md` Rule 3 for full AMA citation, bibliography, and writing convention details.

---

## Includes and Page Breaks

### File Includes

```markdown
{{< include 01_introduction.qmd >}}
```

Paths are relative to the including file.

### Page Breaks

```markdown
{{< pagebreak >}}
```

**Do not** use `\newpage` -- it only works in LaTeX output. Use `{{< pagebreak >}}` for all formats.

---

## Callouts

```markdown
:::{.callout-note}
This finding should be interpreted with caution due to high heterogeneity.
:::
```

Types: `note`, `tip`, `warning`, `caution`, `important`.

With custom title:

```markdown
:::{.callout-warning}

## Limitation

Small sample sizes limit generalizability.
:::
```

---

## Text Formatting

```markdown
_italics_, **bold**, **_bold italics_**
Superscript^2^ / Subscript~2~
~~strikethrough~~
`verbatim code`
[Small caps]{.smallcaps}
[Underline]{.underline}
```

### Footnotes

```markdown
This is a claim[^1].

[^1]: Supporting detail here.

Also inline^[This is an inline footnote.].
```

---

## Equations

### Inline

```markdown
The pooled risk ratio was $RR = 1.26$ (95% CI 1.16--1.37).
```

### Display with Cross-Reference

```markdown
$$
\hat{\theta} = \frac{\sum w_i \theta_i}{\sum w_i}
$$ {#eq-pooled}

See @eq-pooled for the pooled estimate formula.
$$
```

---

## Format-Specific Raw Content

For content that should only appear in one output format:

````markdown
```{=latex}
\begin{landscape}
% Wide table here
\end{landscape}
```
````

````markdown
```{=html}
<details>
<summary>Click to expand</summary>
Additional content here.
</details>
```
````

---

## Journal Extensions

### Available Templates

```bash
# Create new article from template
quarto use template quarto-journals/plos

# Add format to existing document
quarto add quarto-journals/elsevier
```

Pre-built: ACM, PLOS, ASA, Elsevier, Biophysical Journal, ACS, JSS.

### Common Medical Journal CSL Files

| Journal         | CSL File                                  | Citation Style |
| --------------- | ----------------------------------------- | -------------- |
| **AMA (default)** | **`american-medical-association.csl`**  | **Superscript numbered** |
| Lancet          | `the-lancet.csl`                          | Superscript numbered |
| JAMA            | `jama.csl`                                | Superscript numbered (AMA) |
| BMJ             | `bmj.csl`                                 | Superscript numbered (Vancouver) |
| NEJM            | `the-new-england-journal-of-medicine.csl` | Superscript numbered |
| Nature Medicine | `nature-medicine.csl`                     | Superscript numbered |

---

## PDF-Specific Options

### Font Configuration (lualatex/xelatex)

```yaml
format:
  pdf:
    mainfont: "Times New Roman"
    sansfont: "Open Sans"
    monofont: "Roboto Mono"
    fontsize: 12pt
    linestretch: 1.5
```

### LaTeX Includes

```yaml
format:
  pdf:
    include-in-header:
      - text: |
          \usepackage{longtable}
          \usepackage{booktabs}
    include-before-body: preamble.tex
```

### Citation Method for PDF

```yaml
format:
  pdf:
    cite-method: citeproc # Default (most portable)
    # cite-method: natbib    # For natbib users
    # cite-method: biblatex  # For biblatex users
```

---

## Checklist for Meta-Analysis Manuscripts

- [ ] `_quarto.yml` uses `project: type: manuscript`
- [ ] All figures have `{#fig-label}` with `fig-` prefix
- [ ] All tables have `{#tbl-label}` with `tbl-` prefix
- [ ] All labels are lowercase with hyphens only
- [ ] Figure alt-text provided (`fig-alt`)
- [ ] Figures exported at 300 DPI minimum
- [ ] Citations use `[@key]` / `@key` syntax
- [ ] `references.bib` and CSL file present
- [ ] `{{< pagebreak >}}` used (not `\newpage`)
- [ ] `{#refs}` div placed for bibliography location
- [ ] PRISMA flow diagram included
- [ ] All result claims map to figures/tables
- [ ] `number-sections: true` enabled for cross-refs
