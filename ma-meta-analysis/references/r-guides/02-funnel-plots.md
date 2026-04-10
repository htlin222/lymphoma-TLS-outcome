# Funnel Plots for Publication Bias Assessment

**When to use**: You need to assess publication bias visually and statistically
**Time**: 15-25 minutes
**Stage**: 06 (Analysis)

**Packages**:

```r
library(metafor)     # Funnel plot + statistical tests + selection models
library(meta)        # Alternative funnel plot
library(ggplot2)     # Custom funnel plot (optional)

# Optional (install as needed):
# library(metaviz)          # Sunset (power-enhanced) funnel plot
# library(PublicationBias)  # Sensitivity analysis + S-values
# library(RoBMA)            # Bayesian model-averaged publication bias
# library(puniform)         # p-uniform* method
# library(metasens)         # Copas selection model + limit meta-analysis
```

---

## Why Log Scale Matters for Funnel Plots

For **ratio measures** (HR, RR, OR), always plot on the **log scale**:

| Scale           | Confidence region               | Verdict                                        |
| --------------- | ------------------------------- | ---------------------------------------------- |
| Natural (HR/RR) | Asymmetric -- wider on one side | Misleading: fake "asymmetry" even without bias |
| Log (log HR/RR) | Symmetric                       | Correct: asymmetry = real evidence of bias     |

The reason: the standard error of log(HR) is symmetric, but the standard error
of HR itself is skewed. A symmetric funnel is the reference expectation, so you
can only judge departures from symmetry when the baseline IS symmetric.

### The Rule

```r
# For ratio measures (HR, RR, OR) with meta package:
funnel(model, backtransf = FALSE, xlab = "Log HR")

# For ratio measures with metafor package:
funnel(res)  # metafor already uses log scale internally
```

`backtransf = FALSE` is the key parameter for `meta::funnel()`. Without it,
the x-axis shows back-transformed values (HR, RR) and the shading is skewed.

For **continuous measures** (SMD, MD), no transformation needed -- the scale is
already linear and symmetric.

---

## Quick Start: Standard Funnel Plot

```r
library(metafor)

# Load data and fit model
data <- read.csv("05_extraction/extraction.csv")
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)
res <- rma(yi, vi, data = es, method = "REML")

# Basic funnel plot (300 DPI) -- metafor uses log scale by default
png("figures/funnel_plot.png", width = 7, height = 6, units = "in", res = 300)
funnel(res,
       xlab = "Log Risk Ratio",
       main = "Funnel Plot: Assessment of Publication Bias",
       back = "white",
       shade = "gray90",
       hlines = "gray80")
dev.off()
```

### Quick Start: meta Package (HR/RR/OR)

```r
library(meta)

# After fitting metagen/metabin with sm = "HR" / "RR" / "OR":
png("figures/funnel_plot.png", width = 7, height = 6, units = "in", res = 300)
funnel(meta_model,
       backtransf = FALSE,            # <-- KEY: keeps log scale
       studlab = TRUE, cex.studlab = 0.8,
       xlab = paste0("Log ", meta_model$sm),
       col = "navy", pch = 16)
dev.off()
```

### Quick Start: With Egger's Test Annotation

```r
library(meta)

# Egger's test
bias_test <- metabias(meta_model, method.bias = "linreg")

png("figures/funnel_with_egger.png", width = 7, height = 6, units = "in", res = 300)
funnel(meta_model, backtransf = FALSE,
       studlab = TRUE, cex.studlab = 0.8,
       xlab = paste0("Log ", meta_model$sm),
       col = "navy", pch = 16)
title(sub = sprintf("Egger's test: t = %.2f, p = %.3f",
                     bias_test$statistic, bias_test$p.value),
      cex.sub = 0.9, col.sub = "gray40")
dev.off()
```

---

## Statistical Tests for Asymmetry

### Egger's Regression Test

```r
# Egger's test (most common for continuous outcomes)
regtest(res, model = "lm")

# Interpretation:
# p < 0.10 -> Evidence of funnel plot asymmetry (possible bias)
# p >= 0.10 -> No strong evidence of asymmetry
```

**Note on binary outcomes (RR/OR)**: For binary outcomes, Peters' test is
preferred over Egger's test because Egger's test has inflated false-positive
rates when the outcome is rare. Peters' test uses sample size as the predictor
instead of standard error:

```r
# Peters' test for binary outcomes (RR, OR)
regtest(res, model = "lm", predictor = "ni")

# Interpretation is the same as Egger's: p < 0.10 suggests asymmetry
```

### Rank Correlation Test (Begg & Mazumdar)

```r
# Rank correlation test
ranktest(res)
```

