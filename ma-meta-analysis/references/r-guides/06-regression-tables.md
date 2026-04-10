# Regression Tables for Meta-Analysis

**When to use**: You need to present meta-regression results in a formatted table
**Time**: 20-30 minutes
**Stage**: 07 (Manuscript)

**Packages**:

```r
library(metafor)        # Meta-regression models
library(broom)          # Tidy model extraction (tidy.rma, glance.rma)
library(modelsummary)   # Side-by-side model comparison tables (v2.0+)
library(tinytable)      # Zero-dependency table backend (used by modelsummary)
library(gtsummary)      # Formatted summary tables
library(gt)             # HTML/PDF export with decimal alignment
library(flextable)      # Word export
library(dplyr)          # Data manipulation
```

---

## Quick Start: Meta-Regression Table

```r
library(metafor)
library(broom)

# Load data and calculate effect sizes
data <- read.csv("05_extraction/extraction.csv")
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Fit meta-regression
res_mr <- rma(yi, vi, mods = ~ mean_age + pdl1_status, data = es, method = "REML")

# Tidy extraction (broom integration)
tidy(res_mr, conf.int = TRUE)                # Coefficient table
tidy(res_mr, conf.int = TRUE, exponentiate = TRUE)  # Exponentiated (RR/OR scale)
glance(res_mr)                                # Model-level stats: I2, QE, R2

# Summary
print(res_mr)
```

---

## Common Scenarios

### Scenario 1: Univariate Meta-Regression Table

```r
library(metafor)
library(dplyr)

# Run univariate regressions for each moderator
moderators <- c("mean_age", "female_pct", "follow_up_months", "pdl1_status")

results <- lapply(moderators, function(mod) {
  formula <- as.formula(paste("~ ", mod))
  res <- rma(yi, vi, mods = formula, data = es, method = "REML")
  data.frame(
    Moderator = mod,
    Estimate = round(res$beta[2], 3),
    SE = round(res$se[2], 3),
    CI_lower = round(res$ci.lb[2], 3),
    CI_upper = round(res$ci.ub[2], 3),
    z = round(res$zval[2], 2),
    p = round(res$pval[2], 4),
    R2 = round(res$R2, 1)
  )
})

# Combine into table
mr_table <- bind_rows(results)
print(mr_table)

# Export to CSV
write.csv(mr_table, "tables/meta_regression_univariate.csv", row.names = FALSE)
```

### Scenario 2: Multivariate Meta-Regression with broom + modelsummary

Use `broom::tidy.rma()` to extract tidy coefficients, then `modelsummary` for
publication-ready comparison tables.

```r
library(metafor)
library(broom)
library(modelsummary)

# Fit multiple models
res_uni <- rma(yi, vi, mods = ~ mean_age, data = es, method = "REML")
res_multi <- rma(yi, vi,
                 mods = ~ mean_age + female_pct + pdl1_status,
                 data = es, method = "REML")

# Side-by-side model comparison (modelsummary v2.0+ with tinytable backend)
modelsummary(
  list("Univariate" = res_uni, "Multivariate" = res_multi),
  estimate  = "{estimate} ({std.error})",
  statistic = "[{conf.low}, {conf.high}]",
  fmt = 3,
  gof_map = c("nobs", "r.squared"),
  output = "tables/meta_regression_comparison.docx"
)

# Alternative outputs: "gt", "flextable", "tinytable", "latex", "html"
modelsummary(
  list("Univariate" = res_uni, "Multivariate" = res_multi),
  output = "gt"
)
```

### Scenario 3: Manual Coefficient Extraction (No modelsummary)

```r
library(metafor)
library(broom)

# Multivariate model
res_multi <- rma(yi, vi,
                 mods = ~ mean_age + female_pct + pdl1_status,
                 data = es, method = "REML")

# Tidy extraction
coef_table <- tidy(res_multi, conf.int = TRUE)
model_stats <- glance(res_multi)

# Or manual extraction (equivalent)
coef_table <- data.frame(
  Variable = rownames(res_multi$beta),
  Estimate = round(res_multi$beta, 3),
  SE = round(res_multi$se, 3),
  CI_lower = round(res_multi$ci.lb, 3),
  CI_upper = round(res_multi$ci.ub, 3),
  z = round(res_multi$zval, 2),
  p = round(res_multi$pval, 4)
)
coef_table$Variable[1] <- "Intercept"

# Add model statistics
cat(sprintf("Model R² = %.1f%%\n", res_multi$R2))
cat(sprintf("Q_model = %.2f, df = %d, p = %.4f\n",
            res_multi$QM, res_multi$m, res_multi$QMp))
cat(sprintf("Residual I² = %.1f%%\n", res_multi$I2))

# Export
write.csv(coef_table, "tables/meta_regression_multivariate.csv", row.names = FALSE)
```

