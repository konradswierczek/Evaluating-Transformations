# src/R/inference.R

# =========================================================================== #
# Setup.
library(purrr)
library(dplyr)
library(coin)
library(rcompanion)
library(tidyr)
library(irr)
library(tibble)

SEED <- 1618
set.seed(SEED)

N_RESAMPLE <- 10000

OUT_RDATA <- "data/inference.RData"
OUT_SUMMARY <- "data/inference_summary.txt"

# =========================================================================== #
# Data preparation.
df_test <- df_diff |>
  group_by(feature, tool) |>
  mutate(
    rdb = abs(value - value_baseline) / sd(value_baseline)
  ) |>
  filter(level != 0) |>
  group_by(setCode, pieceID, transformation, tool, feature) |>
  summarize(rdb = mean(rdb), .groups = "drop") |>
  mutate(
    transformation = as.factor(transformation),
    tool  = as.factor(tool)
  )

df_test$interaction <- interaction(df_test$tool, df_test$transformation)

# =========================================================================== #
# Run one oneway_test with a fixed seed.
run_oneway <- function(formula, data) {
  set.seed(SEED)
  oneway_test(
    formula,
    data = data,
    distribution = approximate(nresample = N_RESAMPLE)
  )
}

run_independence <- function(formula, data) {
  set.seed(SEED)
  independence_test(
    formula,
    data = data,
    distribution = approximate(nresample = N_RESAMPLE)
  )
}

run_pairwise <- function(formula, data) {
  set.seed(SEED)
  pairwisePermutationTest(
    formula,
    data = data,
    distribution = approximate(nresample = N_RESAMPLE),
    method = "holm"
  )
}

df_mode <- df_test |> filter(feature == "Relative Mode")
df_onsets <- df_test |> filter(feature == "Onsets (#)")

# =========================================================================== #
# Main effect of tool (stratified by transformation).
test_tool_mode   <- run_oneway(
  rdb ~ tool | transformation,
  df_mode
)
test_tool_onsets <- run_oneway(
  rdb ~ tool | transformation,
  df_onsets
)

# Main effect of transformation (stratified by tool).
test_transformation_mode   <- run_oneway(
  rdb ~ transformation | tool,
  df_mode
)
test_transformation_onsets <- run_oneway(
  rdb ~ transformation | tool,
  df_onsets
)

# =========================================================================== #
# Interaction tests (residuals from additive LM)
lm_additive_mode <- lm(
  rdb ~ tool + transformation,
  data = df_mode
)
resid_additive_mode <- residuals(lm_additive_mode)
test_interaction_mode <- run_independence(
  resid_additive_mode ~ interaction,
  data = df_mode
)

lm_additive_onsets <- lm(
  rdb ~ tool + transformation,
  data = df_onsets
)
resid_additive_onsets <- residuals(lm_additive_onsets)
test_interaction_onsets <- run_independence(
  resid_additive_onsets ~ interaction,
  data = df_onsets
)

# =========================================================================== #
# Pairwise post-hoc tests (Holm correction).
pairwise_tool_mode <- run_pairwise(
  rdb ~ tool | transformation,
  df_mode
)
pairwise_transformation_mode <- run_pairwise(
  rdb ~ transformation | tool,
  df_mode
)
pairwise_tool_onsets <- run_pairwise(
  rdb ~ tool | transformation,
  df_onsets
)
pairwise_transformation_onsets <- run_pairwise(
  rdb ~ transformation | tool,
  df_onsets
)

# =========================================================================== #
# Save all result objects to .RData.
pairwise_results <- list(
  tool_mode = pairwise_tool_mode,
  transformation_mode = pairwise_transformation_mode,
  tool_onsets = pairwise_tool_onsets,
  transformation_onsets = pairwise_transformation_onsets
)

save(
  SEED, N_RESAMPLE,
  df_test,
  test_tool_mode,
  test_tool_onsets,
  test_transformation_mode,
  test_transformation_onsets,
  lm_additive_mode,
  lm_additive_onsets,
  test_interaction_mode,
  test_interaction_onsets,
  pairwise_results,
  file = OUT_RDATA
)

# =========================================================================== #
# Plain-text summary.
cap <- function(x) capture.output(print(x))

summary_lines <- c(
  "=============================================================",
  "  INFERENCE SUMMARY",
  sprintf("  Seed: %d | Resamples: %d", SEED, N_RESAMPLE),
  sprintf("  Generated: %s", format(Sys.time(), "%Y-%m-%d %H:%M:%S %Z")),
  "=============================================================",
  "",
  "-------------------------------------------------------------",
  "  FEATURE: Relative Mode",
  "-------------------------------------------------------------",
  "",
  "  [Omnibus] Tool effect (stratified by transformation)",
  cap(test_tool_mode),
  "",
  "  [Omnibus] Transformation effect (stratified by tool)",
  cap(test_transformation_mode),
  "",
  "  [Interaction] Tool × Transformation (residual independence test)",
  cap(test_interaction_mode),
  "",
  "  [Post-hoc] Pairwise tool comparisons (Holm-corrected)",
  cap(pairwise_tool_mode),
  "",
  "  [Post-hoc] Pairwise transformation comparisons (Holm-corrected)",
  cap(pairwise_transformation_mode),
  "",
  "-------------------------------------------------------------",
  "  FEATURE: Onsets (#)",
  "-------------------------------------------------------------",
  "",
  "  [Omnibus] Tool effect (stratified by transformation)",
  cap(test_tool_onsets),
  "",
  "  [Omnibus] Transformation effect (stratified by tool)",
  cap(test_transformation_onsets),
  "",
  "  [Interaction] Tool × Transformation (residual independence test)",
  cap(test_interaction_onsets),
  "",
  "  [Post-hoc] Pairwise tool comparisons (Holm-corrected)",
  cap(pairwise_tool_onsets),
  "",
  "  [Post-hoc] Pairwise transformation comparisons (Holm-corrected)",
  cap(pairwise_transformation_onsets),
  "",
  "============================================================="
)

writeLines(summary_lines, OUT_SUMMARY)
