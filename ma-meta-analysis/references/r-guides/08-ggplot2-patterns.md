# ggplot2 Best Practices for Meta-Analysis

**When to use**: You need to create custom plots beyond forest/funnel plots
**Time**: 30-45 minutes (reference guide)
**Stage**: Any

**Packages**:

```r
library(ggplot2)     # Core plotting
library(dplyr)       # Data manipulation
library(tidyr)       # Data reshaping
library(scales)      # Axis formatting
library(robvis)      # Risk of bias visualization (ROB2, ROBINS-I, QUADAS-2)
library(PRISMA2020)  # PRISMA 2020-compliant flow diagrams
library(metaviz)     # Modern forest/funnel plot variants
library(dmetar)      # Combined diagnostic plots
library(ragg)        # High-quality PNG rendering
```

---

## Quick Start: Meta-Analysis Summary Plot

```r
library(ggplot2)
library(dplyr)

data <- read.csv("05_extraction/extraction.csv")

# Effect size dot plot with CI
p <- ggplot(data, aes(x = reorder(study_id, effect_size),
                       y = effect_size,
                       ymin = ci_lower,
                       ymax = ci_upper)) +
  geom_pointrange(size = 0.5) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray50") +
  coord_flip() +
  labs(x = NULL, y = "Effect Size [95% CI]",
       title = "Individual Study Effects") +
  theme_minimal(base_size = 14)

ggsave("figures/effect_dotplot.png", p, width = 8, height = 6, dpi = 300)
```

---

## Essential Patterns

### 1. Data Preparation

```r
library(dplyr)
library(tidyr)

# Always prepare data before plotting
plot_data <- data %>%
  filter(!is.na(effect_size)) %>%
  mutate(
    study_label = paste0(author, " (", year, ")"),
    weight = 1 / se^2,
    significant = ifelse(ci_lower > 0 | ci_upper < 0, "Yes", "No")
  ) %>%
  arrange(desc(effect_size))
```

### 2. Basic Plot Structure

```r
# The ggplot2 pattern: data + aesthetics + geom + labels + theme
ggplot(data, aes(x = var1, y = var2)) +  # Data + aesthetics
  geom_point() +                          # Geometry
  labs(title = "Title", x = "X", y = "Y") + # Labels
  theme_minimal(base_size = 14)           # Theme
```

### 3. Save at Publication Quality

**Recommended**: Use `ragg::agg_png()` for better antialiasing and cross-platform consistency.

```r
# Preferred: ragg for high-quality rendering
library(ragg)
agg_png("figures/plot.png", width = 2400, height = 1800, res = 300)
print(p)
dev.off()

# Alternative: ggsave with ragg backend (if ragg is installed, ggsave uses it automatically)
ggsave("figures/plot.png", p,
       width = 8,      # inches
       height = 6,     # inches
       dpi = 300,      # publication quality
       bg = "white")   # white background (not transparent)

# For base R plots (metafor, robvis): use ragg directly
ragg::agg_png("figures/forest.png", width = 3000, height = 2400, res = 300)
metafor::forest(res)
dev.off()
```

**Why ragg?** The `ragg` package provides superior text rendering, consistent output across macOS/Linux/Windows, and better antialiasing compared to base `png()`. Install with `install.packages("ragg")`.

---

## Common Meta-Analysis Plots

### PRISMA 2020 Flow Diagram

**Purpose**: Generate a PRISMA 2020-compliant flow diagram for the study selection process.

```r
library(PRISMA2020)

# Prepare PRISMA data (see ?PRISMA_data for all fields)
prisma_data <- PRISMA_data(
  found = 1500,                      # Records from databases
  found_other = 50,                  # Records from other sources
  no_dupes = 1200,                   # After deduplication
  screened = 1200,                   # Title/abstract screened
  screen_exclusions = 1150,          # Excluded at screening
  full_text = 50,                    # Full-text assessed
  full_text_exclusions = 25,         # Excluded at full-text
  quantitative = 25,                 # Included in meta-analysis
  reasons = c("Wrong population = 10", "Wrong intervention = 8",
              "Wrong outcome = 5", "Duplicate data = 2")
)

# Generate flow diagram
flow <- PRISMA_flowdiagram(prisma_data,
                           fontsize = 12,
                           interactive = FALSE)

# Save as PNG or SVG
PRISMA_save(flow, filename = "figures/prisma_flow.png",
            filetype = "png", overwrite = TRUE)
```

This produces a publication-ready PRISMA 2020 flow diagram with all required boxes and arrows, replacing any manual approach.

### Risk of Bias Visualization with robvis

**Purpose**: Create standardized Risk of Bias summary and traffic light plots using the `robvis` package. This is the current standard approach, replacing manual `geom_tile` heatmaps.