### Scenario 4: Subgroup Summary Table

```r
library(metafor)
library(dplyr)

# Subgroup analyses
subgroup_vars <- c("study_design", "ici_type", "line_of_therapy")

sg_results <- lapply(subgroup_vars, function(sg) {
  formula <- as.formula(paste("~", sg))
  res <- rma(yi, vi, mods = formula, data = es, method = "DL")

  # Get subgroup-specific estimates
  levels <- unique(es[[sg]])
  sub_estimates <- lapply(levels, function(lev) {
    sub_data <- es[es[[sg]] == lev, ]
    if (nrow(sub_data) >= 2) {
      sub_res <- rma(yi, vi, data = sub_data, method = "DL")
      data.frame(
        Moderator = sg,
        Subgroup = lev,
        k = nrow(sub_data),
        Estimate = round(exp(sub_res$beta[1]), 2),
        CI = sprintf("[%.2f, %.2f]", exp(sub_res$ci.lb), exp(sub_res$ci.ub)),
        I2 = round(sub_res$I2, 1),
        p_interaction = round(res$QMp, 4)
      )
    }
  })
  bind_rows(sub_estimates)
})

sg_table <- bind_rows(sg_results)
print(sg_table)

write.csv(sg_table, "tables/subgroup_summary.csv", row.names = FALSE)
```

### Scenario 5: tinytable for Minimal-Dependency Tables

When you need formatted tables with zero extra dependencies. The `tinytable`
package supports LaTeX, HTML, Word, and Typst output from a single call.

```r
library(metafor)
library(broom)
library(tinytable)

# Tidy coefficients from meta-regression
coef_df <- tidy(res_multi, conf.int = TRUE) |>
  mutate(
    across(where(is.numeric), \(x) round(x, 3)),
    term = ifelse(term == "intrcpt", "Intercept", term)
  )

# Create formatted table
tt(coef_df) |>
  style_tt(bold = TRUE, i = 0) |>          # Bold header row
  style_tt(italic = TRUE, i = 1) |>         # Italic intercept
  format_tt(digits = 3) |>
  save_tt("tables/meta_regression.docx")     # Also: .html, .tex, .png, .typst

# Add model footnote
model_note <- sprintf("I² = %.1f%%, R² = %.1f%%, Q(df=%d) = %.2f, p = %.4f",
                       res_multi$I2, res_multi$R2, res_multi$m,
                       res_multi$QM, res_multi$QMp)

tt(coef_df) |>
  style_tt(bold = TRUE, i = 0) |>
  format_tt(digits = 3) |>
  save_tt("tables/meta_regression.html")
```

### Scenario 6: Export to Word with flextable

```r
library(flextable)
library(officer)

# Create formatted table
ft <- flextable(mr_table) %>%
  set_header_labels(
    Moderator = "Moderator",
    Estimate = "Coefficient",
    SE = "SE",
    CI_lower = "95% CI Lower",
    CI_upper = "95% CI Upper",
    z = "z",
    p = "p-value",
    R2 = "R² (%)"
  ) %>%
  bold(part = "header") %>%
  autofit() %>%
  theme_vanilla()

# Save to Word
save_as_docx(ft, path = "07_manuscript/tables/meta_regression.docx")
```

### Scenario 7: gt Table with Decimal Alignment and Footnotes

```r
library(gt)
library(broom)

coef_df <- tidy(res_multi, conf.int = TRUE, exponentiate = TRUE) |>
  mutate(term = ifelse(term == "intrcpt", "Intercept", term))

model_stats <- glance(res_multi)

gt_table <- coef_df |>
  gt(rowname_col = "term") |>
  fmt_number(columns = c(estimate, conf.low, conf.high), decimals = 2) |>
  fmt_number(columns = std.error, decimals = 3) |>
  fmt_number(columns = statistic, decimals = 2) |>
  cols_align_decimal() |>
  cols_label(
    estimate  = "RR",
    std.error = "SE",
    statistic = "z",
    p.value   = "p-value",
    conf.low  = "95% CI Lower",
    conf.high = "95% CI Upper"
  ) |>
  tab_footnote(
    footnote = sprintf(
      "Random-effects meta-regression (REML). I² = %.1f%%, R² = %.1f%%, Q_M(df=%d) = %.2f, p = %s",
      model_stats$i.squared, model_stats$r.squared, res_multi$m,
      res_multi$QM, format_p(res_multi$QMp)
    )
  ) |>
  tab_header(title = "Meta-Regression Results")

# Export
gtsave(gt_table, "tables/meta_regression.html")
gtsave(gt_table, "tables/meta_regression.docx")
```

---

## Formatting Tips