### Trim-and-Fill Method

```r
# Trim-and-fill (estimates missing studies)
res_tf <- trimfill(res)
print(res_tf)

# Plot with imputed studies
png("figures/funnel_trimfill.png", width = 7, height = 6, units = "in", res = 300)
funnel(res_tf,
       xlab = "Log Risk Ratio",
       main = "Trim-and-Fill Funnel Plot")
dev.off()
```

**Note**: Trim-and-fill is a useful visual diagnostic but has known limitations
-- it assumes a specific mechanism of bias and can perform poorly when
heterogeneity is present. For bias-corrected effect estimates, prefer
selection models (see Scenario 4 below).

### Selection Models (Preferred for Bias-Corrected Estimates)

Selection models provide more principled bias correction than trim-and-fill
by modeling the probability that a study is published as a function of its
p-value. The three-parameter selection model (3PSM) is now the recommended
approach for estimating a bias-adjusted pooled effect.

```r
# Three-parameter selection model (3PSM)
# Models a step function in selection probability at alpha = 0.025 (one-sided)
res_sel <- selmodel(res, type = "stepfun", steps = 0.025)
print(res_sel)

# Compare original vs bias-corrected estimate
cat(sprintf("Original estimate:        %.3f (95%% CI: %.3f to %.3f)\n",
            res$beta[1], res$ci.lb, res$ci.ub))
cat(sprintf("Selection model estimate: %.3f (95%% CI: %.3f to %.3f)\n",
            res_sel$beta[1], res_sel$ci.lb, res_sel$ci.ub))
cat(sprintf("Likelihood ratio test: p = %.4f\n", res_sel$LRTp))

# Interpretation:
# If LRT p < 0.05 -> Evidence that selection affects the results
# Compare adjusted estimate to original -- large shift suggests bias
```

```r
# Beta selection model (smooth selection function)
# Alternative to step function; models selection weight as beta density
res_beta <- selmodel(res, type = "beta")
print(res_beta)
```

---

## Common Scenarios

### Scenario 1: Contour-Enhanced Funnel Plot

**Purpose**: Distinguish publication bias from heterogeneity

```r
library(metafor)

png("figures/funnel_contour.png", width = 7, height = 6, units = "in", res = 300)
funnel(res,
       level = c(90, 95, 99),
       shade = c("white", "gray85", "gray75"),
       refline = 0,
       xlab = "Log Risk Ratio",
       main = "Contour-Enhanced Funnel Plot")
legend("topright",
       c("p > 0.10", "0.05 < p < 0.10", "0.01 < p < 0.05", "p < 0.01"),
       fill = c("white", "gray85", "gray75", "gray60"),
       bty = "n", cex = 0.8)
dev.off()
```

### Scenario 2: Sunset (Power-Enhanced) Funnel Plot

**Purpose**: Show statistical power regions to identify underpowered studies

The sunset funnel plot overlays power contours, making it easy to see which
studies had adequate power and which fell in "twilight" or "dark" regions.

```r
# install.packages("metaviz")
library(metaviz)

png("figures/funnel_sunset.png", width = 7, height = 6, units = "in", res = 300)
viz_sunset(res,
           xlab = "Effect Size",
           ylab = "Standard Error",
           text_size = 3)
dev.off()

# Interpretation:
# White region  = adequate power (>80%)
# Gray region   = twilight zone (33-80% power)
# Dark region   = underpowered (<33% power)
# Studies in the dark zone are especially suspect for selective reporting
```

### Scenario 3: ggplot2 Custom Funnel Plot

**Purpose**: More visual control

```r
library(ggplot2)
library(metafor)

# Prepare data
df <- data.frame(
  yi = es$yi,
  sei = sqrt(es$vi),
  study = data$study_id
)

# ggplot2 funnel plot
p <- ggplot(df, aes(x = yi, y = sei)) +
  geom_point(size = 3, shape = 16) +
  geom_vline(xintercept = res$beta[1], linetype = "dashed", color = "gray50") +
  scale_y_reverse() +
  labs(
    x = "Effect Size (Log RR)",
    y = "Standard Error",
    title = "Funnel Plot"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold")
  )

ggsave("figures/funnel_ggplot.png", p, width = 8, height = 6, dpi = 300)
```

### Scenario 4: Publication Bias Summary Report

**Purpose**: Complete bias assessment for manuscript