```r
library(robvis)

# Prepare RoB 2 data (for RCTs)
# Columns: Study, D1, D2, D3, D4, D5, Overall
rob_data <- data.frame(
  Study = c("Study A 2020", "Study B 2021", "Study C 2022"),
  D1 = c("Low", "Some concerns", "Low"),
  D2 = c("Low", "Low", "Low"),
  D3 = c("Some concerns", "Low", "Low"),
  D4 = c("Low", "High", "Low"),
  D5 = c("Low", "Some concerns", "Low"),
  Overall = c("Some concerns", "High", "Low"),
  stringsAsFactors = FALSE
)

# Summary bar chart (proportions per domain)
rob_summary(rob_data, tool = "ROB2")
ggsave("figures/rob_summary.png", width = 8, height = 5, dpi = 300)

# Traffic light plot (per-study, per-domain grid)
rob_traffic_light(rob_data, tool = "ROB2")
ggsave("figures/rob_traffic_light.png", width = 8, height = 5, dpi = 300)
```

Supported tools: `"ROB2"` (RCTs), `"ROBINS-I"` (non-randomized), `"QUADAS-2"` (diagnostic accuracy). Column names must follow the tool-specific convention (see `?rob_summary` for details).

```r
# ROBINS-I example (7 domains)
# Columns: Study, D1-D7, Overall
rob_traffic_light(robins_data, tool = "ROBINS-I")

# QUADAS-2 example (4 domains)
rob_summary(quadas_data, tool = "QUADAS-2")
```

### Heterogeneity Visualization (I-squared by Subgroup)

```r
subgroup_het <- data.frame(
  subgroup = c("Overall", "RCT", "Observational", "High quality", "Low quality"),
  I2 = c(65, 30, 80, 25, 75),
  k = c(15, 8, 7, 6, 9)
)

p <- ggplot(subgroup_het, aes(x = reorder(subgroup, I2), y = I2)) +
  geom_col(fill = "gray40", width = 0.6) +
  geom_text(aes(label = sprintf("%.0f%% (k=%d)", I2, k)),
            hjust = -0.1, size = 4) +
  coord_flip() +
  scale_y_continuous(limits = c(0, 100), breaks = seq(0, 100, 25)) +
  geom_hline(yintercept = c(25, 50, 75), linetype = "dashed", color = "gray70") +
  labs(x = NULL, y = expression(I^2~"(%)"),
       title = "Heterogeneity by Subgroup") +
  theme_minimal(base_size = 14)

ggsave("figures/heterogeneity.png", p, width = 8, height = 5, dpi = 300)
```

---

## Diagnostic Visualizations (metafor Built-Ins)

**Purpose**: `metafor` provides a suite of built-in diagnostic plots that require no additional packages. These should be your first choice for standard diagnostic visualizations.

### Baujat Plot (Heterogeneity Contribution vs. Influence)

```r
library(metafor)

# Baujat plot: x-axis = contribution to Q statistic, y-axis = influence on pooled estimate
ragg::agg_png("figures/baujat.png", width = 2400, height = 2400, res = 300)
baujat(res, main = "Baujat Plot")
dev.off()
```

Studies in the upper-right quadrant contribute most to heterogeneity and have the largest influence on the pooled result.

### Cumulative Meta-Analysis Forest

```r
# Cumulative forest: studies added one at a time (e.g., by year)
cum <- cumul(res, order = data$year)

ragg::agg_png("figures/cumulative_forest.png", width = 2400, height = 2400, res = 300)
forest(cum, main = "Cumulative Meta-Analysis (by Year)")
dev.off()
```

Shows how the pooled estimate evolves as each study is added chronologically.

### Radial (Galbraith) Plot

```r
# Radial plot: precision on x-axis, standardized effect on y-axis
ragg::agg_png("figures/radial.png", width = 2400, height = 2400, res = 300)
radial(res, main = "Radial Plot")
dev.off()
```

Studies should cluster around the regression line if there is no heterogeneity. Outliers indicate influential or heterogeneous studies.

### L'Abbe Plot (Binary Outcomes)

```r
# L'Abbe plot: event rates in treatment vs. control group
# Requires ai/n1i and ci/n2i in the data
ragg::agg_png("figures/labbe.png", width = 2400, height = 2400, res = 300)
labbe(res, main = "L'Abbe Plot")
dev.off()
```

Points above the diagonal indicate treatment benefit. Useful for binary outcome meta-analyses to identify studies with unusual event rates.

### GOSH Plot (Graphical Overview of Study Heterogeneity)

```r
# GOSH: fit model to all possible subsets of studies
# NOTE: computationally intensive for k > 15 studies
gosh_res <- gosh(res)

ragg::agg_png("figures/gosh.png", width = 3000, height = 2400, res = 300)
plot(gosh_res, main = "GOSH Plot")
dev.off()
```

Each point represents a subset of studies. Multimodal clusters suggest outlier studies driving heterogeneity. Use `gosh.diagnostics()` from `metafor` to identify cluster membership.

---

## Combined Influence Diagnostics with dmetar

**Purpose**: `dmetar::InfluenceAnalysis()` produces a single 4-panel diagnostic figure combining Baujat plot, leave-one-out forest, influence measures, and studentized residuals. This replaces the need for multiple manual diagnostic plots.