### P-value formatting

```r
format_p <- function(p) {
  ifelse(p < 0.001, "< 0.001",
         ifelse(p < 0.01, sprintf("%.3f", p),
                sprintf("%.2f", p)))
}
```

### Journal-Specific CI Formatting

Different journals require different confidence interval styles. Use these
formatters to match your target journal.

```r
# Lancet: parentheses with "to" — e.g., "1.26 (1.16 to 1.37)"
format_ci_lancet <- function(est, lower, upper, digits = 2) {
  sprintf("%.*f (%.*f to %.*f)", digits, est, digits, lower, digits, upper)
}

# JAMA: "estimate (95% CI, lower-upper)" — e.g., "1.26 (95% CI, 1.16-1.37)"
format_ci_jama <- function(est, lower, upper, digits = 2) {
  sprintf("%.*f (95%% CI, %.*f-%.*f)", digits, est, digits, lower, digits, upper)
}

# NEJM: "estimate (95% CI, lower to upper)" — e.g., "1.26 (95% CI, 1.16 to 1.37)"
format_ci_nejm <- function(est, lower, upper, digits = 2) {
  sprintf("%.*f (95%% CI, %.*f to %.*f)", digits, est, digits, lower, digits, upper)
}

# Generic bracket format — e.g., "[1.16, 1.37]"
format_ci <- function(lower, upper, digits = 2) {
  sprintf("[%.*f, %.*f]", digits, lower, digits, upper)
}
```

**Usage example**:

```r
# Apply journal-specific formatting to a tidy coefficient table
coef_df <- tidy(res_mr, conf.int = TRUE, exponentiate = TRUE)

# For Lancet submission
coef_df$CI_formatted <- format_ci_lancet(coef_df$estimate, coef_df$conf.low, coef_df$conf.high)

# For JAMA submission
coef_df$CI_formatted <- format_ci_jama(coef_df$estimate, coef_df$conf.low, coef_df$conf.high)
```

### Quarto Cross-Referencing

When embedding tables in Quarto manuscripts, use labels for automated numbering
and in-text cross-references.

````
```{r}
#| label: tbl-metareg
#| tbl-cap: "Meta-Regression of Treatment Effect by Study-Level Covariates"

# Any of the table outputs above (gt, flextable, tinytable, modelsummary)
modelsummary(
  list("Univariate" = res_uni, "Multivariate" = res_multi),
  output = "gt"
)
```
````

Reference in text with `@tbl-metareg`:

```
As shown in @tbl-metareg, PD-L1 status was significantly associated with
treatment effect (p < 0.001).
```

---

## Troubleshooting

### Problem: "Number of parameters to be estimated is larger than k"

**Cause**: Too many moderators for the number of studies.

**Solution**: Use univariate regressions or reduce moderators. Rule of thumb: at least 10 studies per moderator.

### Problem: R² is negative or NA

**Explanation**: Residual heterogeneity exceeds total heterogeneity (rare, usually means moderator doesn't help).

**Solution**: Report R² = 0% and note the moderator does not explain heterogeneity.

### Problem: broom::tidy() does not recognize rma objects

**Cause**: The metafor-specific tidiers require broom to be loaded after metafor, or you may need the `broom.mixed` package for older broom versions.

**Solution**:

```r
# Ensure both packages are loaded
library(metafor)
library(broom)

# Verify the method exists
methods(tidy)  # Should list tidy.rma.uni

# If not found, try broom.mixed
# install.packages("broom.mixed")
library(broom.mixed)
```

### Problem: modelsummary does not display rma models

**Cause**: modelsummary relies on broom tidiers. Ensure broom is loaded and can tidy rma objects.

**Solution**:

```r
library(broom)
library(modelsummary)

# Test that tidy works first
tidy(res_mr, conf.int = TRUE)

# Then pass to modelsummary
modelsummary(list("Model" = res_mr))
```

---

## Package Documentation

- **metafor**: https://www.metafor-project.org/
- **broom**: https://broom.tidymodels.org/
- **modelsummary**: https://modelsummary.com/
- **tinytable**: https://vincentarelbundock.github.io/tinytable/
- **gt**: https://gt.rstudio.com/
- **gtsummary**: https://www.danieldsjoberg.com/gtsummary/
- **flextable**: https://ardata-fr.github.io/flextable-book/

---

## See Also

- [05-table1-gtsummary.md](05-table1-gtsummary.md) - Study characteristics tables
- [03-subgroup-plots.md](03-subgroup-plots.md) - Visualize subgroup results
- [07-themes-colors.md](07-themes-colors.md) - Consistent themes for tables and figures
- [08-ggplot2-patterns.md](08-ggplot2-patterns.md) - ggplot2 patterns for plots
