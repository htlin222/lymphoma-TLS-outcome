# R Script Architecture & Style Guide

**When to use**: Setting up `06_analysis/` R scripts for a meta-analysis project
**Time**: Read in 10 min, saves hours of iteration
**Packages**: `meta`, `metafor`, `dplyr`, `readr`

---

## Modular Script Architecture

### One Figure = One Script

Never put multiple figures in one script. Each script should produce exactly one output figure.

```
06_analysis/
  01_setup.R                    # Package install (run once)
  02_load_data.R                # Shared data loading (sourced by all)
  03a_forest_efs.R              # Figure 1: EFS forest
  03b_forest_os.R               # Figure 2: OS forest
  03c_forest_pcr.R              # Figure 3: pCR forest
  03d_forest_trae.R             # Figure 4: TRAE forest
  04a_subgroup_timing.R         # Figure 5: Timing subgroup
  04b_subgroup_region.R         # Figure 6: Region subgroup
  05a_sensitivity_loo.R         # Figure 7: Leave-one-out
  05b_sensitivity_no_impower.R  # Figure 7b: Exclude trial
  05c_sensitivity_low_rob.R     # Figure 7c: Low RoB only
  06_publication_bias.R         # Figures 8-9: Funnel plots
  figures/                      # All PNG output
  tables/                       # All CSV output
```

**Why**: Monolithic scripts (one file producing 4+ figures) cause:

- Hard to debug when one figure fails
- Re-running regenerates all figures unnecessarily
- Difficult to iterate on a single figure's style

### Shared Data Loading Script

Create `02_load_data.R` that all figure scripts `source()`:

```r
# 02_load_data.R
library(tidyverse)
library(meta)
library(metafor)

data <- read_csv("../05_extraction/round-01/extraction.csv", show_col_types = FALSE)

# Pre-compute derived columns ONCE
data$efs_se <- (log(data$efs_hr_95ci_upper) - log(data$efs_hr_95ci_lower)) / (2 * 1.96)
data$efs_log_hr <- log(data$efs_hr)
data$n.e <- data$n_intervention
data$n.c <- data$n_control

# Factor levels
data$timing_strategy <- factor(data$timing_strategy,
                                levels = c("neoadjuvant", "perioperative", "adjuvant"))
```

Each figure script starts with:

```r
source("02_load_data.R")
```

---

## Forest Plot Style (meta::forest)

### Use `meta::forest()`, NOT forestploter

`meta::forest()` is reliable and handles layout automatically. `forestploter` gives more control but has critical issues:

- Subgroup plots can render as blank white images
- Footnote text collides with x-axis tick labels
- Requires manual column layout that breaks easily

### What to HIDE

```r
meta::forest(model,
  # HIDE heterogeneity text - it ALWAYS ruins layout
  print.tau2 = FALSE,
  print.I2 = FALSE,
  print.pval.Q = FALSE,
  # ...
)
```

**Heterogeneity text** (I-squared, tau-squared, Q-test): Always suppress from the plot. These stats are available in the console output and belong in manuscript text/tables, not cluttering the figure.

**Prediction intervals**: Set `prediction = FALSE` in `metagen()`. The prediction bar looks ugly and adds visual noise. Report the interval in text instead.

### What to SHOW

```r
meta::forest(model,
  sortvar = TE,                    # Sort by effect size
  col.diamond = "maroon",          # Pooled estimate color
  col.square = "navy",             # Individual study color
  xlab = "Hazard Ratio (95% CI)",  # Single-line xlab
  xlim = c(0.2, 1.2),             # Consistent axis limits
  fontsize = 10                    # Readable text
)
```

### Subgroup Forest Plots

Additional suppressions needed:

```r
meta::forest(subgroup_model,
  # Standard suppressions
  print.tau2 = FALSE, print.I2 = FALSE, print.pval.Q = FALSE,
  # Subgroup-specific suppressions
  hetstat = FALSE,            # Per-subgroup heterogeneity
  overall.hetstat = FALSE,    # Overall heterogeneity
  test.subgroup = FALSE,      # Between-subgroup test
  # Layout
  spacing = 1.5,              # Extra row spacing for readability
  at = c(0.5, 0.75, 1.0),    # Custom tick marks
  xlim = c(0.25, 1.15)
)
```

