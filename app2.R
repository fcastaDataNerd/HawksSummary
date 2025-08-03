library(shiny)
library(tidyverse)
library(DT)
library(xgboost)
library(plotly)

# ---- Load Data ----
df <- read_csv("Test2025_combined.csv")

# ---- Load Trained xwOBA Model ----
xgb_model <- readRDS("xgb_xwoba_model.rds")

# ---- Prepare and Format Batter Names ----
df <- df %>%
  filter(BatterTeam == "UPP_VAL") %>%
  filter(!is.na(Batter)) %>%
  filter(!is.na(AutoPitchType)) %>%
  mutate(
    Batter = str_trim(Batter),
    LastName = toupper(str_extract(Batter, "^[^,]+")),
    FirstInitial = toupper(str_sub(str_extract(Batter, ",\\s*\\w"), -1)),
    BatterFormatted = paste0(LastName, ", ", FirstInitial)
  )

nighthawks_df <- df

# ---- UI ----
ui <- fluidPage(
  titlePanel("Upper Valley Nighthawks - Game-by-Game Hitter Reports"),
  
  do.call(tabsetPanel, c(id = "player_tabs", lapply(unique(nighthawks_df$BatterFormatted), function(player) {
    safe_id <- make.names(player)
    tabPanel(player,
             selectInput(
               inputId = paste0("date_", safe_id),
               label = "Select Game Date",
               choices = NULL
             ),
             DTOutput(outputId = paste0("pitch_table_", safe_id)),
             br(),
             plotlyOutput(outputId = paste0("chase_take_plot_", safe_id), height = "600px"),
             br(),
             wellPanel(
               h4("Chase/Take Plot Explanation"),
               p("This plot shows whether the hitter made a good decision based on pitch location."),
               p("Circles indicate good decisions (swinging at strikes or taking balls)."),
               p("Squares indicate poor decisions (chasing balls or taking strikes).")
             )
    )
  })))
)

# ---- Server ----
server <- function(input, output, session) {
  players <- unique(nighthawks_df$BatterFormatted)
  non_swing_calls <- c("BallCalled", "BallinDirt", "StrikeCalled", "BallIntentional", "HitByPitch")
  
  for (player in players) {
    local({
      player_copy <- player
      safe_id <- make.names(player_copy)
      
      observe({
        player_data <- nighthawks_df %>% filter(BatterFormatted == player_copy)
        game_dates <- unique(player_data$Date) %>% sort()
        updateSelectInput(session, inputId = paste0("date_", safe_id), choices = game_dates)
      })
      
      render_game_data <- reactive({
        req(input[[paste0("date_", safe_id)]])
        player_game_data <- nighthawks_df %>%
          filter(BatterFormatted == player_copy, Date == input[[paste0("date_", safe_id)]])
        
        model_rows <- which(
          player_game_data$PitchCall == "InPlay" &
            !is.na(player_game_data$ExitSpeed) &
            !is.na(player_game_data$Angle) &
            !is.na(player_game_data$Direction)
        )
        
        prob_cols <- c("Out", "Single", "Double", "Triple", "HomeRun")
        for (col in prob_cols) player_game_data[[col]] <- NA_real_
        
        if (length(model_rows) > 0) {
          input_matrix <- as.matrix(player_game_data[model_rows, c("ExitSpeed", "Angle", "Direction")])
          pred_probs <- predict(xgb_model, input_matrix)
          pred_probs <- matrix(pred_probs, ncol = 5, byrow = TRUE)
          colnames(pred_probs) <- prob_cols
          player_game_data[model_rows, prob_cols] <- pred_probs
        }
        
        woba_weights <- c("Out" = 0, "Single" = 0.882, "Double" = 1.254, "Triple" = 1.59, "HomeRun" = 2.05)
        player_game_data <- player_game_data %>%
          mutate(xwOBA = case_when(
            !is.na(Single) ~ Out * woba_weights["Out"] +
              Single * woba_weights["Single"] +
              Double * woba_weights["Double"] +
              Triple * woba_weights["Triple"] +
              HomeRun * woba_weights["HomeRun"],
            TRUE ~ woba_weights[as.character(PlayResult)]
          )) %>%
          mutate(across(c(
            Out, Single, Double, Triple, HomeRun, xwOBA,
            ExitSpeed, Angle, Direction,
            PlateLocHeight, PlateLocSide,
            RelSpeed, SpinRate, VertBreak, HorzBreak
          ), ~ round(.x, 2)))
        
        return(player_game_data)
      })
      
      output[[paste0("pitch_table_", safe_id)]] <- renderDT({
        render_game_data() %>%
          select(
            PitcherThrows, BatterSide, Balls, Strikes, AutoPitchType,
            PitchCall, PlayResult,
            ExitSpeed, Angle, Direction,
            PlateLocHeight, PlateLocSide,
            RelSpeed, SpinRate, VertBreak, HorzBreak,
            Out, Single, Double, Triple, HomeRun, xwOBA
          )
      })
      
      output[[paste0("chase_take_plot_", safe_id)]] <- renderPlotly({
        data <- render_game_data() %>%
          filter(!is.na(PlateLocHeight), !is.na(PlateLocSide)) %>%
          mutate(
            InZone = PlateLocSide >= -0.85 & PlateLocSide <= 0.85 &
              PlateLocHeight >= 1.5 & PlateLocHeight <= 3.5,
            GoodDecision = case_when(
              InZone & !(PitchCall %in% non_swing_calls) ~ TRUE,
              !InZone & PitchCall %in% non_swing_calls ~ TRUE,
              TRUE ~ FALSE
            ),
            shape = if_else(GoodDecision, "circle", "square"),
            hover_text = if_else(
              PitchCall == "InPlay",
              paste0("Pitch Type: ", AutoPitchType, "<br>",
                     "Count: ", Balls, "-", Strikes, "<br>",
                     "PitchCall: ", PitchCall, "<br>",
                     "PlayResult: ", PlayResult, "<br>",
                     "Out: ", Out, ", 1B: ", Single, ", 2B: ", Double, ", 3B: ", Triple, ", HR: ", HomeRun),
              paste0("Pitch Type: ", AutoPitchType, "<br>",
                     "Count: ", Balls, "-", Strikes, "<br>",
                     "PitchCall: ", PitchCall, "<br>",
                     "PlayResult: ", PlayResult)
            )
          )
        
        if (nrow(data) == 0) return(NULL)
        
        plot_ly(data,
                x = ~PlateLocSide, y = ~PlateLocHeight,
                type = "scatter", mode = "markers",
                symbol = ~shape,
                symbols = c("circle", "square"),
                color = ~AutoPitchType,
                text = ~hover_text,
                hoverinfo = "text",
                marker = list(size = 8, line = list(width = 1, color = "black"))
        ) %>%
          layout(
            title = "Chase/Take Analysis",
            xaxis = list(title = "PlateLocSide", range = c(-4, 4), scaleanchor = "y", scaleratio = 1),
            yaxis = list(title = "PlateLocHeight", range = c(0, 5)),
            shapes = list(list(type = "rect", x0 = -0.85, x1 = 0.85, y0 = 1.5, y1 = 3.5, line = list(color = "red")))
          )
      })
    })
  }
}

# ---- Run App ----
shinyApp(ui = ui, server = server)