```r
library(metafor)

res <- rma(yi, vi, data = es, method = "REML")

# 1. Egger's test (or Peters' test for binary outcomes)
egger <- regtest(res, model = "lm")

# 2. Rank correlation
rank <- ranktest(res)

# 3. Trim-and-fill (visual diagnostic)
tf <- trimfill(res)

# 4. Three-parameter selection model (bias-corrected estimate)
sel <- selmodel(res, type = "stepfun", steps = 0.025)

# 5. Fail-safe N (Rosenthal)
fsn <- fsn(yi, vi, data = es)

# Report
cat(sprintf("Publication Bias Assessment:\n"))
cat(sprintf("  Egger's test: z = %.2f, p = %.4f\n", egger$zval, egger$pval))
cat(sprintf("  Rank correlation: tau = %.3f, p = %.4f\n", rank$tau, rank$pval))
cat(sprintf("  Trim-and-fill: %d imputed studies\n", tf$k0))
cat(sprintf("  Selection model (3PSM) adjusted estimate: %.3f (p = %.4f)\n",
            sel$beta[1], sel$pval))
cat(sprintf("  Fail-safe N: %d\n", fsn$fsnum))
```

### Scenario 5: Sensitivity Analysis with PublicationBias Package

**Purpose**: Quantify how severe publication bias would need to be to change conclusions

```r
# install.packages("PublicationBias")
library(PublicationBias)
library(metafor)

# Sensitivity analysis: at what level of bias does significance vanish?
# q = 0 tests whether the effect could be entirely due to bias
sens <- pubbias_svalue(yi = es$yi,
                       vi = es$vi,
                       q = 0,
                       model_type = "robust",
                       favor_positive = TRUE)
print(sens)

# Interpretation:
# S-value = the severity of publication bias (as a ratio of the probability
# of publishing significant vs non-significant results) required to shift
# the pooled estimate to the null. Higher S-values = more robust results.
# S-value > 10 is generally considered robust.

# Bias-corrected meta-analysis at a specific selection ratio
corrected <- pubbias_meta(yi = es$yi,
                          vi = es$vi,
                          model_type = "robust",
                          selection_ratio = 4,
                          favor_positive = TRUE)
print(corrected)
```

### Scenario 6: Bayesian Model-Averaged Bias Assessment (RoBMA)

**Purpose**: Combine multiple bias models via Bayesian model averaging for a
single, comprehensive publication bias assessment

```r
# install.packages("RoBMA")
library(RoBMA)

# RoBMA averages across models with and without publication bias,
# selection models, and PET-PEESE, weighting by posterior probability
fit <- RoBMA(d = es$yi,
             se = sqrt(es$vi),
             study_names = data$study_id)

summary(fit)

# Key outputs:
# - Inclusion Bayes factor for publication bias (BF_pb)
#   BF_pb > 3 suggests evidence for publication bias
#   BF_pb < 1/3 suggests evidence against publication bias
# - Model-averaged effect estimate (accounts for bias uncertainty)

# Diagnostic plots
plot(fit, parameter = "mu", prior = TRUE)
plot(fit, parameter = "PET")
```

**Note**: RoBMA requires JAGS to be installed on the system. Run times can be
several minutes depending on model complexity.

### Scenario 7: Copas Selection Model and Limit Meta-Analysis

**Purpose**: Additional sensitivity analyses using alternative selection model frameworks

```r
# install.packages("metasens")
library(metasens)
library(meta)

# Fit meta-analysis with meta package (required by metasens)
m <- metagen(TE = es$yi,
             seTE = sqrt(es$vi),
             studlab = data$study_id,
             sm = "RR")

# Copas selection model
# Models selection as a function of study precision and true effect
cop <- copas(m)
summary(cop)

png("figures/copas_plot.png", width = 7, height = 6, units = "in", res = 300)
plot(cop)
dev.off()

# Limit meta-analysis (Rucker et al.)
# Extrapolates funnel plot regression to the limit of infinite precision
lim <- limitmeta(m)
summary(lim)

png("figures/limitmeta_plot.png", width = 7, height = 6, units = "in", res = 300)
funnel(lim)
dev.off()
```

### Scenario 8: p-uniform\* Analysis

**Purpose**: Test and correct for publication bias using p-value distributions

p-uniform\* is a more robust successor to p-curve analysis. It uses the
conditional distribution of statistically significant p-values to test for
and correct publication bias.

```r
# install.packages("puniform")
library(puniform)

# p-uniform* analysis
# Requires observed effects, variances, and sample sizes
puni <- puniform(yi = es$yi,
                 vi = es$vi,
                 side = "right",       # Direction of expected effect
                 method = "LNP")       # Fisher's method (recommended)

print(puni)

# Key outputs:
# - Test for publication bias (p_pub)
# - Bias-corrected effect estimate
# - Test for an effect after bias correction (p_eff)
```

---

## Cochrane ROB-ME Framework