### Dynamic Height Calculation

Prevents excessive white space (padding). Calculate PNG height from the number of studies:

```r
# Basic forest plot
h <- max(3.5, 1 + (model$k + 2) * 0.35)

# Subgroup forest plot
n_subgroups <- length(unique(data$subgroup_var))
h <- max(4.5, 1 + (model$k + n_subgroups * 2 + 2) * 0.35)

# Small study count (e.g., pCR with 3 studies)
h <- max(3, 1 + (model$k + 2) * 0.35)
```

```r
png("figures/figure1.png", width = 10, height = h, units = "in", res = 300)
```

---

## Funnel Plot Style

### Use log-scale x-axis (backtransf = TRUE)

```r
funnel(model,
       backtransf = TRUE,       # Show HR values on log-scale axis (0.5, 0.7, 1.0)
       xlab = "Hazard Ratio",   # NOT "Log Hazard Ratio"
       ylab = "Standard Error",
       # ...
)
```

`backtransf = FALSE` shows raw log(HR) values (-0.8, -0.4, 0) which are mathematically correct but clinically unintuitive.

### Contour-Enhanced Funnel Plot

Use light gray contours so dots and labels stand out:

```r
funnel(model,
       contour = c(0.9, 0.95, 0.99),
       col.contour = c("gray95", "gray90", "gray82"),  # Light grays
       studlab = FALSE,          # Disable built-in labels (we add our own)
       col = "navy", pch = 16,
       cex = 1.3)               # Larger dots
```

### Label Placement (Pitfall: Overflow)

**NEVER use built-in `studlab = TRUE`** for funnel plots. Labels will overflow the plot edges for extreme-value studies.

Instead, manually place labels with `text()`:

```r
# Disable built-in labels
funnel(model, studlab = FALSE, ...)

# Add labels manually with tight offset
text(exp(model$TE), model$seTE, labels = model$studlab,
     pos = 4, offset = 0.3, cex = 0.85)
```

For **trim-and-fill** plots where imputed studies extend far right, use **smart positioning** to prevent right-edge overflow:

```r
tf_hr <- exp(tf_result$TE)
tf_mid <- median(tf_hr)
tf_pos <- ifelse(tf_hr > tf_mid, 2, 4)  # Left for right-side dots, right for left-side
text(tf_hr, tf_result$seTE, labels = tf_result$studlab,
     pos = tf_pos, offset = 0.3, cex = 0.85)
```

### Legend Styling

Place legend in a white box with border, using data coordinates:

```r
legend(0.4, 0.025,  # x, y in data coordinates
       c("p > 0.10", "0.05 < p < 0.10", "0.01 < p < 0.05", "p < 0.01"),
       fill = c("white", "gray95", "gray90", "gray82"),
       bty = "o", box.lwd = 0.5, box.col = "gray60",
       bg = "white",
       x.intersp = 0.8, y.intersp = 1.2,
       cex = 1.0)
```

Key settings:

- `bty = "o"` draws a border box (vs `"n"` for no border)
- `bg = "white"` prevents contour shading bleeding through
- `x.intersp` / `y.intersp` control internal padding

### Font Sizes for Funnel Plots

Set via `par()` before the funnel call:

```r
par(mar = c(6, 6, 4, 4), xpd = NA, cex.lab = 1.3, cex.axis = 1.1)
funnel(model, ..., cex = 1.3)           # Dot size
text(..., cex = 0.85)                    # Label size
title(..., cex.main = 1.4, cex.sub = 1.0)  # Title sizes
legend(..., cex = 1.0)                   # Legend text size
```

For wider plots (e.g., trim-and-fill at 12in width), scale up proportionally:

```r
par(cex.lab = 1.6, cex.axis = 1.3)
funnel(..., cex = 1.5)
text(..., cex = 1.1)
title(..., cex.main = 1.6, cex.sub = 1.2)
```

