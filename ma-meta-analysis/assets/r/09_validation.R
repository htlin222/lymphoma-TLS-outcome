library(dplyr)

# Basic consistency checks for extracted data
raw <- read.csv("../05_extraction/extraction.csv")

stopifnot(!any(is.na(raw$study_id)))

# Example range checks
if ("sd" %in% names(raw)) {
  stopifnot(all(raw$sd[!is.na(raw$sd)] >= 0))
}

if ("n" %in% names(raw)) {
  stopifnot(all(raw$n[!is.na(raw$n)] > 0))
}