```r
library(meta)
library(dmetar)

# Fit model with meta package (dmetar works with meta objects)
m <- metagen(TE = data$effect_size,
             seTE = data$se,
             studlab = data$study_label,
             sm = "RR")

# Single call produces 4-panel diagnostic plot
ragg::agg_png("figures/influence_diagnostics.png",
              width = 3600, height = 2700, res = 300)
InfluenceAnalysis(m, random = TRUE)
dev.off()
```

The four panels show:

1. **Baujat plot** - heterogeneity contribution vs. influence
2. **Leave-one-out forest** - pooled estimate when each study is removed
3. **Influence measures** - DFFITS, Cook's distance, hat values, covariance ratio
4. **Studentized residuals** - identify statistical outliers (|z| > 2)

This is the recommended single-function approach for routine influence diagnostics.

---

## Modern Plot Variants with metaviz

**Purpose**: `metaviz` provides modern alternatives to standard forest and funnel plots with improved visual encodings.

### Rainforest Plot

```r
library(metaviz)
library(metafor)

# Rainforest: replaces diamond with a density distribution
ragg::agg_png("figures/rainforest.png", width = 3000, height = 2400, res = 300)
viz_forest(res, type = "rain",
           xlab = "Risk Ratio",
           study_labels = data$study_label)
dev.off()
```

The rainforest plot displays the posterior distribution for each study, making uncertainty more intuitive than a simple confidence interval bar.

### Thick Forest Plot

```r
# Thick forest: line width proportional to study weight
ragg::agg_png("figures/thick_forest.png", width = 3000, height = 2400, res = 300)
viz_forest(res, type = "thick",
           xlab = "Risk Ratio",
           study_labels = data$study_label)
dev.off()
```

Line thickness encodes study precision, removing the need for a separate weight column.

### Sunset (Power-Enhanced) Funnel Plot

```r
# Sunset funnel: shaded regions indicate statistical power
ragg::agg_png("figures/sunset_funnel.png", width = 2400, height = 2400, res = 300)
viz_sunset(res, xlab = "Effect Size")
dev.off()
```

The sunset plot augments the standard funnel with power contours, highlighting the region where studies have sufficient power to detect the pooled effect. Studies outside the shaded region may be underpowered.

---

## Best Practices

### Do

```r
# Use explicit aesthetics
aes(x = var, y = var, color = group)  # Named columns

# Set consistent base size
theme_minimal(base_size = 14)

# Always label axes clearly
labs(x = "Clear Label (units)", y = "Clear Label (units)")

# Use white background for publication
ggsave(..., bg = "white")

# Fix factor ordering
mutate(study = factor(study, levels = desired_order))

# Use ragg for saving base R plots
ragg::agg_png("file.png", width = 2400, height = 1800, res = 300)

# Use dedicated packages (robvis, PRISMA2020) instead of manual ggplot2 code
```

### Don't

```r
# Don't use default gray background for publications
# theme_gray() is the default - switch to theme_minimal()

# Don't use 3D effects
# No pie charts, no 3D bar charts

# Don't use rainbow colors
# Use ggsci or viridis instead

# Don't forget units on axis labels
# "Age" -> "Age (years)"

# Don't build manual RoB heatmaps - use robvis instead
# Don't draw PRISMA diagrams manually - use PRISMA2020 instead

# Don't use base png() - use ragg::agg_png() for consistent rendering
```

---

## Troubleshooting

### Problem: Text overlaps

```r
# Use ggrepel for auto-positioning
library(ggrepel)
geom_text_repel(aes(label = study_id))
```

### Problem: X-axis labels too long

```r
# Wrap long labels
scale_x_discrete(labels = function(x) stringr::str_wrap(x, width = 15))

# Or rotate
theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

### Problem: Legend cluttered

```r
# Move legend inside plot
theme(legend.position = c(0.8, 0.2))

# Or put below
theme(legend.position = "bottom")

# Or remove
theme(legend.position = "none")
```

### Problem: Base R plot from metafor looks jagged

```r
# Use ragg instead of base png()
ragg::agg_png("figures/plot.png", width = 3000, height = 2400, res = 300)
forest(res)
dev.off()
```

---

## Package Documentation

- **ggplot2**: https://ggplot2.tidyverse.org/
- **scales**: https://scales.r-lib.org/
- **ggrepel**: https://ggrepel.slowkow.com/
- **robvis**: https://mcguinlu.github.io/robvis/
- **PRISMA2020**: https://github.com/prisma-flowdiagram/PRISMA2020
- **metaviz**: https://github.com/Mkossmeier/metaviz
- **dmetar**: https://dmetar.protectlab.org/
- **ragg**: https://ragg.r-lib.org/
- **metafor**: https://www.metafor-project.org/

---

## See Also

- [01-forest-plots.md](01-forest-plots.md) - Forest plots (use forestplot package)
- [02-funnel-plots.md](02-funnel-plots.md) - Funnel plots
- [04-multi-panel.md](04-multi-panel.md) - Combine plots into figures
- [05-table1-gtsummary.md](05-table1-gtsummary.md) - Tables (not plots)
- [07-themes-colors.md](07-themes-colors.md) - Color palettes and themes
