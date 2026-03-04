library(DBI)
library(RSQLite)
library(dplyr)
library(jsonlite)
library(tidyr)
library(stringr)

con <- dbConnect(SQLite(), "data/data.db")
df_logs <- dbReadTable(con, "logs")
dbDisconnect(con)

df_logs <- df_logs |>
  filter(!is.na(exception)) |>
  tibble() |>
  rowwise() |>
  mutate(
    context_parsed = list(fromJSON(context)),
    error_type = str_extract(exception, "[a-zA-Z0-9_.]+Error"),
    error_message = str_extract(exception, "(?<=: ).*$")
  ) |>
  unnest_wider(context_parsed)
