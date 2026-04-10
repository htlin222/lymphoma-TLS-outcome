# Multi-Panel Figures

**When to use**: You need to combine multiple plots into a single figure (e.g., Figure 1A, 1B, 1C)
**Time**: 15-20 minutes
**Stage**: 07 (Manuscript)

**Packages**:

```r
library(patchwork)   # Combine ggplot2 plots (recommended, v1.3.0+)
library(ragg)        # Superior raster rendering (recommended backend)
library(cowplot)     # Alternative: precise layout control
library(ggplot2)     # Base plots
library(grid)        # Panel labels for base R plots
library(magick)      # PNG/TIFF assembly (simpler alternative to grid)
library(svglite)     # SVG vector export
library(multipanelfigure)  # mm-based journal layouts
```

---

## Quick Start: Combine Plots with patchwork

```r
library(ggplot2)
library(patchwork)

# Create individual plots
p1 <- ggplot(mtcars, aes(mpg, hp)) +
  geom_point() +
  labs(title = "Plot A") +
  theme_minimal()

p2 <- ggplot(mtcars, aes(mpg, wt)) +
  geom_point() +
  labs(title = "Plot B") +
  theme_minimal()

p3 <- ggplot(mtcars, aes(factor(cyl), mpg)) +
  geom_boxplot() +
  labs(title = "Plot C") +
  theme_minimal()

# Combine: A on top, B and C side-by-side below
combined <- p1 / (p2 | p3) +
  plot_annotation(
    tag_levels = "A",
    title = "Figure 1. Study Results",
    theme = theme(plot.title = element_text(face = "bold", size = 16))
  )

# Save at 300 DPI using ragg for superior rendering
ragg::agg_png("figures/figure1_combined.png",
              width = 3600, height = 3000, res = 300)
print(combined)
dev.off()

# Or use ggsave with ragg backend
ggsave("figures/figure1_combined.png", combined,
       width = 12, height = 10, dpi = 300, device = ragg::agg_png)

cat("Done! Multi-panel figure saved.\n")
```

---

## Layout Operators (patchwork)

```r
# Side by side
p1 | p2

# Stacked vertically
p1 / p2

# Complex layouts
p1 / (p2 | p3)          # A on top, B+C below
(p1 | p2) / (p3 | p4)   # 2x2 grid
p1 | (p2 / p3)           # A left, B+C stacked right

# Control relative widths/heights
(p1 | p2) + plot_layout(widths = c(2, 1))   # A is 2x wider
(p1 / p2) + plot_layout(heights = c(1, 2))  # B is 2x taller
```

### patchwork v1.3.0+ Features

```r
# Embed a gt table alongside plots
library(gt)
tbl <- gt(head(mtcars[, 1:4])) |> tab_header(title = "Summary")
(p1 | wrap_table(tbl)) / p2 +
  plot_annotation(tag_levels = "A")

# Independent axis scales per panel using free()
(free(p1) | free(p2, side = "y")) / p3

# Merge overlapping plot elements (e.g., shared legends)
(p1 + p2) + plot_layout(guides = "collect") & theme(legend.position = "bottom")
```

---

## Common Scenarios

### Scenario 1: Forest Plot + Funnel Plot (Most Common)

