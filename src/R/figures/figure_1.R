# src/R/figures/figure_1.R
# Figure 1: One MIDI file transformed by T~tempo~ analyzed by two onset detection algorithms (A and B). Horizontal lines and filled dots correspond to the untransformed, or baseline audio file. Each unfilled dot represents a specific value of the transformation, with the x axis representing the level, or magnitude of that transformation. Vertical lines are proportional to the degree of deviation from the baseline value.

# =========================================================================== #
# Setup.
library(dplyr)
library(ggplot2)
library(MAPLEemo)
library(patchwork)

# =========================================================================== #
# Filter data.
df_fig1a <- df_diff |>
  filter(
    feature == "Onsets (#)",
    transformation == "Tempo",
    tool == "Essentia",
    pieceID == "M10",
    setCode == "bach-1"
  )

df_fig1b <- df_diff |>
  filter(
    feature == "Onsets (#)",
    transformation == "Tempo",
    tool == "Librosa",
    pieceID == "M10",
    setCode == "bach-1"
  )

# Fixed y axis limits.
fig1_ylims <- range(c(df_fig1a$value, df_fig1b$value))

# Generate plots.
list(
  list(
    data = df_fig1a,
    title = "A"
  ),
  list(
    data = df_fig1b,
    title = "B"
  )
) |>
  map(\(x) {
    x$data |>
      ggplot(
        aes(
          x = level,
          y = value, 
          yend = value_baseline
        )
      ) +
      # Baseline value horizontal line.
      geom_hline(
        aes(yintercept = value_baseline),
        colour = "darkgray"
      ) +
      # Line from baseline value to individual levels.
      geom_segment(colour = "lightgray") +
      # Level point.
      geom_point(
        shape = 21,
        fill = "white"
      ) +
      # Baseline point.
      geom_point(
        aes(y = value_baseline),
        x = 0,
        shape = 21,
        fill = "black"
      ) +
      labs(
        x = "Tempo",
        y = "Number of Onsets Detected",
        title = x$title
      ) +
      lims(y = fig1_ylims) +
      scale_x_continuous(
        breaks = c(
          -20,
          20
        ),
        labels = c(
          "Slower",
          "Faster"
        )
      ) +
      theme_maple() +
      theme(
        legend.position = "none",
        axis.ticks.x = element_blank()
      )
  }) |>
  wrap_plots(
    ncol = 2,
    axes = "collect"
  )

ggsave(
  filename = "img/figure_1.png",
  width = 10,
  height = 5
)

# =========================================================================== #