---

## Common Pitfalls

### 1. Text Collision in Forest Plots

**Problem**: Heterogeneity text (I-squared, tau, Q-test p-value) overlaps with x-axis tick labels.

**Solution**: Always suppress: `print.tau2 = FALSE, print.I2 = FALSE, print.pval.Q = FALSE`. Report in manuscript text.

### 2. Prediction Interval Bar

**Problem**: The prediction interval renders as a long colored bar below the diamond, visually distracting.

**Solution**: Set `prediction = FALSE` in `metagen()`. Report the interval in text.

### 3. Label Overflow in Funnel Plots

**Problem**: Study labels near plot edges (especially rightmost trim-and-fill imputed studies) get clipped.

**Solution**: Use manual `text()` with smart positioning based on x-coordinate. Place labels toward the center of the plot.

### 4. Blank Subgroup Plots

**Problem**: Some packages (e.g., forestploter) silently produce blank white PNG files for subgroup analyses.

**Solution**: Stick with `meta::forest()` for subgroup plots. It handles subgroup layout reliably.

### 5. Working Directory Issues

**Problem**: Scripts use relative paths like `"figures/..."` but run from wrong directory, saving files to unexpected locations.

**Solution**: Always verify output exists at expected path after running:

```r
# At end of each script
cat("Saved:", normalizePath("figures/figure1.png"), "\n")
```

### 6. Two Code Paths (Egger's Test)

