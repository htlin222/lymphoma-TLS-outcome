# Subgroup Analysis Plots

**When to use**: You need to visualize subgroup analyses or meta-regression results
**Time**: 20-30 minutes
**Stage**: 06 (Analysis)

**Packages**:

```r
library(meta)        # Subgroup forest plots (recommended for subgroup workflow)
library(metafor)     # Meta-regression + bubble plots
library(forestplot)  # Custom subgroup forest plots (medical journal standard)
library(forestploter) # ggplot2-based forest plots (alternative)
library(dmetar)      # Mixed-effects subgroup testing
library(orchaRd)     # Orchard/caterpillar plots (modern alternative)
library(dplyr)       # Data manipulation
library(grid)        # Graphics support
```

---

## Sizing Helper (Copy from 01-forest-plots.md)

```r
# Dynamic PNG height for meta::forest() -- avoids white padding / text overlap
forest_height <- function(model, subgroups = FALSE, spacing = 1.0) {
  k <- model$k
  header  <- 1.0
  row_h   <- 0.35 * spacing
  footer  <- 1.5
  n_rows  <- k + 1
  if (subgroups && !is.null(model$bylevs)) {
    n_sg   <- length(model$bylevs)
    n_rows <- n_rows + n_sg * 2
    footer <- footer + 0.4
  }
  height_in <- max(4, min(20, header + n_rows * row_h + footer))
  return(height_in)
}
```

---

## Quick Start: Subgroup Forest Plot

```r
library(meta)

# Load data
data <- read.csv("05_extraction/extraction.csv")

# Fit meta-analysis with subgroups using meta package (simplest approach)
res <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = data,
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK",
  subgroup = subgroup_var,
  print.subgroup.name = TRUE
)

# Forest plot with subgroups (300 DPI)
# Dynamic height -- see 01-forest-plots.md "Sizing & Margins" section
h <- forest_height(res, subgroups = TRUE)
png("figures/forest_subgroup.png", width = 10, height = h, units = "in", res = 300)
par(mar = c(5, 0, 1, 0))  # extra bottom for subgroup test line
forest(res, sortvar = subgroup_var, layout = "JAMA")
dev.off()
```

---

## Best Practices

### Always Report Q_between (Interaction Test)

A common methodological error is reporting only within-subgroup p-values without the
formal test for subgroup differences (Q_between / interaction test). The interaction
test answers: "Are the subgroup effects truly different from each other?"

```r
# After fitting a subgroup model with meta package:
cat(sprintf(
  "Test for subgroup differences: Q = %.2f, df = %d, p = %.4f\n",
  res$Q.b.random, res$df.Q.b, res$pval.Q.b.random
))
```

**Key rule**: A significant effect in one subgroup and a non-significant effect in
another does NOT mean the subgroups differ. You must report the interaction test.

### Use REML Estimation (Current Best Practice)

REML (Restricted Maximum Likelihood) is the current recommended estimator for
random-effects meta-analysis, replacing DerSimonian-Laird (DL) as the default.

```r
# Current best practice
method.tau = "REML"

# Combine with Hartung-Knapp confidence intervals
method.random.ci = "HK"
```

---

## Common Scenarios

### Scenario 1: Quick Subgroup with meta Package

**Fastest approach** for simple subgroup analyses. Uses `update()` to add subgroups
to an already fitted model:

```r
library(meta)

# Step 1: Fit the overall model
res <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = data,
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK"
)

# Step 2: Add subgroup variable using update()
res_sub <- update(res, subgroup = subgroup_var)

# Step 3: Forest plot with subgroups
h <- forest_height(res_sub, subgroups = TRUE)
png("figures/forest_subgroup_quick.png", width = 10, height = h, units = "in", res = 300)
par(mar = c(5, 0, 1, 0))
forest(res_sub, sortvar = subgroup_var)
dev.off()

# Step 4: Always report the interaction test
cat(sprintf(
  "Test for subgroup differences (Q_between): Q = %.2f, df = %d, p = %.4f\n",
  res_sub$Q.b.random, res_sub$df.Q.b, res_sub$pval.Q.b.random
))
```