Statistical tests alone cannot fully assess publication bias. Cochrane's
**Risk of Bias due to Missing Evidence (ROB-ME)** tool provides a structured
framework for evaluating bias from missing results. It includes 8 signalling
questions covering:

1. Were results available for all planned comparisons?
2. Were results available for all planned outcomes?
3. Were results available for all planned analyses?
4. Were there concerns about selective non-reporting?
5. Were there concerns about selective publication?

**Recommendation**: Use ROB-ME alongside statistical tests and funnel plots
for a comprehensive bias assessment. Document ROB-ME judgments in
`08_reviews/grade_summary.md` as part of the GRADE "publication bias" domain.

Reference: Page MJ, Higgins JPT, et al. (2023). Assessing risk of bias due
to missing results in a synthesis. _Cochrane Handbook_, Chapter 13.

---

## Troubleshooting

### Problem: Funnel shading is asymmetric / skewed (ratio measures)

**Symptom**: Confidence region is wider on one side than the other, making it
hard to tell if points are distributed symmetrically

**Cause**: Plotting HR/RR/OR on the natural scale instead of the log scale.
The standard error of a ratio is inherently asymmetric on the natural scale.

**Solution**: Use `backtransf = FALSE` for `meta::funnel()`:

```r
# BAD: natural scale -- asymmetric shading
funnel(model)

# GOOD: log scale -- symmetric shading
funnel(model, backtransf = FALSE, xlab = "Log HR")
```

For `metafor::funnel()`, the log scale is already the default (no fix needed).

### Problem: Funnel plot looks asymmetric

**Not always publication bias!** Other causes:

- True heterogeneity (different effect in small vs large studies)
- Methodological differences in study quality
- Chance (with few studies)

**Solution**: Use contour-enhanced funnel plot to distinguish bias from heterogeneity.
Use selection models to quantify impact on the pooled estimate.

### Problem: Too few studies for Egger's test

**Rule of thumb**: Need at least 10 studies for reliable asymmetry tests.

**Solution**: Report the limitation and rely on visual inspection. Selection
models (`selmodel()`) can still be applied with fewer studies, though
interpret with caution. The PublicationBias S-value approach can also be
informative with smaller pools.

### Problem: Trim-and-fill imputes too many studies

**Solution**: Interpret cautiously. Report both original and adjusted estimates.
Prefer the 3PSM selection model (`selmodel()`) for bias-corrected estimates, as
it makes fewer structural assumptions than trim-and-fill.

### Problem: Binary outcome with rare events

**Solution**: Use Peters' test (`regtest(res, model = "lm", predictor = "ni")`)
instead of Egger's test. Egger's test has inflated type I error rates for
binary outcomes, especially with rare events.

### Problem: Selection model fails to converge

**Solution**: Try different optimization settings or a simpler model:

```r
# Try beta selection model instead of step function
selmodel(res, type = "beta")

# Try with different optimizer
selmodel(res, type = "stepfun", steps = 0.025,
         control = list(optimizer = "nlminb"))
```

---

## Export Formats

```r
# PNG (recommended)
png("funnel_plot.png", width = 7, height = 6, units = "in", res = 300)
funnel(model, backtransf = FALSE, xlab = "Log HR")  # log scale for ratio measures
dev.off()

# TIFF (some journals)
tiff("funnel_plot.tif", width = 7, height = 6, units = "in",
     res = 300, compression = "lzw")
funnel(model, backtransf = FALSE, xlab = "Log HR")
dev.off()
```

---

## Package Documentation

- **metafor**: https://www.metafor-project.org/
  - `funnel()`, `regtest()`, `trimfill()`, `ranktest()`, `fsn()`, `selmodel()`
- **metaviz**: https://cran.r-project.org/package=metaviz
  - `viz_sunset()` for power-enhanced funnel plots
- **PublicationBias**: https://cran.r-project.org/package=PublicationBias
  - `pubbias_svalue()` for S-values, `pubbias_meta()` for bias-corrected estimates
- **RoBMA**: https://cran.r-project.org/package=RoBMA
  - Bayesian model-averaged publication bias assessment
- **puniform**: https://cran.r-project.org/package=puniform
  - `puniform()` for p-uniform\* analysis (replaces p-curve)
- **metasens**: https://cran.r-project.org/package=metasens
  - `copas()` for Copas selection model, `limitmeta()` for limit meta-analysis
- **Cochrane ROB-ME**: Chapter 13, Cochrane Handbook for Systematic Reviews

---

## See Also

- [01-forest-plots.md](01-forest-plots.md) - Create forest plots
- [03-subgroup-plots.md](03-subgroup-plots.md) - Subgroup analysis plots
- [09-package-selection.md](09-package-selection.md) - Publication bias package selection
