library(meta)

if (!dir.exists("figures")) {
  dir.create("figures", recursive = TRUE)
}
if (!dir.exists("tables")) {
  dir.create("tables", recursive = TRUE)
}

lines <- c("# Influence Diagnostics")

if (exists("cont_model")) {
  lines <- c(lines, "\n## Continuous outcomes")
  inf <- tryCatch(metainf(cont_model), error = function(e) NULL)
  if (!is.null(inf)) {
    lines <- c(lines, capture.output(summary(inf)))
    png("figures/influence_continuous.png", width = 2400, height = 1800, res = 300)
    try(plot(inf), silent = TRUE)
    dev.off()
  }

  png("figures/baujat_continuous.png", width = 2400, height = 1800, res = 300)
  try(baujat(cont_model), silent = TRUE)
  dev.off()
}

if (exists("bin_model")) {
  lines <- c(lines, "\n## Binary outcomes")
  inf <- tryCatch(metainf(bin_model), error = function(e) NULL)
  if (!is.null(inf)) {
    lines <- c(lines, capture.output(summary(inf)))
    png("figures/influence_binary.png", width = 2400, height = 1800, res = 300)
    try(plot(inf), silent = TRUE)
    dev.off()
  }

  png("figures/baujat_binary.png", width = 2400, height = 1800, res = 300)
  try(baujat(bin_model), silent = TRUE)
  dev.off()
}

writeLines(lines, con = "tables/influence_summary.txt")
