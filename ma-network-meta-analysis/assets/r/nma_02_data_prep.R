# =============================================================================
# nma_02_data_prep.R — Data Preparation for Network Meta-Analysis
# =============================================================================
# Purpose: Read extraction CSV, reshape to NMA format, validate network data
# Input: 05_extraction/extraction.csv
# Output: nma_data (contrast-based data frame ready for netmeta)
# =============================================================================

source("nma_01_setup.R")

# --- 1. Read extraction data ---
extraction <- read_csv("../05_extraction/extraction.csv", show_col_types = FALSE)

cat("Studies loaded:", nrow(extraction), "\n")
cat("Columns:", paste(names(extraction), collapse = ", "), "\n")

# --- 2. Prepare contrast-based data ---
# Option A: Data already in contrast format (TE, seTE, treat1, treat2)
# Uncomment and adapt column names:
#
# nma_data <- extraction %>%
#   select(
#     studlab  = study_id,
#     treat1   = treatment_1,
#     treat2   = treatment_2,
#     TE       = effect_estimate,    # log-scale for RR/OR/HR
#     seTE     = standard_error
#   ) %>%
#   filter(!is.na(TE), !is.na(seTE))

# Option B: Data in arm-based format (events + totals per arm)
# Use pairwise() to convert:
#
# nma_data <- pairwise(
#   treat = treatment,
#   event = events,
#   n     = total_n,
#   studlab = study_id,
#   data  = extraction,
#   sm    = "RR"         # "RR", "OR", "RD", "MD", "SMD"
# )

# --- 3. Validate data ---
cat("\n--- Data Summary ---\n")
cat("Number of contrasts:", nrow(nma_data), "\n")
cat("Unique studies:", length(unique(nma_data$studlab)), "\n")
cat("Unique treatments:", length(unique(c(nma_data$treat1, nma_data$treat2))), "\n")
cat("Treatments:", paste(sort(unique(c(nma_data$treat1, nma_data$treat2))), collapse = ", "), "\n")

# --- 4. Check for missing data ---
missing_te   <- sum(is.na(nma_data$TE))
missing_se   <- sum(is.na(nma_data$seTE))
cat("\nMissing TE:", missing_te, "\n")
cat("Missing seTE:", missing_se, "\n")

if (missing_te > 0 || missing_se > 0) {
  warning("Missing effect estimates detected. Review extraction data.")
}

# --- 5. Save prepared data ---
write_csv(nma_data, "nma_prepared_data.csv")
cat("\nPrepared data saved to nma_prepared_data.csv\n")
