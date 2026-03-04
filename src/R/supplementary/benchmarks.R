library(DBI)
library(RSQLite)
library(dplyr)
library(lubridate)
library(tidyr)

con <- dbConnect(SQLite(), "data/data.db")
df_logs <- dbReadTable(con, "logs")
df_timing <- dbReadTable(con, "timing")
dbDisconnect(con)

df_task_durations <- df_logs |>
  tibble() |>
  filter(is.na(exception)) |>
  mutate(
    time = ymd_hms(gsub(",", ".", time)),
    task = gsub("Started |Finished ", "", message),
    status = ifelse(grepl("^Started", message), "start", "finish")
  ) |>
  group_by(task) |>
  arrange(task, time) |>
  mutate(pair_id = cumsum(status == "start")) |>
  ungroup() |>
  pivot_wider(
    id_cols = c(task, pair_id),
    names_from = status,
    values_from = time
  ) |>
  mutate(
    elapsed_seconds = as.numeric(difftime(finish, start, units = "secs")),
    elapsed_minutes = elapsed_seconds / 60
  ) |>
  select(task, start, finish, elapsed_seconds, elapsed_minutes)

print(df_task_durations)
