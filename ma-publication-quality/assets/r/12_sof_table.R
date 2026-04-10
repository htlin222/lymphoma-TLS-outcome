library(readr)
library(dplyr)

if (!dir.exists("tables")) {
  dir.create("tables", recursive = TRUE)
}

sof_path <- "../08_reviews/grade_summary.csv"

if (file.exists(sof_path)) {
  sof <- read_csv(sof_path, show_col_types = FALSE)
  write_csv(sof, "tables/grade_summary.csv")

  if (requireNamespace("gt", quietly = TRUE)) {
    library(gt)
    gt_tbl <- gt(sof)
    gtsave(gt_tbl, "tables/grade_summary.html")
  } else {
    # Fallback: write markdown table
    writeLines(paste(capture.output(print(sof)), collapse = "\n"), con = "tables/grade_summary.txt")
  }
}