### Scenario 2: Journal-Style Layouts with meta::forest()

**Purpose**: Match specific journal formatting requirements.

```r
library(meta)

res_sub <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = data,
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK",
  subgroup = subgroup_var
)

# BMJ-style layout
h <- forest_height(res_sub, subgroups = TRUE)
png("figures/forest_subgroup_bmj.png", width = 10, height = h, units = "in", res = 300)
par(mar = c(5, 0, 1, 0))
forest(res_sub, layout = "BMJ", sortvar = subgroup_var)
dev.off()

# JAMA-style layout
h <- forest_height(res_sub, subgroups = TRUE)
png("figures/forest_subgroup_jama.png", width = 10, height = h, units = "in", res = 300)
par(mar = c(5, 0, 1, 0))
forest(res_sub, layout = "JAMA", sortvar = subgroup_var)
dev.off()
```

**Available layouts**: `"BMJ"`, `"JAMA"`, `"Lancet"`, `"RevMan5"`, `"meta"` (default)

### Scenario 3: Mixed-Effects Subgroup Testing with dmetar

**Purpose**: Proper mixed-effects subgroup analysis. Avoids the common mistake of
fitting separate fixed-effect models per subgroup, which underestimates heterogeneity.

```r
library(meta)
library(dmetar)

# Fit model with subgroups
res <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = data,
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK",
  subgroup = subgroup_var
)

# Mixed-effects subgroup analysis (recommended approach)
# Uses a single pooled tau-squared across subgroups
sub_mixed <- subgroup.analysis.mixed.effects(res, subgroup = data$subgroup_var)
print(sub_mixed)

# Reports:
# - Within-subgroup estimates (using common tau-squared)
# - Q_between test for subgroup differences
# - Between-subgroup heterogeneity
```

### Scenario 4: Combining Separate Subgroup Analyses with metabind()

**Purpose**: When subgroups come from entirely separate datasets or require different
models, use `metabind()` to combine them for a single plot.

```r
library(meta)

# Fit separate models per subgroup
res_rct <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = subset(data, design == "RCT"),
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK"
)

res_obs <- metabin(
  event.e = events_intervention,
  n.e = n_intervention,
  event.c = events_control,
  n.c = n_control,
  studlab = study_id,
  data = subset(data, design == "Observational"),
  sm = "RR",
  method.tau = "REML",
  method.random.ci = "HK"
)

# Combine with metabind()
res_combined <- metabind(res_rct, res_obs,
                         name = c("RCTs", "Observational"),
                         pooled = "random")

# Forest plot of combined subgroups
png("figures/forest_subgroup_combined.png", width = 4200, height = 3600, res = 300)
forest(res_combined)
dev.off()
```

### Scenario 5: Meta-Regression with Continuous Moderator

**Purpose**: Visualize the relationship between a continuous moderator and effect size.

```r
library(metafor)

# Calculate effect sizes
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Meta-regression
res_mr <- rma(yi, vi, mods = ~ mean_age, data = es, method = "REML")
print(res_mr)

# Bubble plot using regplot() (preferred approach)
png("figures/meta_regression_bubble.png", width = 8, height = 6, units = "in", res = 300)
regplot(res_mr,
        xlab = "Mean Age (years)",
        ylab = "Log Risk Ratio",
        main = "Meta-Regression: Effect by Mean Age",
        atransf = exp,    # Back-transform to RR scale on axis
        pi = TRUE,        # Add prediction interval
        ci = TRUE)        # Add confidence interval
dev.off()
```

**Note**: `regplot()` from metafor is preferred over manual ggplot bubble plots for
meta-regression because it automatically sizes points by precision, adds the
regression line, and handles confidence/prediction intervals correctly.

For a manual bubble plot with more visual control:

```r
library(metafor)
library(ggplot2)

# Manual bubble plot
png("figures/meta_regression_manual.png", width = 8, height = 6, units = "in", res = 300)

wi <- 1 / sqrt(es$vi)
size <- 0.5 + 3.0 * (wi - min(wi)) / (max(wi) - min(wi))

plot(es$mean_age, es$yi,
     pch = 19, cex = size, col = "gray40",
     xlab = "Mean Age (years)",
     ylab = "Effect Size (log RR)",
     main = "Meta-Regression: Effect by Mean Age")

abline(res_mr, lwd = 2)
abline(h = 0, lty = 2, col = "gray70")

# Add prediction interval
xs <- seq(min(es$mean_age), max(es$mean_age), length.out = 100)
preds <- predict(res_mr, newmods = xs)
lines(xs, preds$ci.lb, lty = 2)
lines(xs, preds$ci.ub, lty = 2)

dev.off()
```

### Scenario 6: Test for Subgroup Differences (metafor)

**Purpose**: Formal test for moderation using meta-regression framework.

```r
library(metafor)

# Calculate effect sizes
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Test for subgroup differences using meta-regression
res_mod <- rma(yi, vi, mods = ~ subgroup_var, data = es, method = "REML")

# Q-test for moderation (this IS the interaction test / Q_between)
cat(sprintf("Test for subgroup differences: Q = %.2f, df = %d, p = %.4f\n",
            res_mod$QM, res_mod$m, res_mod$QMp))

# Per-subgroup estimates
for (sg in unique(es$subgroup_var)) {
  sub <- rma(yi, vi, data = es, subset = (subgroup_var == sg), method = "REML")
  cat(sprintf("  %s: estimate = %.3f [%.3f, %.3f], I2 = %.1f%%\n",
              sg, sub$beta[1], sub$ci.lb, sub$ci.ub, sub$I2))
}
```

### Scenario 7: Orchard Plot with orchaRd (Modern Alternative)

**Purpose**: Orchard (caterpillar) plots combine effect sizes, heterogeneity, and
precision in a single visual. A modern alternative to traditional subgroup forest plots,
especially useful when you have many subgroups or moderators.

```r
library(metafor)
library(orchaRd)

# Calculate effect sizes
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Fit meta-regression with categorical moderator
res_mod <- rma.mv(yi, vi,
                   mods = ~ subgroup_var - 1,
                   random = ~ 1 | study_id,
                   data = es,
                   method = "REML")

# Orchard plot
png("figures/orchard_subgroup.png", width = 10, height = 8, units = "in", res = 300)
orchard_plot(res_mod,
             mod = "subgroup_var",
             group = "study_id",
             xlab = "Log Risk Ratio",
             transfm = "none")
dev.off()
```

**What the orchard plot shows**:

- **Points**: Individual study effect sizes (sized by precision)
- **Thick bar**: 95% confidence interval of the mean
- **Thin bar**: 95% prediction interval (where future studies might fall)
- **Color/position**: Grouped by moderator level

### Scenario 8: Custom Subgroup Forest Plot with forestplot Package

**Purpose**: Full manual control over subgroup layout for complex presentations.

