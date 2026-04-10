library(dplyr)
library(readr)
library(metafor)

# Expected columns in extraction.csv
# study_id, outcome_id, arm_label, n, mean, sd, events, total, outcome_type

raw <- read_csv("../05_extraction/extraction.csv", show_col_types = FALSE)

continuous <- raw %>%
  filter(outcome_type == "continuous") %>%
  group_by(study_id, outcome_id) %>%
  mutate(arm_order = row_number()) %>%
  ungroup()

if (nrow(continuous) > 0) {
  cont_pairs <- continuous %>%
    group_by(study_id, outcome_id) %>%
    filter(n() == 2) %>%
    ungroup()

  cont_es <- escalc(
    measure = "SMD",
    m1i = cont_pairs$mean[cont_pairs$arm_order == 1],
    sd1i = cont_pairs$sd[cont_pairs$arm_order == 1],
    n1i = cont_pairs$n[cont_pairs$arm_order == 1],
    m2i = cont_pairs$mean[cont_pairs$arm_order == 2],
    sd2i = cont_pairs$sd[cont_pairs$arm_order == 2],
    n2i = cont_pairs$n[cont_pairs$arm_order == 2],
    slab = cont_pairs$study_id[cont_pairs$arm_order == 1]
  )
}

binary <- raw %>%
  filter(outcome_type == "binary") %>%
  group_by(study_id, outcome_id) %>%
  mutate(arm_order = row_number()) %>%
  ungroup()

if (nrow(binary) > 0) {
  bin_pairs <- binary %>%
    group_by(study_id, outcome_id) %>%
    filter(n() == 2) %>%
    ungroup()

  bin_es <- escalc(
    measure = "RR",
    ai = bin_pairs$events[bin_pairs$arm_order == 1],
    n1i = bin_pairs$total[bin_pairs$arm_order == 1],
    ci = bin_pairs$events[bin_pairs$arm_order == 2],
    n2i = bin_pairs$total[bin_pairs$arm_order == 2],
    slab = bin_pairs$study_id[bin_pairs$arm_order == 1]
  )
}
