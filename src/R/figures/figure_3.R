# src/R/figures/figure_3.R
# Figure 3: Mean RDB for each combination of tool, feature, and transformation. Each gray point corresponds to the value of one prelude across all levels of a given transformation. Gray dots are jittered on the x axis without any specific order. Coloured dots indicate the grand mean of all 72 preludes (plotted with 95% bootstrap confidence intervals, r = 10,000).

# =========================================================================== #
# Setup.
library(ggplot2)
library(dplyr)
library(ggsignif)
library(tidyr)
library(MAPLEemo)
source("src/R/plotters.R")
SEED = 1618
set.seed(SEED)

# =========================================================================== #
# Calculate RDB..
df_fig3a <- df_diff |>
  group_by(
    feature, tool, transformation
  ) |>
  mutate(
    rdb = abs(value - value_baseline) / sd(value_baseline)
  ) |>
  filter(
    level != 0
  )

# Calculate mean RDM for each combination of transformation, feature, and tool.
df_fig3b <- df_fig3a |>
  group_by(
    transformation, feature, tool
  ) |>
  summarize(
    ci = list(boot_mean_ci(rdb, seed = set.seed(SEED))),
    .groups = "drop"
  ) |>
  unnest_wider(ci)

# Calculate mean RDB for each piece within each combination of transformation, feature, and tool.
df_fig3c <- df_fig3a |>
  group_by(transformation, feature, tool, pieceID, setCode) |>
  summarize(
    mean = mean(rdb),
    .groups = "drop"
  )

# Plot.
df_fig3b |>
  ggplot(
    aes(
      x = transformation,
      y = mean,
      color = tool
    )
  ) +
  geom_point(
    data = df_fig3c,
    aes(
      x = transformation,
      y = mean
    ),
    inherit.aes = FALSE,
    color = "gray70",
    alpha = 0.6,
    shape = 20,
    position = position_jitter(
      width = 0.25,
      height = 0
    )
  ) +
  geom_point(size = 2) +
  geom_errorbar(
    aes(
      ymin = lower,
      ymax = upper
    ),
    width = 0.2
  ) +
  facet_grid(
    feature ~ tool,
    scales = "free_y"
  ) +
  labs(
    x = "Transformation",
    y = "Mean Relative Deviation from Baseline"
  ) +
  lims(
    y = c(0, 3.25)
  ) +
  scale_colour_manual(values = colours_tool) +
  theme_maple() +
  theme(
    legend.position = "none",
    axis.text.x = element_text(angle = 30, hjust = 1),
    plot.caption = element_text(hjust = 0)
  )

ggsave(
  width = 9,
  height = 6,
  filename = "img/figure_3.png"
)

# =========================================================================== #