```r
library(ggplot2)
library(patchwork)
library(metafor)

# Prepare data
data <- read.csv("05_extraction/extraction.csv")
es <- escalc(measure = "RR",
             ai = events_intervention, n1i = n_intervention,
             ci = events_control, n2i = n_control,
             data = data)
res <- rma(yi, vi, data = es, method = "DL")

# Panel A: Forest plot (as ggplot)
df_forest <- data.frame(
  study = paste0(data$author, " (", data$year, ")"),
  rr = exp(es$yi),
  lo = exp(es$yi - 1.96 * sqrt(es$vi)),
  hi = exp(es$yi + 1.96 * sqrt(es$vi))
)
df_forest$study <- factor(df_forest$study, levels = rev(df_forest$study))

p_forest <- ggplot(df_forest, aes(x = rr, y = study, xmin = lo, xmax = hi)) +
  geom_pointrange(size = 0.5) +
  geom_vline(xintercept = 1, linetype = "dashed", color = "gray50") +
  scale_x_log10() +
  labs(x = "Risk Ratio (log scale)", y = NULL, title = "Forest Plot") +
  theme_minimal(base_size = 12)

# Panel B: Funnel plot (as ggplot)
df_funnel <- data.frame(yi = es$yi, sei = sqrt(es$vi))

p_funnel <- ggplot(df_funnel, aes(x = yi, y = sei)) +
  geom_point(size = 3) +
  geom_vline(xintercept = res$beta[1], linetype = "dashed", color = "gray50") +
  scale_y_reverse() +
  labs(x = "Log Risk Ratio", y = "Standard Error", title = "Funnel Plot") +
  theme_minimal(base_size = 12)

# Combine
figure1 <- p_forest | p_funnel
figure1 <- figure1 + plot_annotation(tag_levels = "A")

# Export as TIFF for journal submission (LZW compression)
ragg::agg_tiff("figures/figure1.tif",
               width = 4200, height = 2100, res = 300, compression = "lzw")
print(figure1)
dev.off()

# Also save PNG for quick review
ggsave("figures/figure1.png", figure1,
       width = 14, height = 7, dpi = 300, device = ragg::agg_png)
```

### Scenario 2: Assemble Pre-Made PNG Files with magick

**When**: You have individual PNG files (e.g., from forestplot or base R) and need to combine them.

```r
library(magick)

# Read pre-made PNGs
img1 <- image_read("figures/forest_plot.png")
img2 <- image_read("figures/funnel_plot.png")
img3 <- image_read("figures/sensitivity.png")

# Add panel labels
img1 <- image_annotate(img1, "A", size = 60, weight = 700,
                        location = "+20+10", color = "black")
img2 <- image_annotate(img2, "B", size = 60, weight = 700,
                        location = "+20+10", color = "black")
img3 <- image_annotate(img3, "C", size = 60, weight = 700,
                        location = "+20+10", color = "black")

# Resize to uniform dimensions if needed
img2 <- image_resize(img2, geometry_size_pixels(width = image_info(img3)$width))

# Arrange: A on top (full width), B and C side-by-side below
bottom_row <- image_append(c(img2, img3), stack = FALSE)
bottom_row <- image_resize(bottom_row,
                           geometry_size_pixels(width = image_info(img1)$width))
assembled <- image_append(c(img1, bottom_row), stack = TRUE)

# Save at high resolution
image_write(assembled, "figures/figure1_assembled.png", format = "png")

# Or save as TIFF for journal submission
image_write(assembled, "figures/figure1_assembled.tif", format = "tiff",
            compression = "lzw")
```

#### Alternative: grid-based PNG Assembly (Fine-Grained Control)

For more precise viewport control, use grid and gridExtra directly:

```r
library(png)
library(grid)
library(gridExtra)

# Read pre-made PNGs
img1 <- readPNG("figures/forest_plot.png")
img2 <- readPNG("figures/funnel_plot.png")
img3 <- readPNG("figures/sensitivity.png")

# Convert to grob objects
g1 <- rasterGrob(img1, interpolate = TRUE)
g2 <- rasterGrob(img2, interpolate = TRUE)
g3 <- rasterGrob(img3, interpolate = TRUE)

# Arrange with labels
ragg::agg_png("figures/figure1_assembled.png",
              width = 4200, height = 3000, res = 300)

grid.newpage()
pushViewport(viewport(layout = grid.layout(2, 2)))

# Panel A (top, spanning full width)
pushViewport(viewport(layout.pos.row = 1, layout.pos.col = 1:2))
grid.draw(g1)
grid.text("A", x = 0.02, y = 0.98, gp = gpar(fontsize = 18, fontface = "bold"))
popViewport()

# Panel B (bottom-left)
pushViewport(viewport(layout.pos.row = 2, layout.pos.col = 1))
grid.draw(g2)
grid.text("B", x = 0.04, y = 0.96, gp = gpar(fontsize = 18, fontface = "bold"))
popViewport()

# Panel C (bottom-right)
pushViewport(viewport(layout.pos.row = 2, layout.pos.col = 2))
grid.draw(g3)
grid.text("C", x = 0.04, y = 0.96, gp = gpar(fontsize = 18, fontface = "bold"))
popViewport()

dev.off()
```

