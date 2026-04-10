library(meta)
library(ggplot2)

# ---------------------------------------------------------------------------
# Helper: calculate dynamic PNG height for meta::forest()
#
# meta::forest() uses base R graphics and does NOT auto-size the PNG canvas.
# A fixed height causes either massive white padding (too tall) or clipped
# text (too short). This function calculates the right height based on the
# number of rows the plot will contain.
#
# Formula: height_in = header + (n_rows * row_height) + footer
#   - header (title, column labels): ~1.0 in
#   - each study row: ~0.35 in (with spacing=1.5 this becomes ~0.45)
#   - subgroup header: ~0.4 in
#   - footer (heterogeneity stats, x-axis, prediction): ~1.5 in
#   - extra for subgroup test line: +0.4 in
# ---------------------------------------------------------------------------
forest_height <- function(model, subgroups = FALSE, spacing = 1.0) {
  k <- model$k  # number of studies
  header  <- 1.0
  row_h   <- 0.35 * spacing
  footer  <- 1.5
  n_rows  <- k + 1  # studies + overall summary

  if (subgroups && !is.null(model$bylevs)) {
    n_sg   <- length(model$bylevs)
    n_rows <- n_rows + n_sg * 2  # subgroup header + subtotal per group
    footer <- footer + 0.4       # extra space for "Test for subgroup differences"
  }

  height_in <- header + (n_rows * row_h) + footer
  # Enforce reasonable bounds
  height_in <- max(height_in, 4)
  height_in <- min(height_in, 20)
  return(height_in)
}

# Width: 10 in is good for most forest plots (gives room for labels + CI columns)
FOREST_WIDTH_IN <- 10

if (exists("cont_model")) {
  h <- forest_height(cont_model)
  png("figures/forest_continuous.png",
      width = FOREST_WIDTH_IN, height = h, units = "in", res = 300)
  par(mar = c(4, 0, 1, 0))  # bottom, left, top, right margins
  forest(cont_model, spacing = 1.5)
  dev.off()

  # Funnel plot on log scale for symmetric shading
  # backtransf=FALSE keeps the x-axis on the log(effect) scale, which makes
  # the confidence region symmetric and easier to judge for publication bias.
  png("figures/funnel_continuous.png",
      width = 7, height = 6, units = "in", res = 300)
  funnel(cont_model, backtransf = FALSE,
         xlab = paste0("Log ", cont_model$sm),
         studlab = TRUE, cex.studlab = 0.8,
         col = "navy", pch = 16)
  dev.off()
}

if (exists("bin_model")) {
  h <- forest_height(bin_model)
  png("figures/forest_binary.png",
      width = FOREST_WIDTH_IN, height = h, units = "in", res = 300)
  par(mar = c(4, 0, 1, 0))
  forest(bin_model, spacing = 1.5)
  dev.off()

  # Funnel plot on log scale for ratio measures (RR, OR, HR)
  png("figures/funnel_binary.png",
      width = 7, height = 6, units = "in", res = 300)
  funnel(bin_model, backtransf = FALSE,
         xlab = paste0("Log ", bin_model$sm),
         studlab = TRUE, cex.studlab = 0.8,
         col = "navy", pch = 16)
  dev.off()
}
