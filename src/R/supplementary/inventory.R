library(DBI)
library(RSQLite)
library(jsonlite)
library(dplyr)
library(tidyr)
library(purrr)

con <- dbConnect(SQLite(), "data/data.db")
df_files <- dbReadTable(con, "files")
dbDisconnect(con)

df_files <- df_files |>
  tibble() |>
  mutate(extra_parsed = map(extra, fromJSON)) |>
  unnest_wider(extra_parsed) |>
  unnest_wider(midi_file, names_sep = "_") |>
  unnest_wider(transformation_vector, names_sep = "_")

library(ggplot2)

df_files |>
  ggplot(
    aes(
      x = transformation_vector_tempo_ratio,
      y = duration
    )
  ) +
  geom_point()

df_files |>
  count(midi_file_file_name) |>
  pull(n) |>
  unique() |>
  print()