```r
library(forestplot)
library(metafor)
library(dplyr)
library(grid)

# Load data
data <- read.csv("05_extraction/extraction.csv")

# Calculate effect sizes
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Fit subgroup models
subgroups <- split(es, es$subgroup_var)
sub_results <- lapply(subgroups, function(d) {
  if (nrow(d) >= 2) rma(yi, vi, data = d, method = "REML")
  else list(beta = d$yi, ci.lb = d$yi - 1.96*sqrt(d$vi),
            ci.ub = d$yi + 1.96*sqrt(d$vi), I2 = NA)
})

# Overall model
res_overall <- rma(yi, vi, data = es, method = "REML")

# Build table text with subgroup headers
tabletext_col1 <- "Study"
tabletext_col2 <- "RR [95% CI]"
mean_vals <- c(NA)
lower_vals <- c(NA)
upper_vals <- c(NA)
is_summary <- c(FALSE)

for (sg_name in names(subgroups)) {
  sg_data <- subgroups[[sg_name]]
  sg_res <- sub_results[[sg_name]]

  # Subgroup header
  tabletext_col1 <- c(tabletext_col1, sg_name)
  tabletext_col2 <- c(tabletext_col2, "")
  mean_vals <- c(mean_vals, NA)
  lower_vals <- c(lower_vals, NA)
  upper_vals <- c(upper_vals, NA)
  is_summary <- c(is_summary, TRUE)

  # Studies in subgroup
  for (i in seq_len(nrow(sg_data))) {
    rr <- exp(sg_data$yi[i])
    lo <- exp(sg_data$yi[i] - 1.96 * sqrt(sg_data$vi[i]))
    hi <- exp(sg_data$yi[i] + 1.96 * sqrt(sg_data$vi[i]))
    tabletext_col1 <- c(tabletext_col1, paste0("  ", sg_data$study_id[i]))
    tabletext_col2 <- c(tabletext_col2, sprintf("%.2f [%.2f, %.2f]", rr, lo, hi))
    mean_vals <- c(mean_vals, rr)
    lower_vals <- c(lower_vals, lo)
    upper_vals <- c(upper_vals, hi)
    is_summary <- c(is_summary, FALSE)
  }

  # Subgroup subtotal
  tabletext_col1 <- c(tabletext_col1, paste0("  Subtotal (", sg_name, ")"))
  tabletext_col2 <- c(tabletext_col2,
    sprintf("%.2f [%.2f, %.2f]", exp(sg_res$beta[1]), exp(sg_res$ci.lb), exp(sg_res$ci.ub)))
  mean_vals <- c(mean_vals, exp(sg_res$beta[1]))
  lower_vals <- c(lower_vals, exp(sg_res$ci.lb))
  upper_vals <- c(upper_vals, exp(sg_res$ci.ub))
  is_summary <- c(is_summary, TRUE)
}

# Overall
tabletext_col1 <- c(tabletext_col1, "Overall Effect")
tabletext_col2 <- c(tabletext_col2,
  sprintf("%.2f [%.2f, %.2f]", exp(res_overall$beta[1]), exp(res_overall$ci.lb), exp(res_overall$ci.ub)))
mean_vals <- c(mean_vals, exp(res_overall$beta[1]))
lower_vals <- c(lower_vals, exp(res_overall$ci.lb))
upper_vals <- c(upper_vals, exp(res_overall$ci.ub))
is_summary <- c(is_summary, TRUE)

# Create forest plot
n_rows <- length(mean_vals)
h <- max(4, 1.0 + n_rows * 0.35 + 1.5)
png("figures/forest_subgroup_custom.png", width = 10, height = h, units = "in", res = 300)

forestplot(
  labeltext = list(tabletext_col1, tabletext_col2),
  mean = mean_vals,
  lower = lower_vals,
  upper = upper_vals,

  title = "Subgroup Analysis: Effect by Subgroup Variable",
  xlab = "     <--- Favors Control ---     --- Favors Intervention --->",

  col = fpColors(box = "black", lines = "black", zero = "gray50", summary = "black"),

  zero = 1,
  xlog = TRUE,
  is.summary = is_summary,
  ci.vertices = TRUE,
  ci.vertices.height = 0.2,
  lwd.ci = 2.5,
  boxsize = 0.3
)

dev.off()
```

### Scenario 9: forestploter Package (ggplot2 Backend)

**Purpose**: Alternative to forestplot package with ggplot2 backend for more
customization options and integration with the tidyverse ecosystem.

```r
library(forestploter)
library(metafor)
library(dplyr)
library(grid)

# Load and prepare data
data <- read.csv("05_extraction/extraction.csv")
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)

# Prepare data frame for forestploter (requires specific column structure)
plot_data <- es %>%
  mutate(
    Study = study_id,
    Subgroup = subgroup_var,
    RR = exp(yi),
    Lower = exp(yi - 1.96 * sqrt(vi)),
    Upper = exp(yi + 1.96 * sqrt(vi)),
    ` ` = paste(rep(" ", 20), collapse = ""),   # Space for forest plot
    `RR [95% CI]` = sprintf("%.2f [%.2f, %.2f]", RR, Lower, Upper)
  ) %>%
  arrange(Subgroup, Study) %>%
  select(Subgroup, Study, `RR [95% CI]`, ` `, RR, Lower, Upper)

# Create forest plot
p <- forest(
  plot_data,
  est = plot_data$RR,
  lower = plot_data$Lower,
  upper = plot_data$Upper,
  ci_column = 4,            # Column index for the forest plot area
  ref_line = 1,             # Reference line at RR = 1
  x_trans = "log",          # Log scale
  xlim = c(0.1, 10),
  ticks_at = c(0.1, 0.5, 1, 2, 10)
)

ggsave("figures/forest_subgroup_forestploter.png", p,
       width = 12, height = 8, dpi = 300)
```

