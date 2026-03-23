library(ggplot2)
library(dplyr)
library(forcats)
library(patchwork)

df_plot <- df_diff |>
  group_by(feature, tool, transformation) |>
  mutate(
    rdb = abs(value - value_baseline) / sd(value_baseline)
  ) |>
  filter(level != 0) |>
  filter(
    (feature == "Relative Mode" & transformation == "Pitch") |
    (feature == "Onsets (#)" & transformation == "Tempo")
  ) |>
  group_by(
    pieceID, setCode, feature, transformation
  ) |>
  summarize(
    mean_rdb = mean(rdb),
    .groups = "drop"
  ) |>
  left_join(
    df_set_metadata,
    by = "setCode"
  ) |>
  left_join(
    df_piece_metadata,
    by = c("pieceID", "setCode")
  ) |>
  mutate(
    piece = paste(composer, keyName, mode)
  )

df_fig4_mode <- df_plot |>
  filter(
    feature == "Relative Mode",
    transformation == "Pitch"
  ) |>
  mutate(piece = fct_reorder(piece, mean_rdb))

df_fig4_onsets <- df_plot |>
  filter(
    feature == "Onsets (#)",
    transformation == "Tempo"
  ) |>
  mutate(piece = fct_reorder(piece, mean_rdb))

fig4_p1 <- ggplot(
  df_fig4_mode,
  aes(
    x = mean_rdb,
    y = piece
  )
) +
  geom_point() +
  labs(
    title = expression("Relative Mode - " ~ T[pitch]),
    x = "Mean RDB",
    y = NULL
  ) +
  theme_maple()

fig4_p2 <- ggplot(
  df_fig4_onsets,
  aes(
    x = mean_rdb,
    y = piece
  )
) +
  geom_point() +
  labs(
    title = expression("Onsets (#) - " ~ T[tempo]),
    x = "Mean RDB",
    y = NULL
  ) +
  theme_maple()

fig4 <- fig4_p1 +
  fig4_p2 +
  plot_layout(
    axes = "collect",
    guides = "collect"
  ) &
  theme(legend.position = "bottom")

ggsave(
  "img/figure_s1.png",
  fig4,
  width = 8.5,
  height = 11
)
