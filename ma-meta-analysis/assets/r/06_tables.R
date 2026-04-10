library(dplyr)
library(readr)
library(gtsummary)

raw <- read_csv("../05_extraction/extraction.csv", show_col_types = FALSE)

study_table <- raw %>%
  distinct(study_id, outcome_id, outcome_type, n, .keep_all = FALSE) %>%
  select(study_id, outcome_id, outcome_type, n)

summary_tbl <- study_table %>%
  tbl_summary(by = outcome_type) %>%
  bold_labels()

gtsave(summary_tbl, "tables/study_summary.html")
