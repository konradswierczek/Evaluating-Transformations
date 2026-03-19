# src/R/figures/figure_4.R
# Figure 4: A comparison of the extracted values from four preludes for two combinations of feature, tool, and transformation. A shows the the effect of T~pitch~ on relative mode extracted by Essentia, and B shows the effect of T~tempo~ on onset detection performed by Essentia. Horizontal lines and filled dots correspond to the untransformed, or baseline audio file. Each unfilled dot represents a specific value of the transformation, with the x axis representing the level of that transformation. Vertical lines are proportional to the degree of deviation from the baseline value.

# =========================================================================== #
library(ggplot2)
library(MAPLEemo)
library(patchwork)
library(dplyr)

# =========================================================================== #

slide_constant <- 0.25

plot_one_piece <- function(f, tf, p, s, ylims = NULL) {
    df <- df_diff |>
      filter(
        feature == f,
        transformation == tf,
        pieceID == p,
        setCode == s,
        level != 0
      ) |>
      mutate(
        level = case_when(
          tool == "Librosa" ~ level - slide_constant,
          tool == "Essentia" ~ level + slide_constant,
          .default = level 
        )
      )
    
    full_name <- df$fullName[1]
    piece <- df$piece[1]
    
    df |>
      ggplot(
        aes(
          x = level,
          y = value,
          colour = tool
        )
      ) +
      geom_hline(
        aes(
          yintercept = value_baseline,
          colour = tool
        ),
        alpha = 0.2
      ) +
      geom_segment(
        aes(
          y = value_baseline,
          yend = value
        ),
        linetype = 1,
        alpha = 0.35
      ) +
      geom_point(
        aes(y = value_baseline),
        x = 0,
        fill = "white",
        shape = 16
      ) +
      geom_point(
        fill = "white",
        shape = 21
      ) +
      labs(
        x = paste0(
          "Transformation Level (",
          tf,
          ")"
        ),
        y = f,
        colour = "Tool",
        title = paste(
          tail(strsplit(full_name, " ")[[1]], 1),
          piece
        )
      ) +
      { if (!is.null(ylims)) lims(y = ylims) } +
      scale_colour_manual(values = colours_tool) +
      theme_maple() +
      theme(legend.position = "bottom")
}

df_fig4 <- df_diff |>
  group_by(
    feature, tool, transformation
  ) |>
  mutate(
    rdb = abs(value - value_baseline) / sd(value_baseline)
  ) |>
  filter(
    level != 0
  ) |>
  filter(
    (feature == "Relative Mode" & transformation == "Pitch") |
    (feature == "Onsets (#)" & transformation == "Tempo")
  ) |>
  group_by(pieceID, setCode, feature, tool, transformation) |>
  summarize(mean_rdb = mean(rdb)) |>
  group_by(feature, transformation) |>
  arrange(mean_rdb, .by_group = TRUE) |>
  slice(round(seq(1, n(), length.out = 4))) |>
  ungroup()


lims_pitch <- df_diff |>
  filter(feature == "Relative Mode", transformation == "Pitch") |>
  summarise(lo = min(value, value_baseline), hi = max(value, value_baseline)) |>
  unlist()

lims_tempo <- df_diff |>
  filter(feature == "Onsets (#)", transformation == "Tempo") |>
  summarise(lo = min(value, value_baseline), hi = max(value, value_baseline)) |>
  unlist()

plots_pitch <- df_fig4 |>
  filter(feature == "Relative Mode", transformation == "Pitch") |>
  arrange(mean_rdb) |>
  distinct(feature, transformation, pieceID, setCode, mean_rdb) |>
  mutate(
    plot = purrr::pmap(
      list(feature, transformation, pieceID, setCode),
      \(f, tf, p, s)
        plot_one_piece(f, tf, p, s, lims_pitch)
    )
  ) |>
  pull(plot)

plots_tempo <- df_fig4 |>
  filter(feature == "Onsets (#)", transformation == "Tempo") |>
  arrange(mean_rdb) |>
  distinct(feature, transformation, pieceID, setCode, mean_rdb) |>
  mutate(
    plot = purrr::pmap(
      list(feature, transformation, pieceID, setCode),
      \(f, tf, p, s)
        plot_one_piece(f, tf, p, s, lims_tempo)
    )
  ) |>
  pull(plot)

pitch_row <- wrap_plots(plots_pitch, nrow = 1) +
  plot_layout(axis_titles = "collect")

tempo_row <- wrap_plots(plots_tempo, nrow = 1) +
  plot_layout(axis_titles = "collect")

final_plot <-
  wrap_plots(
    pitch_row, tempo_row,
    ncol = 1
  ) +
  plot_layout(guides = "collect") +
  plot_annotation(tag_levels = list(c("A", "", "", "", "B", "", "", ""))) &
  theme(legend.position = "bottom")

ggsave(
  "img/figure_4.png",
  final_plot,
  width = 12,
  height = 6
)

# =========================================================================== #
