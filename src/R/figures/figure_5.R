# src/R/figures/figure_5.R
# Figure 5: A comparison of VBV from this study to Swierczek & Schutz (2025). Points correspond to the mean of all 24 Bach preludes (plotted with 95% bootstrap confidence intervals, r = 10,000). Albums uses 17 versions, Dynamics use 40 versions, Tempo use 50 versions, and pitch use 14 versions, as described in the methods of this study.

# =========================================================================== #
# Setup.
library(tibble)
library(dplyr)
library(tidyr)
library(ggplot2)
library(MAPLEemo)
library(boot)
library(forcats)
source("src/R/plotters.R")

# =========================================================================== #
# Read in VBV data from Swierczek & Schutz, 2025.
df_vbv <- readRDS("data/df_vbv.RDS") |>
  tibble() |>
  mutate(
    transformation = "Albums"
  )

# Calculate VBV from this dataset.
df_fig5a <- df_diff |>
  filter(
    setCode == "bach-1" # Use only Bach for "apples to apples" comparison.
  ) |>
  group_by(feature, transformation, tool) |>
  relative_variation(
    piece,
    value
  ) |>
  group_by(feature, transformation, tool) |>
  summarize(
    mean = mean(ratio),
    boot = boot.ci(
      boot(
        ratio,
        mean_func,
        R = 10000
      ),
      type = "bca"
    )$bca
  )

# Join the two datasets.
df_fig5b <- bind_rows(
    df_vbv,
    df_fig5a
  ) |>
  mutate(
    transformation = fct_relevel(
      transformation,
      "Albums",
      "Dynamics",
      "Tempo",
      "Pitch"
    ),
    study = case_when(
      transformation == "Albums" ~ "Open",
      .default = "Closed"
    )
  )

df_fig5b |>
  group_by(feature, tool) |>
  mutate(
    albums_mean = mean[transformation == "Albums"],
    pct_of_albums = (mean / albums_mean) * 100
  ) |>
  ungroup() |>
  filter(transformation != "Albums") |>
  select(feature, tool, transformation, pct_of_albums) |> filter(transformation == "Dynamics")

# Plot.
df_fig5b |>
  ggplot(
    aes(
      x = tool,
      y = mean,
      colour = tool,
      shape = study
    )
  ) +
  geom_errorbar(
    aes(
      ymin = boot[, 4],
      ymax = boot[, 5]
    ),
    width = 0.2,
    position = position_dodge(0.9)
  )  +
  geom_point(
    size = 3,
    fill = "white"
  ) +
  facet_grid(
    feature ~ transformation
  ) +
  labs(
    y = "Variation Between Versions (VBV)",
    colour = "Tool"
  ) +
  scale_colour_manual(values = tool_cols) +
  scale_shape_manual(
    values = c(
      16,
      21
    )
  ) +
  guides(
    shape = "none"
  ) +
  theme_maple() +
  theme(
    legend.position = "bottom",
    axis.title.x = element_blank(),
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank()
  )

ggsave(
  "img/figure_5.png",
  height = 4,
  width = 8.5
)

# =========================================================================== #
