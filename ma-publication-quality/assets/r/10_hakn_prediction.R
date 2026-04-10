library(meta)

# This script assumes cont_model/bin_model exist (from 03_models.R)
# It writes summary outputs to tables/.

if (!dir.exists("tables")) {
  dir.create("tables", recursive = TRUE)
}

lines <- c("# Hartung-Knapp and Prediction Intervals")

if (exists("cont_model")) {
  cont_model_hakn <- update.meta(cont_model, hakn = TRUE)
  lines <- c(lines, "\n## Continuous outcomes (HK)")
  lines <- c(lines, capture.output(summary(cont_model_hakn)))

  pred <- tryCatch(predict(cont_model_hakn), error = function(e) NULL)
  if (!is.null(pred)) {
    pred_df <- data.frame(
      outcome = "continuous",
      estimate = pred$TE,
      se = pred$seTE,
      ci_low = pred$lower,
      ci_high = pred$upper,
      pi_low = pred$lower.predict,
      pi_high = pred$upper.predict
    )
    write.csv(pred_df, file = "tables/prediction_intervals.csv", row.names = FALSE)
  }
}

if (exists("bin_model")) {
  bin_model_hakn <- update.meta(bin_model, hakn = TRUE)
  lines <- c(lines, "\n## Binary outcomes (HK)")
  lines <- c(lines, capture.output(summary(bin_model_hakn)))

  pred <- tryCatch(predict(bin_model_hakn), error = function(e) NULL)
  if (!is.null(pred)) {
    pred_df <- data.frame(
      outcome = "binary",
      estimate = pred$TE,
      se = pred$seTE,
      ci_low = pred$lower,
      ci_high = pred$upper,
      pi_low = pred$lower.predict,
      pi_high = pred$upper.predict
    )
    if (file.exists("tables/prediction_intervals.csv")) {
      pred_df <- rbind(read.csv("tables/prediction_intervals.csv"), pred_df)
    }
    write.csv(pred_df, file = "tables/prediction_intervals.csv", row.names = FALSE)
  }
}

writeLines(lines, con = "tables/hakn_summary.txt")
