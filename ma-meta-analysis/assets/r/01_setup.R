# Initialize renv and load packages

if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv")
}
renv::init(bare = TRUE)

packages <- c(
  "dplyr",
  "readr",
  "tidyr",
  "ggplot2",
  "meta",
  "metafor",
  "gtsummary",
  "gt",
  "stringr"
)

for (pkg in packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    install.packages(pkg)
  }
}

renv::snapshot()
