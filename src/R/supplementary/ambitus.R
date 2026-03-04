
library(readr)
library(readr)
library(dplyr)

df_ambitus <- read_csv("data/df_ambitus.csv") |>
  mutate(
    max_transposition = pmin(7, 108 - max_note),
    min_transposition = pmax(-7, 0 - min_note),
    safe = (max_transposition == 7) & (min_transposition == -7)
  )

print(df_ambitus |> filter(!safe), n = 72)