### Scenario 3: cowplot for Precise Control

```r
library(cowplot)
library(ggplot2)

# Create individual plots
p1 <- ggplot(mtcars, aes(mpg, hp)) + geom_point() + theme_minimal()
p2 <- ggplot(mtcars, aes(mpg, wt)) + geom_point() + theme_minimal()

# Combine with precise sizing
combined <- plot_grid(
  p1, p2,
  labels = c("A", "B"),
  label_size = 18,
  label_fontface = "bold",
  ncol = 2,
  rel_widths = c(1.2, 1)  # A is slightly wider
)

ggsave("figures/figure_cowplot.png", combined,
       width = 14, height = 7, dpi = 300, device = ragg::agg_png)
```

### Scenario 4: multipanelfigure for Journal-Ready Dimensions

**When**: You need precise mm-based layouts that match journal column widths exactly.

```r
library(multipanelfigure)

# Create figure matching Nature double-column width (183mm x 247mm max)
fig <- multi_panel_figure(
  width = 183, height = 180,
  columns = 2, rows = 2,
  unit = "mm",
  panel_label_type = "upper-alpha"  # A, B, C labels
)

# Fill panels (accepts ggplot objects, grobs, or file paths)
fig <- fill_panel(fig, p_forest, row = 1, column = 1:2)  # span full width
fig <- fill_panel(fig, p_funnel, row = 2, column = 1)
fig <- fill_panel(fig, p_sensitivity, row = 2, column = 2)

# Save with ragg for consistent rendering
ragg::agg_tiff("figures/figure1_nature.tif",
               width = 183, height = 180, units = "mm", res = 300,
               compression = "lzw")
print(fig)
dev.off()
```

---

## Rendering Backend: ragg

The **ragg** package provides superior raster rendering compared to base R devices. Benefits include 40% faster rendering, better antialiasing, consistent cross-platform output, and proper Unicode/font handling.

```r
library(ragg)

# PNG export (replaces base png())
agg_png("figures/figure1.png",
        width = 3600, height = 3000, res = 300)
print(combined)
dev.off()

# TIFF with LZW compression (preferred for journal submission)
agg_tiff("figures/figure1.tif",
         width = 3600, height = 3000, res = 300,
         compression = "lzw")
print(combined)
dev.off()

# Use ragg as the default ggsave backend
ggsave("figures/figure1.png", combined,
       width = 12, height = 10, dpi = 300,
       device = ragg::agg_png)

ggsave("figures/figure1.tif", combined,
       width = 12, height = 10, dpi = 300,
       device = ragg::agg_tiff)
```

---

## Export Formats by Use Case

| Format     | Use Case                    | Package              | Notes                                    |
| ---------- | --------------------------- | -------------------- | ---------------------------------------- |
| TIFF (LZW) | Journal submission          | `ragg::agg_tiff()`   | Preferred by Nature, Lancet, JAMA        |
| PNG        | Quick review, presentations | `ragg::agg_png()`    | Smaller files, web-friendly              |
| SVG        | Web supplements, editing    | `svglite::svglite()` | Scalable vector, editable in Illustrator |
| PDF        | LaTeX manuscripts           | `cairo_pdf()`        | Vector, embeddable                       |

### SVG Export for Web and Supplementary Materials

```r
library(svglite)

# Export as SVG (vector graphics, scalable)
svglite("figures/figure1.svg", width = 12, height = 10)
print(combined)
dev.off()

# ggsave with svglite
ggsave("figures/figure1.svg", combined,
       width = 12, height = 10, device = svglite::svglite)
```

---

## Journal-Specific Dimension Standards

Use these dimensions when preparing figures for submission. All values at 300 DPI minimum.

