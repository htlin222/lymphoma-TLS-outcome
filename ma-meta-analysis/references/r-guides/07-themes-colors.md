# Themes and Color Palettes for Meta-Analysis Figures

**When to use**: You want professional, journal-appropriate styling for your plots
**Time**: 10-15 minutes
**Stage**: Any (applies to all figure generation)

**Packages**:

```r
library(ggplot2)         # Base plotting
library(ggsci)           # Scientific journal color palettes (400+ palettes)
library(viridis)         # Colorblind-safe continuous palettes
library(khroma)          # 62 science-specific colorblind-safe palettes
library(paletteer)       # Meta-package: 2,893 palettes from 79 packages
library(hrbrthemes)      # Professional typography themes
library(ragg)            # Modern text rendering (cross-platform)
library(systemfonts)     # Font discovery and registration
library(colorBlindness)  # CVD simulation for accessibility testing
```

---

## Quick Start: Journal-Specific Palette

```r
library(ggplot2)
library(ggsci)

p <- ggplot(data, aes(x = subgroup, y = effect, fill = subgroup)) +
  geom_bar(stat = "identity") +
  scale_fill_lancet() +   # Lancet journal colors
  theme_minimal(base_size = 14) +
  theme(legend.position = "bottom")

ggsave("figures/plot_lancet.png", p, width = 8, height = 6, dpi = 300)
```

---

## Journal Color Palettes (ggsci 4.0+)

ggsci 4.0+ includes 400+ palettes covering all major scientific journals.

### Available Palettes

```r
library(ggsci)

# Lancet Oncology (red/blue/green)
scale_color_lancet()
scale_fill_lancet()

# NEJM (blue/red/green/purple)
scale_color_nejm()
scale_fill_nejm()

# JAMA (blue/red/gray)
scale_color_jama()
scale_fill_jama()

# Nature (vibrant multi-color)
scale_color_npg()
scale_fill_npg()

# BMJ (subdued, professional) - added in ggsci 4.0+
scale_color_bmj()
scale_fill_bmj()

# Annals of Oncology
scale_color_aaas()
scale_fill_aaas()
```

### Manual Color Vectors

```r
# Extract palette colors for manual use
lancet_colors <- pal_lancet()(7)
# [1] "#00468BFF" "#ED0000FF" "#42B540FF" "#0099B4FF" "#925E9FFF" "#FDAF91FF" "#AD002AFF"

nejm_colors <- pal_nejm()(8)
jama_colors <- pal_jama()(7)
bmj_colors <- pal_bmj()(9)
```

---

## Colorblind-Safe Palettes

### khroma (Recommended for Discrete Scales)

khroma provides 62 science-specific colorblind-safe palettes, including Okabe-Ito and Paul Tol schemes. Preferred over manually defining hex codes.

```r
library(khroma)

# Okabe-Ito palette (universally accessible, 8 colors)
khroma::color("okabeito")(8)
scale_color_okabeito()
scale_fill_okabeito()

# Paul Tol's bright scheme (7 colors, high contrast)
khroma::color("bright")(7)
scale_color_bright()
scale_fill_bright()

# Paul Tol's muted scheme (9 colors, softer)
khroma::color("muted")(9)
scale_color_muted()
scale_fill_muted()

# Paul Tol's vibrant scheme (7 colors)
khroma::color("vibrant")(7)
scale_color_vibrant()
scale_fill_vibrant()

# Example: subgroup forest plot with Okabe-Ito
ggplot(data, aes(x = effect, y = study, color = subgroup)) +
  geom_point(size = 3) +
  scale_color_okabeito() +
  theme_minimal(base_size = 14)
```

### viridis (Recommended for Continuous Scales)

```r
library(viridis)

# Continuous scale
scale_color_viridis_c()
scale_fill_viridis_c()

# Discrete scale
scale_color_viridis_d()
scale_fill_viridis_d()

# Options: "magma", "inferno", "plasma", "viridis", "cividis"
scale_fill_viridis_d(option = "plasma")
```

### Built-in Okabe-Ito (R 4.0+, No Package Needed)

R 4.0+ includes Okabe-Ito as a built-in palette via `grDevices`:

```r
# No package installation required
okabe_ito <- palette.colors(n = 8, palette = "Okabe-Ito")

# Use with ggplot2
scale_fill_manual(values = okabe_ito)
scale_color_manual(values = okabe_ito)

# Also available:
grDevices::palette.colors(palette = "Okabe-Ito")
```

### Manual Colorblind-Safe Discrete Palette

For environments where khroma is not available and R < 4.0:

```r
# Okabe-Ito palette (universally accessible)
cb_palette <- c(
  "#E69F00",  # Orange
  "#56B4E9",  # Sky blue
  "#009E73",  # Green
  "#F0E442",  # Yellow
  "#0072B2",  # Blue
  "#D55E00",  # Red-orange
  "#CC79A7",  # Pink
  "#999999"   # Gray
)

scale_fill_manual(values = cb_palette)
scale_color_manual(values = cb_palette)
```

---

## Palette Discovery with paletteer

paletteer provides a single interface to 2,893 palettes from 79 packages, including ggsci, khroma, viridis, and more.

```r
library(paletteer)

# Browse available discrete palettes
paletteer::palettes_d_names

# Use journal palettes via unified syntax
scale_fill_paletteer_d("ggsci::lancet_lanonc")
scale_color_paletteer_d("ggsci::nejm_default")

# Access khroma palettes through paletteer
paletteer::paletteer_d("khroma::bright", n = 5)
paletteer::paletteer_d("khroma::okabeito", n = 8)

# Continuous palettes
scale_fill_paletteer_c("viridis::plasma")

# Extract colors as a vector
my_colors <- paletteer::paletteer_d("ggsci::jama_default", n = 4)

# Useful for comparing palettes side-by-side
# when choosing between journal styles
```

---

## Accessibility Validation

### Simulate Color Vision Deficiency

Always test your figures for colorblind accessibility before submission.

```r
library(colorBlindness)

# Create your plot
p <- ggplot(data, aes(x = subgroup, y = effect, fill = subgroup)) +
  geom_bar(stat = "identity") +
  scale_fill_lancet()

# Simulate all CVD types (deuteranopia, protanopia, tritanopia)
cvdPlot(p)
# Produces a panel showing how the plot appears under each deficiency
```

### Check Palette Accessibility Programmatically

```r
library(colorblindcheck)

# Check if a custom palette is accessible
my_colors <- c("#E69F00", "#56B4E9", "#009E73", "#F0E442")
palette_check(my_colors)
# Returns min/mean color distances for each CVD type
# Aim for minimum distance > 10 for safe discrimination
```

### WCAG 2.2 Accessibility Standards

Follow these contrast ratios for publication figures:

- **Non-text elements** (lines, bars, points): minimum **3:1** contrast ratio against background
- **Small text** (annotations, axis labels < 18pt): minimum **4.5:1** contrast ratio
- **Large text** (titles >= 18pt): minimum **3:1** contrast ratio
- **Always use secondary differentiators** alongside color: shape, pattern, linetype, or direct labels

```r
# Use multiple visual channels, not just color
aes(color = group, shape = group, linetype = group)

# Add direct labels where possible (eliminates legend dependency)
library(ggrepel)
geom_text_repel(aes(label = study_label))
```

---

## Professional Themes

### hrbrthemes (Clean Typography)

```r
library(hrbrthemes)

# Professional theme
p + theme_ipsum()

# Minimal variant
p + theme_ipsum_rc()

# With grid lines
p + theme_ipsum(grid = "Y")  # Horizontal grid only
```

### Built-in ggplot2 Themes

```r
# Minimal (recommended for meta-analysis)
p + theme_minimal(base_size = 14)

# Classic (white background, no grid)
p + theme_classic(base_size = 14)

# Black and white (for print)
p + theme_bw(base_size = 14)
```

### Custom Meta-Analysis Theme

```r
theme_meta <- function(base_size = 14) {
  theme_minimal(base_size = base_size) %+replace%
    theme(
      plot.title = element_text(face = "bold", size = base_size * 1.2, hjust = 0),
      plot.subtitle = element_text(color = "gray40", size = base_size * 0.9),
      axis.title = element_text(face = "bold"),
      legend.position = "bottom",
      legend.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      panel.grid.major.x = element_blank(),
      strip.text = element_text(face = "bold")
    )
}

# Apply
p + theme_meta()
```

---

## Modern Font Handling (systemfonts + ragg)

systemfonts and ragg provide reliable cross-platform font rendering, avoiding common issues with hrbrthemes and base R graphics devices.

### Discover and Register Fonts

```r
library(systemfonts)

# List all available system fonts
system_fonts()

# Register a custom font family for use in plots
register_font(
  name = "CustomArial",
  plain = "/path/to/ArialMT.ttf",
  bold = "/path/to/Arial-BoldMT.ttf",
  italic = "/path/to/Arial-ItalicMT.ttf"
)
```

### Render with ragg (Recommended for ggsave)

