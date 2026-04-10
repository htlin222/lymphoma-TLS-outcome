#!/usr/bin/env Rscript
# Render all manuscript tables as PNG images using gt
library(gt)
library(dplyr)
library(readr)

project_root <- "/Users/htlin/meta-pipe/projects/ici-breast-cancer"
out_dir <- file.path(project_root, "07_manuscript", "table_images")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

extraction <- read_csv(file.path(project_root, "05_extraction", "round-01_extraction.csv"), show_col_types = FALSE)
safety <- read_csv(file.path(project_root, "05_extraction", "round-01_safety_data.csv"), show_col_types = FALSE)
pcr_results <- read_csv(file.path(project_root, "06_analysis", "tables_pCR_meta_analysis_results.csv"), show_col_types = FALSE)
efs_results <- read_csv(file.path(project_root, "06_analysis", "tables_EFS_meta_analysis_results.csv"), show_col_types = FALSE)
os_results <- read_csv(file.path(project_root, "06_analysis", "tables_OS_meta_analysis_results.csv"), show_col_types = FALSE)
safety_results <- read_csv(file.path(project_root, "06_analysis", "tables_safety_meta_analysis_summary.csv"), show_col_types = FALSE)

cat("Rendering Table 1...\n")
tbl1 <- extraction |>
  transmute(
    Trial = trial_name,
    `Author (Year)` = paste0(first_author, " (", publication_year, ")"),
    Design = gsub("RCT_", "", study_design) |> gsub("phase", "Phase ", x = _),
    Blinding = gsub("_", "-", blinding),
    N = n_randomized_total,
    `N(ICI)` = n_intervention,
    `N(Ctrl)` = n_control,
    `ICI Agent` = paste0(tools::toTitleCase(ici_agent), " ", ici_dose, " ", ici_schedule),
    Chemotherapy = gsub("\u2192", " then ", chemo_backbone),
    `F/U (mo)` = median_followup_months,
    Outcomes = case_when(
      !is.na(OS_HR) & !is.na(EFS_HR) ~ "pCR, EFS, OS",
      !is.na(EFS_HR) ~ "pCR, EFS",
      TRUE ~ "pCR"
    )
  ) |>
  gt() |>
  tab_header(title = "Table 1. Characteristics of Included Randomized Controlled Trials") |>
  tab_options(
    table.font.size = px(11),
    data_row.padding = px(5),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  cols_align(align = "right", columns = c(N, `N(ICI)`, `N(Ctrl)`, `F/U (mo)`)) |>
  tab_source_note("AC = doxorubicin/cyclophosphamide; EC = epirubicin/cyclophosphamide; F/U = follow-up. All trials enrolled TNBC patients. Total N=2,402.")

gtsave(tbl1, file.path(out_dir, "table1_characteristics.png"), vwidth = 1200, vheight = 600, zoom = 2)

cat("Rendering Table 2...\n")
pooled_pcr <- pcr_results |> filter(grepl("POOLED", Trial))
pooled_efs <- efs_results |> filter(grepl("Pooled", Trial))
pooled_os  <- os_results  |> filter(grepl("Pooled", Trial))

tbl2 <- data.frame(
  Outcome = c("pCR", "EFS (5-year)", "OS (5-year)"),
  Trials = c(
    paste0("5 (N=", pooled_pcr$N_Total, ")"),
    paste0("3 (N=", pooled_efs$N_Total, ")"),
    paste0("2 (N=", pooled_os$N_Total, ")")
  ),
  ICI = c(
    paste0(sum(as.numeric(extraction$pCR_intervention_n), na.rm = TRUE),
           "/", sum(as.numeric(extraction$pCR_intervention_total), na.rm = TRUE)),
    "81.2%", "86.6%"
  ),
  Control = c(
    paste0(sum(as.numeric(extraction$pCR_control_n), na.rm = TRUE),
           "/", sum(as.numeric(extraction$pCR_control_total), na.rm = TRUE)),
    "72.2%", "81.7%"
  ),
  Effect = c(
    paste0("RR ", pooled_pcr$RR),
    paste0("HR ", pooled_efs$HR),
    paste0("HR ", pooled_os$HR)
  ),
  CI_95 = c(pooled_pcr$CI_95, pooled_efs$CI_95, pooled_os$CI_95),
  p = c(format(as.numeric(pooled_pcr$P_value), digits = 4), pooled_efs$P_value, pooled_os$P_value),
  I2 = c("0%", "0%", "62.3%"),
  NNT = c("7", "11", "11"),
  stringsAsFactors = FALSE
) |>
  gt() |>
  tab_header(title = "Table 2. Efficacy Outcomes Summary") |>
  cols_label(CI_95 = "95% CI", I2 = md("I\u00b2")) |>
  tab_options(
    table.font.size = px(12),
    data_row.padding = px(6),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  tab_style(style = cell_text(weight = "bold"), locations = cells_body(columns = Outcome)) |>
  tab_source_note("Random-effects meta-analysis with Hartung-Knapp adjustment. NNT = number needed to treat.")

gtsave(tbl2, file.path(out_dir, "table2_efficacy.png"), vwidth = 1000, vheight = 400, zoom = 2)

cat("Rendering Table 3...\n")
tbl3 <- data.frame(
  Outcome = c("Serious AE", "Grade 3+ irAE", "Discontinuation", "Fatal AE"),
  Trials = c("2 (N=774)", "1 (N=1174)", "1 (N=1174)", "2 (N=1615)"),
  ICI = c("114/387 (29.5%)", "102/784 (13.0%)", "216/784 (27.6%)", "4/1006 (0.40%)"),
  Control = c("76/387 (19.6%)", "6/390 (1.5%)", "55/390 (14.1%)", "0/609 (0%)"),
  RR = c("1.50", "8.5*", "1.96*", "---"),
  CI_95 = c("1.13-1.98", "---", "---", "---"),
  p = c("0.034", "---", "---", "---"),
  NNH = c("10", "9", "7", "250"),
  stringsAsFactors = FALSE
) |>
  gt() |>
  tab_header(title = "Table 3. Safety Outcomes Summary") |>
  cols_label(CI_95 = "95% CI") |>
  tab_options(
    table.font.size = px(12),
    data_row.padding = px(6),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  tab_style(style = cell_text(weight = "bold"), locations = cells_body(columns = Outcome)) |>
  tab_source_note("irAE = immune-related adverse event; NNH = number needed to harm. *Single-trial estimate.")

gtsave(tbl3, file.path(out_dir, "table3_safety.png"), vwidth = 900, vheight = 400, zoom = 2)

cat("Rendering Supplementary Table: Individual pCR...\n")
tbl_pcr <- pcr_results |>
  gt() |>
  tab_header(title = "Supplementary Table 1. Individual Trial pCR Results") |>
  cols_label(CI_95 = "95% CI", P_value = "p-value", N_Total = "N") |>
  tab_options(
    table.font.size = px(12),
    data_row.padding = px(6),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  tab_style(
    style = cell_text(weight = "bold"),
    locations = cells_body(columns = Trial, rows = grepl("POOLED", Trial))
  ) |>
  tab_source_note("Random-effects meta-analysis (Mantel-Haenszel). RR = risk ratio.")

gtsave(tbl_pcr, file.path(out_dir, "supptable1_pcr.png"), vwidth = 1000, vheight = 500, zoom = 2)

cat("Rendering Supplementary Table: EFS...\n")
tbl_efs <- efs_results |>
  select(-any_of("ICI_Agent")) |>
  gt() |>
  tab_header(title = "Supplementary Table 2. Event-Free Survival Results") |>
  cols_label(
    CI_95 = "95% CI", P_value = "p-value", First_Author = "Author",
    N_Total = "N", N_ICI = "N(ICI)", N_Control = "N(Ctrl)",
    EFS_5yr_ICI_pct = "EFS 5yr ICI", EFS_5yr_Control_pct = "EFS 5yr Ctrl",
    Followup_months = "F/U (mo)"
  ) |>
  tab_options(
    table.font.size = px(12),
    data_row.padding = px(6),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  tab_style(
    style = cell_text(weight = "bold"),
    locations = cells_body(columns = Trial, rows = grepl("Pooled", Trial))
  ) |>
  tab_source_note("HR = hazard ratio; EFS = event-free survival. NR = not reported.")

gtsave(tbl_efs, file.path(out_dir, "supptable2_efs.png"), vwidth = 1100, vheight = 400, zoom = 2)

cat("Rendering Supplementary Table: OS...\n")
tbl_os <- os_results |>
  select(-any_of("ICI_Agent")) |>
  gt() |>
  tab_header(title = "Supplementary Table 3. Overall Survival Results") |>
  cols_label(
    CI_95 = "95% CI", P_value = "p-value", First_Author = "Author",
    N_Total = "N", N_ICI = "N(ICI)", N_Control = "N(Ctrl)",
    OS_5yr_ICI_pct = "OS 5yr ICI", OS_5yr_Control_pct = "OS 5yr Ctrl",
    Followup_months = "F/U (mo)"
  ) |>
  tab_options(
    table.font.size = px(12),
    data_row.padding = px(6),
    column_labels.font.weight = "bold",
    heading.title.font.size = px(14),
    heading.title.font.weight = "bold"
  ) |>
  tab_style(
    style = cell_text(weight = "bold"),
    locations = cells_body(columns = Trial, rows = grepl("Pooled", Trial))
  ) |>
  tab_source_note("HR = hazard ratio; OS = overall survival. Wide CI reflects Hartung-Knapp with k=2.")

gtsave(tbl_os, file.path(out_dir, "supptable3_os.png"), vwidth = 1100, vheight = 350, zoom = 2)

cat("\nAll tables saved to:", out_dir, "\n")
list.files(out_dir, pattern = "\\.png$")
