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