ragg produces consistent text rendering across macOS, Linux, and Windows:

```r
library(ragg)

# Use ragg as the graphics device for ggsave
ggsave("figures/figure1.png", p,
       width = 10, height = 8, dpi = 300,
       device = agg_png)

# Or use directly for base R plots
agg_png("figures/figure1.png", width = 10, height = 8, units = "in", res = 300)
forest(res)
dev.off()

# Set ragg as default device for RStudio (add to .Rprofile)
# options(device = function(...) ragg::agg_png(...))
```

**Why ragg over png()?** Base R `png()` uses different text rendering engines per OS, causing font mismatches. `ragg::agg_png()` uses a consistent engine everywhere.

---

## Common Scenarios

### Scenario 1: Black and White (Most Journals)

Most medical journals prefer black/white/gray:

```r
# Grayscale palette
gray_palette <- c("gray20", "gray40", "gray60", "gray80")

p + scale_fill_manual(values = gray_palette) +
  theme_classic(base_size = 14)
```

### Scenario 2: Forest Plot Colors (forestplot Package)

```r
library(forestplot)

# Standard (black - recommended)
col = fpColors(box = "black", lines = "black", zero = "gray50", summary = "black")

# Lancet-style (if journal requests)
col = fpColors(box = "#00468B", lines = "#00468B", zero = "gray50", summary = "#ED0000")
```

### Scenario 3: Heatmap with Colorblind-Safe Scale

```r
library(ggplot2)
library(viridis)

ggplot(cor_matrix, aes(x = Var1, y = Var2, fill = value)) +
  geom_tile() +
  scale_fill_viridis_c(option = "plasma", name = "Correlation") +
  theme_minimal(base_size = 12) +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

---

## Typography Standards

### Font Sizes for Journals

```r
# Title: 14-16pt bold
# Axis labels: 12-14pt bold
# Axis ticks: 10-12pt
# Legend: 10-12pt
# Annotations: 9-10pt

theme(
  plot.title = element_text(size = 16, face = "bold"),
  axis.title = element_text(size = 14, face = "bold"),
  axis.text = element_text(size = 12),
  legend.text = element_text(size = 12),
  legend.title = element_text(size = 12, face = "bold")
)
```

---

## Troubleshooting

### Problem: Colors look different in print vs screen

**Solution**: Test with grayscale conversion and CVD simulation

```r
# Convert to grayscale to check readability
library(grDevices)
p + scale_fill_grey()

# Also simulate colorblind vision
library(colorBlindness)
cvdPlot(p)
```

### Problem: Font not available (hrbrthemes)

**Solution**: Use systemfonts + ragg instead of fighting font issues

```r
# Modern approach: use ragg for consistent rendering
library(ragg)
ggsave("figures/plot.png", p, device = agg_png, dpi = 300)

# List available fonts to find alternatives
library(systemfonts)
system_fonts() |> dplyr::filter(grepl("Arial|Helvetica", family))

# Legacy approach: install fonts for hrbrthemes
hrbrthemes::import_roboto_condensed()

# Fallback: use a built-in theme
theme_minimal(base_size = 14)
```

### Problem: Too many colors needed

**Solution**: Use shape/linetype in addition to color (required by WCAG 2.2)

```r
# Multiple visual channels
aes(color = group, shape = group, linetype = group)

# Or use faceting to reduce color needs
facet_wrap(~subgroup)
```

---

## Package Documentation

- **ggplot2**: https://ggplot2.tidyverse.org/reference/theme.html
- **ggsci**: https://cran.r-project.org/web/packages/ggsci/
- **viridis**: https://cran.r-project.org/web/packages/viridis/
- **khroma**: https://cran.r-project.org/web/packages/khroma/
- **paletteer**: https://cran.r-project.org/web/packages/paletteer/
- **hrbrthemes**: https://cran.r-project.org/web/packages/hrbrthemes/
- **ragg**: https://cran.r-project.org/web/packages/ragg/
- **systemfonts**: https://cran.r-project.org/web/packages/systemfonts/
- **colorBlindness**: https://cran.r-project.org/web/packages/colorBlindness/
- **colorblindcheck**: https://cran.r-project.org/web/packages/colorblindcheck/

---

## See Also

- [00-setup.md](00-setup.md) - Install theme and color packages
- [01-forest-plots.md](01-forest-plots.md) - Apply colors to forest plots
- [04-multi-panel.md](04-multi-panel.md) - Consistent themes across panels
- [08-ggplot2-patterns.md](08-ggplot2-patterns.md) - ggplot2 best practices
