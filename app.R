# app.R
# ============================================================================ #
library(shiny)
library(dplyr)
library(ggplot2)
library(MAPLEemo)

source("src/R/read_data.R")

text_size <- 20
title <- "PAPER TITLE GOES HERE"

# ============================================================================ #
ui <- tagList(
  tags$head(
    tags$style(HTML("
      body {
        margin: 0;
        padding: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      }
      .full-width-header {
        width: 100%;
        height: 60px;
        line-height: 60px;
        background-color: #70747c;
        color: white;
        padding: 0 24px;
        display: flex;
        justify-content: flex-start;  /* <-- change here */
        align-items: center;
        box-sizing: border-box;
        gap: 16px; /* spacing between items */
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-weight: 500;
        font-size: 1rem;
      }
      .full-width-header h2 {
        margin: 0;
        font-family: inherit;
        font-weight: inherit;
      }
    ")),
    tags$title(title)
  ),
  div(
    class = "full-width-header",
    style = "gap: 16px;",  # spacing between items

    # Maple Lab logo
    a(
      href = "https://maplelab.net",
      target = "_blank",
      img(
        src = "https://maplelabs.info/wp-content/uploads/2018/05/final_head-darker-leaf-png-300x300.png",
        height = "50px",
        style = "display:block;"
      )
    ),

    h2(title, style = "margin: 0; font-size: 2.25rem; line-height: 60px; font-weight: 500;"),

    # GitHub icon
    a(
      href = "https://github.com/konradswierczek/evaluating-transformations",
      target = "_blank",
      img(
        src = "https://images.seeklogo.com/logo-png/30/2/github-logo-png_seeklogo-304612.png",
        height = "30px",
        style = "display:block;"
      )
    ),

    # Book icon (Bootstrap SVG)
    a(
      href = "",
      target = "_blank",
      img(
        src = "https://cdn.jsdelivr.net/npm/bootstrap-icons/icons/book.svg",
        height = "30px",
        style = "display:block;"
      )
    ),

    # Website icon (globe)
    a(
      href = "https://konradswierczek.ca",
      target = "_blank",
      img(
        src = "https://cdn.jsdelivr.net/npm/bootstrap-icons/icons/globe.svg",
        height = "30px",
        style = "display:block;"
      )
    )
  ),

  # Small spacer so content doesn't touch header
  tags$div(style = "height: 20px;"),

  # Main page content with normal Shiny layout
  fluidPage(
    sidebarLayout(
      sidebarPanel(
        width = 2,
        selectInput(
          "feature",
          "Select a Musical Property",
          choices = NULL
        ),
        selectInput(
          "tool",
          "Select an Analysis Tool",
          choices = NULL
        ),
        selectInput(
          "transformation",
          "Select a Transformation",
          choices = NULL
        ),
        selectInput(
          "metric",
          "Select a Deviation Metric",
          choices = c("RDB")
        ),
        wellPanel(
          h4("Information")
        )
      ),
      mainPanel(
        width = 10,
        fluidRow(
          column(
            width = 6,
            div(
              style = "aspect-ratio: 1 / 1; width: 100%;",
              plotOutput(
                "summary",
                width = "100%",
                height = "100%",
                click = clickOpts(id = "plot_click"),
                hover  = hoverOpts("plot_hover", delay = 100, delayType = "debounce")
              )
            )
          ),
          column(
            width = 6,
            div(
              style = "aspect-ratio: 1 / 1; width: 100%;",
              plotOutput(
                "piece",
                width = "100%",
                height = "100%"#,
                #click = clickOpts(id = "album_click")
              )
            )
          )
        ),
        uiOutput("hover_tooltip")
      )
    )
  )
)

# ============================================================================ #
server <- function(input, output, session) {
  updateSelectInput(
    session,
    "feature",
    choices = df_diff |>
      pull(feature) |>
      unique()
  )
  updateSelectInput(
    session,
    "tool",
    choices = df_diff |>
      pull(tool) |>
      unique()
  )
  updateSelectInput(
    session,
    "transformation",
    choices = df_diff |>
      pull(transformation) |>
      unique()
  )

  clicked_piece <- reactiveVal(
    tibble::tibble(
      pieceID = "M0",
      setCode = "bach-1"
    )
  )
  observeEvent(input$plot_click, {
    req(input$plot_click)
    df <- df_diff |>
      mutate(
        piece = paste(setCode, pieceID)
      )
    closest_point <- nearPoints(
      df,
      input$plot_click,
      xvar = "diff_rel",
      yvar = "piece",
      threshold = 50,
      maxpoints = 1
    )
    req(nrow(closest_point) == 1)
    clicked_piece(
      closest_point |>
        dplyr::select(pieceID, setCode) |>
        dplyr::slice(1)
    )
  })

hovered_piece <- reactiveVal(NULL)

observeEvent(input$plot_hover, {
  df <- df_diff |>
    mutate(piece = paste(setCode, pieceID))

  closest_point <- nearPoints(
    df,
    input$plot_hover,
    xvar      = "diff_rel",
    yvar      = "piece",
    threshold = 50,
    maxpoints = 1
  )

  if (nrow(closest_point) == 1) {
    hovered_piece(
      closest_point |>
        dplyr::select(pieceID, setCode) |>
        dplyr::slice(1)
    )
  } else {
    hovered_piece(NULL)   # clear when not hovering over a point
  }
})

# Render a floating tooltip near the cursor
output$hover_tooltip <- renderUI({
  req(input$plot_hover)
  hp <- hovered_piece()
  req(!is.null(hp))

  # Position tooltip near the cursor using CSS
  left_px <- input$plot_hover$coords_css$x + 12
  top_px  <- input$plot_hover$coords_css$y - 28

  style <- paste0(
    "position: absolute; ",
    "left: ", left_px, "px; ",
    "top: ", top_px, "px; ",
    "background: rgba(0,0,0,0.75); ",
    "color: white; ",
    "padding: 6px 10px; ",
    "border-radius: 4px; ",
    "font-size: 12px; ",
    "pointer-events: none; ",   # so tooltip doesn't block hover
    "z-index: 100;"
  )

  div(
    style = style,
    strong(hp$pieceID),
    br(),
    paste("Set:", hp$setCode)
    # Add any other fields from closest_point here
  )
})

  df_subset <- reactive({
    df_diff |>
      filter(
        feature == input$feature,
      ) |>
      mutate(
        piece = paste(setCode, pieceID)
      )
  })

  output$summary <- renderPlot({
    df_diff |>
      filter(
        tool == input$tool,
        feature == input$feature,
        transformation == input$transformation
      ) |>
      mutate(
        diff_rel = abs(value - value_baseline) / sd(value_baseline)
      ) |>
      group_by(setCode, pieceID) |>
      summarize(diff_rel = mean(diff_rel), .groups = "drop") |>
      arrange(diff_rel) |>
      mutate(
        piece = paste(setCode, pieceID),
        piece = factor(piece, levels = piece)
      ) |>
      ggplot(
        aes(
          y = piece,
          x = diff_rel
        )
      ) +
      geom_point(
        colour = colours_tool[input$tool]
      ) +
      labs(
        x = "Relative Deviation From Baseline",
        y = "Prelude (Rank Ordered)"

      ) +
      #scale_fill_manual(values = c("#d7191c", "#fdae61", "#2c7bb6")) +
      theme_maple() +
      theme(
        legend.position = "top",
        axis.text.y = element_blank(),
        axis.ticks.y = element_blank(),
        axis.title = element_text(size = text_size),
        axis.text = element_text(size = text_size * 0.8),
        plot.title = element_text(size = text_size)
      )
  })

  output$piece <- renderPlot({
    df_diff |>
      filter(
        tool == input$tool,
        feature == input$feature,
        transformation == input$transformation,
        pieceID == clicked_piece()$pieceID,
        setCode == clicked_piece()$setCode
      ) |>
      ggplot(
        aes(
          x = level,
          y = value,
          colour = tool
        )
      ) +
      geom_hline(
        aes(yintercept = value_baseline, colour = tool),
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
        shape = 21,
        size = 5
      ) +
      geom_point(
        aes(y = value_baseline),
        x = 0,
        fill = "white",
        shape = 16,
        size = 5
      ) +
      labs(
        x = "Transformation Level",
        y = input$feature,
        colour = "Tool",
        title = paste(
          clicked_piece()$setCode,
          clicked_piece()$pieceID
        )
      ) +
      lims(
        y = c(
          df_subset() |> pull(value) |> min(),
          df_subset() |> pull(value) |> max()
        )
      ) +
      scale_colour_manual(values = colours_tool) +
      theme_maple() +
      theme(
        legend.position = "none",
        axis.title = element_text(size = text_size),
        axis.text = element_text(size = text_size * 0.8),
        plot.title = element_text(size = text_size)
      )
  })

  output$score <- renderPrint({
    req(input$plot_click)
    paste(
      clicked_piece()$setCode,
      clicked_piece()$pieceID,
      sep = " "
    )
  })
}

# ============================================================================ #
shinyApp(ui = ui, server = server)

# ============================================================================ #