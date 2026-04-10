# NMA Assumptions: Assessment and Reporting

**Time**: 10 minutes
**Purpose**: Understand and assess the three key NMA assumptions

---

## The Three Assumptions

Network meta-analysis requires three assumptions beyond those of standard pairwise meta-analysis:

1. **Homogeneity** — Studies within each comparison are similar
2. **Transitivity** — Study characteristics are balanced across comparisons
3. **Consistency** — Direct and indirect evidence agree

These are hierarchical: consistency requires transitivity, which requires homogeneity.

---

## 1. Homogeneity

### What It Means
Studies comparing the same pair of treatments should be sufficiently similar in design, population, and outcomes. This is the same assumption as in standard pairwise MA.

### How to Assess
- **I² statistic**: Proportion of variance due to heterogeneity
  - < 25%: low, 25-75%: moderate, > 75%: high
- **Cochran's Q test**: Significance test for heterogeneity
- **Prediction intervals**: Range of plausible effects in future studies
- **Forest plots**: Visual inspection for outliers

### How to Report
> "Heterogeneity was assessed using the I² statistic and Cochran's Q test. Prediction intervals were calculated to quantify the range of plausible treatment effects."

---

## 2. Transitivity

### What It Means
The distribution of **effect modifiers** should be similar across the different treatment comparisons in the network. If patients in A vs B trials are systematically different from patients in B vs C trials, the indirect comparison of A vs C will be biased.

### Common Effect Modifiers
- Age, sex distribution
- Disease severity/stage
- Prior treatment history
- Risk of bias level
- Follow-up duration
- Dose and schedule
- Year of publication

### How to Assess

Transitivity cannot be tested statistically — it is assessed through clinical judgment:

1. **Create a table** of study characteristics grouped by comparison:

| Characteristic | A vs B studies | B vs C studies | A vs C studies |
|---------------|----------------|----------------|----------------|
| Mean age | 55 ± 8 | 58 ± 7 | 54 ± 9 |
| % Female | 45% | 48% | 42% |
| Disease stage | II-III | II-III | II-IV |
| Median FU (mo) | 24 | 18 | 30 |

2. **Check for systematic differences** that could modify treatment effects
3. **Document your assessment** in the protocol and manuscript

### How to Report
> "We assessed transitivity by comparing the distribution of potential effect modifiers (age, disease stage, prior treatment, follow-up duration) across the different treatment comparisons. [Table X] summarizes study characteristics stratified by comparison."

### Red Flags
- Different populations across comparisons (e.g., early-stage vs advanced)
- Different outcome definitions
- Different follow-up durations
- Different eras of study conduct (evolving standard of care)

---

## 3. Consistency

### What It Means
For any comparison where both direct and indirect evidence exist, these two sources should agree (within statistical uncertainty).

### How to Assess

#### Global Test: Design Decomposition

```r
dd <- decomp.design(net_re)
# Q_between-designs: tests for inconsistency across study designs
# p < 0.05 → significant global inconsistency
```

Decomposes the total heterogeneity/inconsistency into:
- **Within-designs** Q: heterogeneity within each design
- **Between-designs** Q: inconsistency between designs

#### Visual: Net Heat Plot

```r
netheat(net_re, random = TRUE)
```

Colors indicate inconsistency between pairs of network designs. Hot colors (red) suggest problematic design combinations.

#### Local Test: Node-Splitting

```r
ns <- netsplit(net_re)
print(ns)
forest(ns)
```

For each comparison with both direct and indirect evidence:
- Compares the direct estimate, indirect estimate, and NMA estimate
- p < 0.10 suggests local inconsistency for that comparison

### How to Report
> "Consistency was evaluated globally using the design-by-treatment interaction test (Q = X.XX, p = X.XX) and locally using node-splitting for all comparisons with direct and indirect evidence. [Figure X] shows the net heat plot."

### When Inconsistency Is Detected

1. **Investigate sources**: Check if specific studies or comparisons drive it
2. **Assess clinical plausibility**: Could different study characteristics explain the discrepancy?
3. **Sensitivity analyses**: Remove problematic studies or comparisons
4. **Report transparently**: Do not hide inconsistency
5. **Consider limitations**: Downgrade GRADE certainty if inconsistency is unexplained

---

## Reporting Template

Include this paragraph (adapted) in your Methods section:

> "We assessed the transitivity assumption by comparing the distribution of potential effect modifiers across treatment comparisons [Table X]. Consistency was evaluated using the design-by-treatment interaction model (global test) and node-splitting (local tests) for all comparisons informed by both direct and indirect evidence. The net heat plot was used to visually identify inconsistent design pairs."

---

## See Also

- [NMA Overview](nma-overview.md) — When to use NMA
- [NMA R Guide](nma-r-guide.md) — Code for all assessment methods
- [NMA Reporting Checklist](nma-reporting-checklist.md) — PRISMA-NMA items 15, 16, 25
