# src/R/plotters.R

# =========================================================================== #
# Setup.
library(boot)

# =========================================================================== #
boot_mean_ci <- function(x, n_boot = 10000, conf = 0.95, seed = NULL) {

  if (!is.null(seed)) {
    old_seed <- .Random.seed
    on.exit(assign(".Random.seed", old_seed, envir = .GlobalEnv))
    set.seed(seed)
  }

  boot_fun <- function(data, indices) mean(data[indices], na.rm = TRUE)
  boot_res <- boot::boot(x, boot_fun, R = n_boot)
  ci <- boot::boot.ci(boot_res, type = "perc", conf = conf)

  c(
    mean  = mean(x, na.rm = TRUE),
    lower = ci$percent[4],
    upper = ci$percent[5]
  )
}

# =========================================================================== #
mean_func <- function(x, indices) {
  mean(x[indices])
}

# =========================================================================== #
plot_one_piece <- function(t, f, tf, p, s, ylims = NULL) {
    df <- df_diff |>
      filter(
        tool == t,
        feature == f,
        transformation == tf,
        pieceID == p,
        setCode == s
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
          yintercept = value_baseline
        ),
        colour = "gray"
      ) +
      geom_segment(
        aes(
          y = value_baseline,
          yend = value
        ),
        linetype = 1
      ) +
      geom_point(
        fill = "white",
        shape = 21
      ) +
      geom_point(
        aes(y = value_baseline),
        x = 0,
        fill = "white",
        shape = 16
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
      theme(legend.position = "none")
}

# =========================================================================== #
