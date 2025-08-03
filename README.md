This repository contains my key projects for the Nighthawks for the 2025 NECBL season. It includes:
xwobaNew.Rmd: An R script developing an XGBoost model to predict BIP outcomes and create xwOBA for the league
Stuff.Rmd: An R scropt developing a random forest model to predict pitch outcomes and create a statistic I call "expected runs saved"
app.R: A shiny app for the league dashboard
app2.R: A shiny app containing game by game Nighthawk hitter reports
Test25.py: A Python script that combined all Trackman CSVs into one master dataset that I use in xwobaNew.Rmd and Stuff.Rmd
Extract.py: A Python script to scrape player statistics from the NECBL website
