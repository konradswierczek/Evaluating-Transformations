library(DBI)
library(RSQLite)
library(tibble)
library(readr)
library(jsonlite)
library(dplyr)
library(purrr)
library(tidyr)
library(stringr)
library(forcats)

con <- dbConnect(SQLite(), "data/data.db")
df_features <- dbReadTable(con, "features") |>
  tibble()
df_logs <- dbReadTable(con, "logs") |>
  tibble()
df_files <- dbReadTable(con, "files") |>
  tibble() |>
  mutate(extra_parsed = map(extra, fromJSON)) |>
  unnest_wider(extra_parsed) |>
  unnest_wider(midi_file, names_sep = "_") |>
  unnest_wider(transformation_vector, names_sep = "_")
df_extractors <- dbReadTable(con, "extractors") |>
  tibble()
dbDisconnect(con)
df_set_metadata <- read_csv("data/df_set_metadata.csv")
df_piece_metadata <- read_csv("data/df_piece_metadata.csv")

df_raw <- df_features |>
  left_join(
    df_extractors,
    by = join_by(extractor_uid == uid)
  ) |>
  left_join(
    df_files,
    by = join_by(file_uid == uid)
  ) |>
  select(
    value, feature, tool, midi_file_file_name, transformation_vector_velocity, transformation_vector_transposition, transformation_vector_tempo_ratio
  ) |>
  mutate(
    value = as.numeric(value)
  )
  # FILTER THE PITCH HEIGHT THAT BREAKS

df_tidy <- df_raw |>
  separate_wider_delim(
    midi_file_file_name,
    delim = "_",
    names = c("composer", "set", NA, "chroma", "mode", NA)
  ) |>
  mutate(
    setCode = paste0(tolower(composer), "-", set),
    pieceID = paste0(substr(mode, start = 1, stop = 1), chroma)
  ) |>
  select(-composer, -set, -chroma, -mode) |>
  mutate(
    tool = case_when(
      tool == "mirtoolbox" ~ "MIRtoolbox",
      .default = str_to_title(tool)
    ),
    feature = case_when(
      feature == "relative_mode" ~ "Relative Mode",
      feature == "onset_detection" ~ "Onsets (#)"
    )
  ) |>
  rename_with(~ gsub("^transformation_vector_", "", .x)) |>
  rename(
    "Dynamics" = "velocity",
    "Pitch" = "transposition",
    "Tempo" = "tempo_ratio"
  ) |>
  left_join(
    df_piece_metadata |>
      select(setCode, pieceID, pieceNumber, keyName, mode),
    by = c("setCode", "pieceID")
  ) |>
  left_join(
    df_set_metadata |>
      select(setCode, title, opus, fullName),
    by = "setCode"
  ) |>
  mutate(
    piece = paste(keyName, mode)
  ) |>
  select(-keyName, -mode)

df_baseline <- df_tidy |>
  filter(
    Pitch == 0,
    Tempo == 1,
    Dynamics == 64
  ) |>
  rename(value_baseline = value) |>
  select(-Dynamics, -Pitch, -Tempo) |>
  filter(!is.na(value_baseline)) # TEMPORARY

df_diff <- df_tidy |>
  group_by(feature, tool, setCode, pieceID, pieceNumber, title, opus, fullName, piece) |>
  left_join(
    df_baseline
  ) |>
  mutate(
    Dynamics = Dynamics - 64,
    Tempo = (Tempo - 1) * 100
  ) |>
  pivot_longer(
    cols = c(Dynamics, Pitch, Tempo),
    names_to = "transformation",
    values_to = "level"
  ) |>
  group_by(across(-c(transformation, level))) |>
  filter(
    level != 0 | all(level == 0)
  ) |>
  ungroup() |>
  mutate(diff_rel = value - value_baseline) |>
  mutate(transformation = fct_relevel(
    transformation,
    "Dynamics",
    "Tempo",
    "Pitch"
  )) |>
  filter(!is.na(value_baseline)) # TEMPORARY
