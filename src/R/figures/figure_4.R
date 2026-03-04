# src/R/figures/figure_4.R
# Figure 4: A comparison of the extracted values from the most and least extreme RDB preludes for two combinations of feature, tool, and transformation. A shows the the effect of T~pitch~ on relative mode extracted by Essentia, and B shows the effect of T~tempo~ on onset detection performed by Essentia. Horizontal lines and filled dots correspond to the untransformed, or baseline audio file. Each unfilled dot represents a specific value of the transformation, with the x axis representing the level of that transformation. Vertical lines are proportional to the degree of deviation from the baseline value.

# =========================================================================== #
library(ggplot2)
library(MAPLEemo)
library(patchwork)
source("src/R/plotters.R")

# =========================================================================== #

lims_pitch <- df_diff |>
  filter(feature == "Relative Mode", transformation == "Pitch") |>
  summarise(lo = min(value, value_baseline), hi = max(value, value_baseline)) |>
  unlist()

lims_tempo <- df_diff |>
  filter(feature == "Onsets (#)", transformation == "Tempo") |>
  summarise(lo = min(value, value_baseline), hi = max(value, value_baseline)) |>
  unlist()

(
  plot_one_piece("Essentia", "Relative Mode", "Pitch", "M4",  "bach-1",   lims_pitch) +
  plot_one_piece("Essentia", "Relative Mode", "Pitch", "M2",  "chopin-1", lims_pitch) +
  plot_layout(axis_titles = "collect")
) /
(
  plot_one_piece("Essentia", "Onsets (#)", "Tempo", "M10", "bach-1", lims_tempo) +
  plot_one_piece("Essentia", "Onsets (#)", "Tempo", "M0",  "bach-1", lims_tempo) +
  plot_layout(axis_titles = "collect")
) +
plot_annotation(tag_levels = list(c("A", "", "B", "")))

ggsave(
  "img/figure_4.png",
  width = 10,
  height = 10
)

# =========================================================================== #