---

## Troubleshooting

### Problem: White padding / text overflow in subgroup forest plot

**Symptom**: Huge blank space or "Test for subgroup differences" text overlaps axis labels

**Cause**: Fixed pixel height in `png()` doesn't account for subgroup rows

**Solution**: Use dynamic height with extra margin:

```r
h <- forest_height(model, subgroups = TRUE, spacing = 1.5)
png("plot.png", width = 10, height = h, units = "in", res = 300)
par(mar = c(5, 0, 1, 0))  # bottom=5 for subgroup test line
forest(model, spacing = 1.5)
dev.off()
```

See [01-forest-plots.md "Sizing & Margins"](01-forest-plots.md#sizing--margins-avoiding-white-padding) for the `forest_height()` function.

### Problem: Too few studies per subgroup

**Rule of thumb**: Need at least 2 studies per subgroup for pooling.

**Solution**: Combine small subgroups or report individual study effects.

### Problem: Subgroup test is significant but individual effects overlap

**Explanation**: The Q-test tests equality of subgroup effects, not whether each is significant.

**Solution**: Report both subgroup-specific estimates and the interaction p-value (Q_between).

### Problem: Using separate fixed-effect models per subgroup

**Explanation**: A common mistake is fitting independent models per subgroup, each with
its own tau-squared. This can lead to incorrect subgroup comparisons because the
heterogeneity variance differs across subgroups.

**Solution**: Use `dmetar::subgroup.analysis.mixed.effects()` for proper mixed-effects
subgroup testing with a common tau-squared, or use `rma()` with `mods = ~` for the
meta-regression approach.

### Problem: Confusing within-subgroup significance with between-subgroup differences

**Explanation**: Finding p < 0.05 in one subgroup and p > 0.05 in another does NOT
mean the subgroups are significantly different.

**Solution**: Always report the Q_between (interaction) test. This is the formal
test for whether the moderator explains heterogeneity.

---

## Package Documentation

- **meta**: https://cran.r-project.org/web/packages/meta/
  - `subgroup` parameter in metabin/metacont, `update()`, `metabind()`
  - `forest()` with `layout` parameter for journal-specific styles
- **metafor**: https://www.metafor-project.org/
  - `rma(mods = ~)` for meta-regression
  - `regplot()` for bubble plots
- **dmetar**: https://dmetar.protectlab.org/
  - `subgroup.analysis.mixed.effects()` for proper mixed-effects subgroup testing
- **orchaRd**: https://daniel1noble.github.io/orchaRd/
  - `orchard_plot()` for orchard/caterpillar plots
- **forestplot**: https://cran.r-project.org/package=forestplot
  - Manual subgroup forest plot construction
- **forestploter**: https://cran.r-project.org/package=forestploter
  - ggplot2-based forest plots with data frame input

**Installation**:

```r
install.packages(c("meta", "metafor", "forestplot", "forestploter"))
install.packages("dmetar")
install.packages("orchaRd")
# If orchaRd is not on CRAN:
# remotes::install_github("daniel1noble/orchaRd")
```

---

## See Also

- [01-forest-plots.md](01-forest-plots.md) - Basic forest plots
- [02-funnel-plots.md](02-funnel-plots.md) - Publication bias
- [04-multi-panel.md](04-multi-panel.md) - Combine subgroup plots
- [09-package-selection.md](09-package-selection.md) - Package comparison