**Problem**: When funnel plot code has if/else branches (e.g., Egger's test success/failure), style changes applied to one branch but not the other.

**Solution**: When a funnel plot is re-drawn inside an if-block, keep ALL style parameters (legend position, font sizes, contour colors) identical between both branches.

### 7. Hakn with Small Subgroups

**Problem**: Hartung-Knapp adjustment (`hakn = TRUE`) with k=2 studies in a subgroup produces unreliable confidence intervals.

**Solution**: Omit `hakn = TRUE` for subgroup analyses where any subgroup has fewer than 3 studies.

---

## Table Export with gtsummary (HTML + PNG + DOCX)

### Packages

```r
library(gtsummary)
library(gt)          # HTML + PNG export
library(flextable)   # DOCX export
library(webshot2)    # PNG rendering (install chromote if needed)
```

### Pattern: Build Once, Export Three Ways

```r
# Build the table once
tbl <- data %>%
  tbl_summary(
    by = timing_strategy,
    include = c(n_total, median_age, percent_male, stage_distribution),
    statistic = list(
      all_continuous() ~ "{median} ({p25}, {p75})",
      all_categorical() ~ "{n} ({p}%)"
    ),
    label = list(
      n_total ~ "Sample size",
      median_age ~ "Median age (years)",
      percent_male ~ "Male (%)",
      stage_distribution ~ "Stage"
    )
  ) %>%
  add_overall() %>%
  add_p() %>%
  bold_labels() %>%
  modify_caption("**Table 1. Baseline Characteristics by Timing Strategy**")

# Export 1: HTML (interactive, for review)
tbl %>%
  as_gt() %>%
  gt::gtsave("tables/table1.html")

# Export 2: PNG (for manuscript figures, 300 DPI)
tbl %>%
  as_gt() %>%
  gt::gtsave("tables/table1.png", vwidth = 800, vheight = 600)

# Export 3: DOCX (for journal submission)
tbl %>%
  as_flex_table() %>%
  flextable::save_as_docx(path = "tables/table1.docx")

cat("Saved: tables/table1.html, table1.png, table1.docx\n")
```

### Sensitivity/Subgroup Summary Tables

```r
# Example: Sensitivity analysis summary
sensitivity_tbl <- sensitivity_summary %>%
  gt() %>%
  fmt_number(columns = c(Pooled_HR, CI_lower, CI_upper), decimals = 2) %>%
  fmt_number(columns = I2, decimals = 1, scale_by = 100, pattern = "{x}%") %>%
  fmt_scientific(columns = P_value, decimals = 2) %>%
  cols_merge(columns = c(CI_lower, CI_upper), pattern = "{1} - {2}") %>%
  cols_label(
    CI_lower = "95% CI",
    Pooled_HR = "HR",
    N_trials = "k"
  ) %>%
  tab_header(title = "Sensitivity Analysis Summary")

# All three formats
sensitivity_tbl %>% gtsave("tables/sensitivity.html")
sensitivity_tbl %>% gtsave("tables/sensitivity.png", vwidth = 700)
sensitivity_tbl %>% as_raw_html() # for Quarto embedding
```

### Tips

- **PNG width**: Set `vwidth` based on column count. 600-800px for 4-6 columns, 1000+ for wide tables.
- **DOCX compatibility**: `as_flex_table()` converts gtsummary to flextable, which handles Word formatting.
- **Quarto embedding**: Use `as_raw_html()` to embed directly in `.qmd` files.
- **Visual verify**: Read the PNG output to check alignment and truncation, same as figures.

---

## Script Template

```r
# ============================================================================
# Figure N: [Description]
# Project: [Project Name]
# ============================================================================

source("02_load_data.R")

cat("\n=== Figure N: [Description] ===\n")

# Model
model <- metagen(TE = efs_log_hr,
                 seTE = efs_se,
                 studlab = trial_name,
                 data = data,
                 sm = "HR",
                 fixed = FALSE,
                 random = TRUE,
                 method.tau = "DL",
                 hakn = TRUE,
                 prediction = FALSE)

print(summary(model))

# Dynamic height
h <- max(3.5, 1 + (model$k + 2) * 0.35)
png("figures/figureN_name.png", width = 10, height = h, units = "in", res = 300)

meta::forest(model,
  sortvar = TE,
  print.tau2 = FALSE,
  print.I2 = FALSE,
  print.pval.Q = FALSE,
  col.diamond = "maroon",
  col.square = "navy",
  xlab = "Hazard Ratio (95% CI)",
  xlim = c(0.2, 1.2),
  fontsize = 10)

dev.off()
cat("Saved: figures/figureN_name.png\n")
```

---

## Visual Verification (MANDATORY)

**R console output tells you nothing about visual quality.** A script can run without errors and still produce figures with text collision, label overflow, blank panels, or ugly padding. The ONLY way to catch these is to look at the output.

After generating any figure, Claude Code MUST read the PNG file to visually verify:

```
Read tool → figures/figureN_name.png
```

### Verification Checklist

Check every generated figure for:

1. **Text collision**: Labels overlapping axis ticks, other labels, or plot elements
2. **Label overflow**: Study names clipped at plot edges (especially rightmost/leftmost)
3. **Blank output**: PNG file exists (non-zero bytes) but renders as white/empty
4. **Excessive padding**: Large white space above/below/around the plot area
5. **Legend readability**: Legend text visible and not obscured by contour shading
6. **Font size**: All text legible at the rendered PNG resolution
7. **File location**: Output saved to `06_analysis/figures/`, not somewhere else

### Why This Matters

Common issues that are invisible in R console output:

| Issue               | Console says | Visual shows                        |
| ------------------- | ------------ | ----------------------------------- |
| Het text collision  | "plot saved" | Text overlapping x-axis ticks       |
| Blank subgroup plot | "plot saved" | White rectangle, 170KB file         |
| Label clipped       | "plot saved" | "Filled: Neoto..." cut off at edge  |
| Prediction bar ugly | "plot saved" | Long red bar cluttering the diamond |
| Wrong directory     | "plot saved" | File not at expected path           |

**Rule**: Never report a figure as "done" without visually confirming it via Read tool.

---

## See Also

- [01-forest-plots.md](01-forest-plots.md) - Package-specific forest plot options
- [02-funnel-plots.md](02-funnel-plots.md) - Funnel plot variations
- [03-subgroup-plots.md](03-subgroup-plots.md) - Subgroup analysis details
- [07-themes-colors.md](07-themes-colors.md) - Color palettes and themes