| Journal     | Single Column   | Double Column    | Max Height       | Preferred Format  |
| ----------- | --------------- | ---------------- | ---------------- | ----------------- |
| **Nature**  | 89 mm (1051 px) | 183 mm (2163 px) | 247 mm (2917 px) | TIFF (LZW)        |
| **Science** | 90 mm (1063 px) | 180 mm (2126 px) | 240 mm (2835 px) | TIFF (LZW)        |
| **Lancet**  | 89 mm (1051 px) | 183 mm (2163 px) | 247 mm (2917 px) | TIFF (LZW)        |
| **JAMA**    | 86 mm (1016 px) | 178 mm (2102 px) | 235 mm (2776 px) | TIFF (LZW)        |
| **BMJ**     | 84 mm (992 px)  | 174 mm (2055 px) | 240 mm (2835 px) | TIFF (LZW) or EPS |

Pixel values calculated at 300 DPI: `pixels = mm / 25.4 * 300`

### Journal-Specific Export Examples

```r
library(ragg)

# Nature: double-column figure
agg_tiff("figures/figure1_nature.tif",
         width = 183, height = 180, units = "mm",
         res = 300, compression = "lzw")
print(combined)
dev.off()

# JAMA: single-column figure
agg_tiff("figures/figure1_jama.tif",
         width = 86, height = 120, units = "mm",
         res = 300, compression = "lzw")
print(combined)
dev.off()

# Lancet: double-column figure
agg_tiff("figures/figure1_lancet.tif",
         width = 183, height = 200, units = "mm",
         res = 300, compression = "lzw")
print(combined)
dev.off()
```

---

## Panel Label Standards

**Journal requirements** for multi-panel figures:

- Labels: **A**, **B**, **C** (uppercase, bold)
- Position: **top-left** corner of each panel
- Font size: **14-18pt** (larger than axis labels)
- Style: **bold**, sans-serif

```r
# patchwork auto-labels
plot_annotation(
  tag_levels = "A",
  tag_prefix = "",
  tag_suffix = "",
  theme = theme(
    plot.tag = element_text(size = 18, face = "bold")
  )
)
```

---

## Troubleshooting

### Problem: Plots have different theme styles

**Solution**: Apply consistent theme to all plots before combining

```r
theme_set(theme_minimal(base_size = 12))
# Now all plots use the same theme
```

### Problem: Legend takes too much space

**Solution**: Collect legends with patchwork

```r
combined <- (p1 | p2) + plot_layout(guides = "collect")
```

### Problem: Unequal panel sizes

**Solution**: Use `plot_layout()` to control dimensions

```r
(p1 | p2 | p3) + plot_layout(widths = c(2, 1, 1))
```

### Problem: Panels need independent axis scales

**Solution**: Use `free()` from patchwork v1.3.0+

```r
# Free y-axis on second panel only
(p1 | free(p2, side = "y")) + plot_annotation(tag_levels = "A")
```

### Problem: Need to mix base R and ggplot2

**Solution**: Save base R plots as PNG with ragg, then combine

```r
# Save base R plot using ragg
ragg::agg_png("temp_base.png", width = 3000, height = 2400, res = 300)
forest(res)  # base R plot
dev.off()

# Read back and combine with ggplot
library(png)
library(patchwork)
img <- readPNG("temp_base.png")
p_base <- ggplot() + annotation_raster(img, -Inf, Inf, -Inf, Inf) + theme_void()
combined <- p_base | p_ggplot
```

### Problem: TIFF file too large for submission

**Solution**: Use LZW compression with ragg

```r
# LZW compression reduces TIFF size by 50-80%
ragg::agg_tiff("figures/figure1.tif",
               width = 183, height = 180, units = "mm",
               res = 300, compression = "lzw")
print(combined)
dev.off()
```

---

## Package Documentation

- **patchwork**: https://patchwork.data-imaginist.com/
- **ragg**: https://ragg.r-lib.org/
- **cowplot**: https://wilkelab.org/cowplot/
- **magick**: https://docs.ropensci.org/magick/
- **svglite**: https://svglite.r-lib.org/
- **multipanelfigure**: https://cran.r-project.org/package=multipanelfigure
- **gridExtra**: https://cran.r-project.org/package=gridExtra

---

## See Also

- [01-forest-plots.md](01-forest-plots.md) - Create individual forest plots
- [02-funnel-plots.md](02-funnel-plots.md) - Create individual funnel plots
- [03-subgroup-plots.md](03-subgroup-plots.md) - Subgroup plots to combine
- [07-themes-colors.md](07-themes-colors.md) - Consistent styling across panels
