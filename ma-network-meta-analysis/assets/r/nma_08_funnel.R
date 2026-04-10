# =============================================================================
# nma_08_funnel.R — Comparison-Adjusted Funnel Plot
# =============================================================================
# Purpose: Assess small-study effects / publication bias in NMA
# Input: net_re from nma_04_models.R
# Output: figures/nma_funnel.png
# =============================================================================

source("nma_04_models.R")

# --- 1. Comparison-adjusted funnel plot ---
cat("Generating comparison-adjusted funnel plot...\n")

png(file.path(FIG_DIR, "nma_funnel.png"),
    width = FIG_WIDTH, height = FIG_HEIGHT, units = "in", res = FIG_DPI)

funnel(net_re,
       order = netrank(net_re)$Pscore.random,
       pch = 16,
       col = "steelblue",
       legend = TRUE)

dev.off()
cat("Funnel plot saved to", file.path(FIG_DIR, "nma_funnel.png"), "\n")

# --- 2. Interpretation guide ---
cat("\n=== Funnel Plot Interpretation ===\n")
cat("- The comparison-adjusted funnel plot accounts for the network structure.\n")
cat("- Treatments are ordered by P-score (best to worst).\n")
cat("- Asymmetry suggests potential small-study effects or publication bias.\n")
cat("- Note: Funnel plot asymmetry tests have limited power with few studies.\n")

# --- 3. Egger-type test for NMA (if available) ---
# Note: Standard Egger's test doesn't directly apply to NMA.
# The comparison-adjusted funnel is the primary diagnostic.
cat("\nNote: Standard funnel plot asymmetry tests (Egger's) are not directly\n")
cat("applicable to NMA. The comparison-adjusted funnel plot is the primary\n")
cat("tool for assessing small-study effects in network meta-analysis.\n")
cat("See Chaimani & Salanti (2012) for methodology details.\n")
