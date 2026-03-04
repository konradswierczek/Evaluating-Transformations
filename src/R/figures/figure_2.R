# src/R/figures/figure_2.R
# Figure 2: Mean SDB for each combination of tool, extracted feature, and transformation. Each point is the mean SDB across all 72 preludes at a given level of a transformation (plotted with 95% bootstrap confidence intervals, r = 10,000). Each level of the transformation is plotted in order from most extreme negative on the left (e.g., -7 semitones) to most extreme positive on the right (e.g., +7 semitones) with the baseline value in the center. Spearman's rho between level and mean deviation from baseline is included at the top of each cell (p < 0.001 = ***, p < 0.01 =** , p < 0.05 =* ).

# =========================================================================== #
# Setup.
library(ggplot2)
library(dplyr)
library(MAPLEemo)
source("src/R/plotters.R")
SEED = 1618
set.seed(SEED)

# =========================================================================== #
# Initialize plotting variables.
fig2_transformations <- c("Dynamics", "Tempo", "Pitch")
fig2_transformation_positions <- setNames(
  seq_along(fig2_transformations),
  fig2_transformations
)

# Mean Signed Difference from Baseline across all 72 preludes for each level.
df_fig2a <- df_diff |>
  filter(level != 0) |>
  group_by(
    transformation, feature, tool, level
  ) |>
  summarize(
    ci = list(boot_mean_ci(diff_rel)),
    .groups = "drop"
  ) |>
  unnest_wider(ci) |>
  mutate(transformation_num = fig2_transformation_positions[transformation])

# Calculate Spearman's rank correlation coefficient for each combination of feature, tool, and transformation.
df_rho <- df_diff |>
  group_by(feature, tool, transformation) |>
  summarise(
    cor_test = list(cor.test(level, diff_rel, method = "spearman")),
    .groups = "drop"
  ) |>
  mutate(
    rho = map_dbl(cor_test, "estimate"),
    p_value = map_dbl(cor_test, "p.value"),
    signif = case_when(
      p_value < 0.001 ~ "***",
      p_value < 0.01 ~ "**",
      p_value < 0.05 ~ "*",
      TRUE ~ ""
    )
  ) |>
  select(
    feature, tool, transformation, rho, p_value, signif
  ) |>
  # Map positions for figure.
  mutate(
    transformation_num = fig2_transformation_positions[transformation]
  )

# Map positions for rho indicators.
df_fig2b <- left_join(
  df_rho,
  df_fig2a|>
    group_by(feature) |>
    summarise(
      y_top = max(upper, na.rm = TRUE) * 1.05,
      .groups = "drop"
    ),
    by = "feature"
  )

# Plot.
ggplot() +
  geom_text(
    data = df_fig2b,
    aes(
      x = transformation_num,
      y = y_top * 0.7 ,
      label = paste0(sprintf("%.2f", rho), "\n", signif)
    ),
    color = "black",
    size = 3,
    fontface = "bold",
    vjust = 0
  ) +
  geom_hline(
    yintercept = 0,
    colour = "lightgray",
    linetype = "dashed"
  ) +
  geom_linerange(
    data = df_fig2a,
    aes(
      ymin = lower,
      ymax = upper,
      x = transformation_num + (level / max(abs(level))) * 0.4,
      y = mean,
      color = tool
    ),
    alpha = .25
  ) +
  geom_point(
    data = df_fig2a,
    aes(
      x = transformation_num + (level / max(abs(level))) * 0.4,
      y = mean,
      color = tool
    ),
    shape = 20,
    size = 1
  ) +
  facet_grid(
    feature ~ tool,
    scales = "free_y"
  ) +
  scale_x_continuous(
    breaks = seq_along(fig2_transformations),
    labels = fig2_transformations
  ) +
  scale_colour_manual(values = colours_tool) +
  labs(
    x = "Transformation",
    y = "Mean Signed Deviation from Baseline (72 Preludes)",
    colour = "Tool"
  ) +
  theme_maple() +
  theme(
    legend.position = "none",
    panel.grid = element_blank(),
    plot.caption = element_text(hjust = 0)
  )

ggsave(
  filename = "img/figure_2.png",
  width = 9,
  height = 6,
)

# =========================================================================== #
