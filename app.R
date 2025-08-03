library(shiny)
library(tidyverse)
library(DT)
library(plotly)

pitching_df <- read_csv("necbl_combined_pitching_stats.csv", show_col_types = FALSE)
batting_df <- read_csv("necbl_combined_batting_stats.csv", show_col_types = FALSE)

# UI
ui <- fluidPage(
  titlePanel("NECBL 2025 Dashboard"),
  
  tabsetPanel(
    tabPanel("Batting Percentiles",
             br(),
             fluidRow(
               column(4,
                      numericInput("minPA", "Minimum PA:", value = 0, min = 0, step = 10)
               ),
               column(4,
                      selectInput("team", "Select Team:",
                                  choices = c("All", unique(batting_df$Team)),
                                  selected = "All")
               )
             ),
             DTOutput("batting_table"),
             br(),
             wellPanel(
               h4("Batting Stat Descriptions"),
               tags$ul(
                 tags$li(strong("wOBA:"), " Weighted On-Base Average. Weights each on base event (BB, HBP, 1B, 2B, 3B, HR) appropriately based on its average impact on run scoring."),
                 tags$li(strong("xwOBA_adjusted:"), " Expected Weighted On-Base Average. Estimates what wOBA should be based on quality of contact on BIP"),
                 tags$li(strong("diff_adjusted:"), " Difference between actual and expected wOBA. Positive numbers indicate a batter is unlucky and negative numbers indicate a batter is lucky"),
                 tags$li(strong("xwOBA_per_BIP:"), " Expected wOBA per ball in play. The average expected value of all BIP for a batter."),
               )
             )
    ),
    
    tabPanel("Pitching Percentiles",
             br(),
             fluidRow(
               column(4,
                      numericInput("minIP", "Minimum IP:", value = 0, min = 0, step = 5)
               ),
               column(4,
                      selectInput("pitch_team", "Select Team:",
                                  choices = c("All", unique(pitching_df$Team)),
                                  selected = "All")
               )
             ),
             DTOutput("pitching_percentiles_table"),
             br(),
             wellPanel(
               h4("Pitching Stat Descriptions"),
               tags$ul(
                 tags$li(strong("Actual Run Value / 100:"), "Average run value per 100 pitches. Every pitch outcome has an average run value attached to it that will either increase or decrease the expected runs scored for the batting team:
                         Ball: +0.056
                         Strike: -0.089
                         HBP: +0.31
                         Out: -0.26
                         1B: +0.44
                         2B: +0.75
                         3B: +1.01
                         HR: +1.4
                         A pitcher hopes this statistic is negative. It reads as: When this pitcher throws a pitch, on average he will either reduce the expected runs scored of the batting team by x (when negative) or increase the expected runs of the batting team by x (when positive). This is a per 100 pitches statistic"),
                 tags$li(strong("Expected Run Value / 100:"), " Expected run value per 100 pitches. This statistic estimates what the actual run value per 100 pitches should be based on the quality of pitch thrown by the pitcher. The interpretation is essentially the same as actual run value per 100 pitches, but it takes into consideration how well a pitcher is executing each pitch."),
                 tags$li(strong("Difference / 100:"), "Expected minus actual run value. A negative value indicates actual run value per 100 should be lower than it currently is, meaning a pitcher has been unlucky. A positive number means actual run value per 100 should be greater than it currently is, meaning the pitcher has been lucky.")
               )
             )
    )
  )
)

# Server
server <- function(input, output) {
  
  output$batting_table <- renderDT({
    df <- batting_df %>%
      filter({if (input$team != "All") Team == input$team else TRUE}) %>%
      filter(PA >= input$minPA) %>%
      mutate(
        OBP_Pctl = percent_rank(OBP) * 100,
        SLG_Pctl = percent_rank(SLG) * 100,
        OPS_Pctl = percent_rank(OPS) * 100,
        wOBA_Pctl = percent_rank(wOBA) * 100,
        xwOBA_Pctl = percent_rank(xwOBA_adjusted) * 100,
        Diff_Pctl = percent_rank(diff_adjusted) * 100,
        xwOBA_per_BIP_Pctl = percent_rank(xwOBA_per_BIP) * 100
      ) %>%
      mutate(across(c(wOBA, xwOBA_adjusted, diff_adjusted, xwOBA_per_BIP,
                      OBP, SLG, OPS,
                      OBP_Pctl, SLG_Pctl, OPS_Pctl,
                      wOBA_Pctl, xwOBA_Pctl, Diff_Pctl, xwOBA_per_BIP_Pctl),
                    ~round(.x, 3)))
    
    datatable(df %>%
                select(Player, Team, PA,
                       wOBA, wOBA_Pctl,
                       xwOBA_adjusted, xwOBA_Pctl,
                       diff_adjusted, Diff_Pctl,
                       xwOBA_per_BIP, xwOBA_per_BIP_Pctl,
                       OBP, OBP_Pctl,
                       SLG, SLG_Pctl,
                       OPS, OPS_Pctl),
              options = list(pageLength = 25),
              rownames = FALSE) %>%
      formatStyle(
        columns = c('wOBA_Pctl', 'xwOBA_Pctl', 'Diff_Pctl', 'xwOBA_per_BIP_Pctl',
                    'OBP_Pctl', 'SLG_Pctl', 'OPS_Pctl'),
        background = styleColorBar(c(0, 100), 'lightblue'),
        backgroundSize = '90% 60%',
        backgroundRepeat = 'no-repeat',
        backgroundPosition = 'center'
      )
  })
  
  
  output$pitching_percentiles_table <- renderDT({
    df <- pitching_df %>%
      filter({if (input$pitch_team != "All") Team == input$pitch_team else TRUE}) %>%
      filter(IP >= input$minIP) %>%
      mutate(
        # Scale run value metrics per 100 pitches
        xRV_100 = avg_xRunValue * 100,
        aRV_100 = avg_ActualRunValue * 100,
        diff_100 = -1*difference * 100,
        
        # Percentiles (higher is better for reverse stats like ERA)
        ERA_Pctl = (1 - percent_rank(ERA)) * 100,
        WHIP_Pctl = (1 - percent_rank(WHIP)) * 100,
        FIP_Pctl = (1 - percent_rank(FIP)) * 100,
        xRV_Pctl = (1 - percent_rank(xRV_100)) * 100,
        aRV_Pctl = (1 - percent_rank(aRV_100)) * 100,
        diffRV_Pctl = (1-percent_rank(diff_100)) * 100
      ) %>%
      mutate(across(
        c(ERA, WHIP, FIP, xRV_100, aRV_100, diff_100,
          ERA_Pctl, WHIP_Pctl, FIP_Pctl, xRV_Pctl, aRV_Pctl, diffRV_Pctl),
        ~ round(.x, 3)
      ))
    
    datatable(df %>%
                select(Player, Team, IP,
                       ERA, ERA_Pctl,
                       WHIP, WHIP_Pctl,
                       FIP, FIP_Pctl,
                       xRV_100, xRV_Pctl,
                       aRV_100, aRV_Pctl,
                       diff_100, diffRV_Pctl),
              options = list(pageLength = 25),
              rownames = FALSE,
              colnames = c(
                "Player", "Team", "IP",
                "ERA", "ERA_Pctl",
                "WHIP", "WHIP_Pctl",
                "FIP", "FIP_Pctl",
                "Expected Run Value / 100", "xRV_Pctl",
                "Actual Run Value / 100", "aRV_Pctl",
                "Difference / 100", "Diff_Pctl"
              )) %>%
      formatStyle(
        columns = c('ERA_Pctl', 'WHIP_Pctl', 'FIP_Pctl',
                    'xRV_Pctl', 'aRV_Pctl', 'diffRV_Pctl'),
        background = styleColorBar(c(0, 100), 'lightblue'),
        backgroundSize = '90% 60%',
        backgroundRepeat = 'no-repeat',
        backgroundPosition = 'center'
      )
  })
}

# Run the app
shinyApp(ui = ui, server = server)
