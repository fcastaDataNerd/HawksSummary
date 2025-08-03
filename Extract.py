import requests
from bs4 import BeautifulSoup
import pandas as pd
import io

# Mapping of team URLs to team abbreviations
team_urls = {
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=89490&seasonid=34029&view=batting&bset=0&orderby=avg": "BRI_B",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6402&seasonid=34029&view=batting&bset=0&orderby=avg": "DAN_WES",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6401&seasonid=34029&view=batting&bset=0&orderby=avg": "KEE_SWA",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=142675&seasonid=34029&view=batting&bset=0&orderby=avg": "MAR_VIN",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=11912&seasonid=34029&view=batting&bset=0&orderby=avg": "MYS_SCH",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6458&seasonid=34029&view=batting&bset=0&orderby=avg": "NEW_GUL",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6404&seasonid=34029&view=batting&bset=0&orderby=avg": "NOR_ADA",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=154432&seasonid=34029&view=batting&bset=0&orderby=avg": "NSH_N",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=51489&seasonid=34029&view=batting&bset=0&orderby=avg": "OCE_STA6",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6459&seasonid=34029&view=batting&bset=0&orderby=avg": "SAN_MAI",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=104040&seasonid=34029&view=batting&bset=0&orderby=avg": "UPP_VAL",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6403&seasonid=34029&view=batting&bset=0&orderby=avg": "VAL_BLU",
    "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6405&seasonid=34029&view=batting&bset=0&orderby=avg": "VER_MOU"
}

# Collect and tag each table
all_dataframes = []

for url, team_abbr in team_urls.items():
    print(f"Scraping: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if table:
        df = pd.read_html(io.StringIO(str(table)))[0]
        df['Team'] = team_abbr
        all_dataframes.append(df)
    else:
        print(f"Warning: No table found at {url}")

# Combine and clean
final_df = pd.concat(all_dataframes, ignore_index=True)
final_df.columns = final_df.columns.str.strip()

# Clean Player column
final_df = final_df[final_df['Player'].str.strip().str.lower() != 'total:']
final_df['Player'] = final_df['Player'].str.replace(r'^x\s+', '', regex=True)
final_df['Player'] = final_df['Player'].str.strip()
final_df['Player'] = final_df['Player'].str.replace(r'\s+', ' ', regex=True)

# Convert to numeric
cols_to_numeric = ['AB', 'H', '2B', '3B', 'HR', 'BB', 'HBP', 'SF', 'SH']
for col in cols_to_numeric:
    final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)

# Derived stats
final_df['1B'] = final_df['H'] - final_df['2B'] - final_df['3B'] - final_df['HR']
final_df['PA'] = final_df['AB'] + final_df['BB'] + final_df['HBP'] + final_df['SF'] + final_df['SH']
# Filter out rows where PA is 0 or less
final_df = final_df[final_df['PA'] > 0].copy()
final_df['OBP'] = (final_df['H'] + final_df['BB'] + final_df['HBP']) / (
    final_df['AB'] + final_df['BB'] + final_df['HBP'] + final_df['SF']
)

final_df['SLG'] = (final_df['1B'] + 2*final_df['2B'] + 3*final_df['3B'] + 4*final_df['HR']) / final_df['AB']
final_df['OPS'] = final_df['OBP'] + final_df['SLG']

# wOBA weights
wBB = 0.689
wHBP = 0.72
w1B = 0.882
w2B = 1.254
w3B = 1.59
wHR = 2.05

# Compute wOBA numerator and denominator
numerator = (
    wBB * final_df['BB'] +
    wHBP * final_df['HBP'] +
    w1B * final_df['1B'] +
    w2B * final_df['2B'] +
    w3B * final_df['3B'] +
    wHR * final_df['HR']
)
denominator = final_df['AB'] + final_df['BB'] + final_df['SF'] + final_df['HBP']

final_df['wOBA'] = numerator / denominator
final_df['wOBA'] = final_df['wOBA'].round(3)

# Save the enriched file
final_df.to_csv("C:/Users/franc/OneDrive/Hawks25/necbl_combined_batting_stats.csv", index=False)

print("✅ wOBA calculated and stats updated.")
print(final_df[['Player', 'Team', 'PA', 'OBP', 'SLG', 'OPS', 'wOBA']].head())
print(len(final_df))




# Dictionary with team pitching stats URLs for pset=0 and pset=1
team_urls2 = {
    "BRI_B": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=89490&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=89490&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "DAN_WES": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6402&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6402&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "KEE_SWA": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6401&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6401&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "MAR_VIN": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=142675&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=142675&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "MYS_SCH": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=11912&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=11912&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "NEW_GUL": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6458&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6458&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "NOR_ADA": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6404&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6404&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "NSH_N": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=154432&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=154432&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "OCE_STA6": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=51489&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=51489&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "SAN_MAI": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6459&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6459&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "UPP_VAL": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=104040&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=104040&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "VAL_BLU": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6403&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6403&seasonid=34029&view=pitching&pset=1&orderby=era"
    ],
    "VER_MOU": [
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6405&seasonid=34029&view=pitching&pset=0&orderby=era",
        "http://necbl.wttbaseball.pointstreak.com/team_stats.html?teamid=6405&seasonid=34029&view=pitching&pset=1&orderby=era"
    ]
}

pset0_dfs = []
pset1_dfs = []

for team, urls in team_urls2.items():
    for i, url in enumerate(urls):
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.find("table")
        if table:
            df = pd.read_html(io.StringIO(str(table)))[0]
            df['Team'] = team
            if i == 0:
                pset0_dfs.append(df)
            else:
                pset1_dfs.append(df)

# Combine tables
pset0_combined = pd.concat(pset0_dfs, ignore_index=True)
pset1_combined = pd.concat(pset1_dfs, ignore_index=True)

# Clean function
def clean_df(df):
    df.columns = df.columns.str.strip()
    df.drop(df[df['Player'].str.strip().str.lower() == 'total:'].index, inplace=True)
    df['Player'] = df['Player'].astype(str).str.replace(r'^x\s+', '', regex=True)
    df['Player'] = df['Player'].str.replace(r'\s+', ' ', regex=True).str.strip().str.title()
    df['Team'] = df['Team'].astype(str).str.strip().str.upper()
    return df

# Clean both
pset0_combined = clean_df(pset0_combined)
pset1_combined = clean_df(pset1_combined)

# Drop duplicate ERA from pset1
pset1_combined = pset1_combined.drop(columns=["ERA"], errors="ignore")

# Merge datasets on cleaned keys
merged_pitching = pd.merge(
    pset0_combined,
    pset1_combined,
    on=["Player", "Team"],
    how="outer"
)

# Save merged output
# Drop unwanted columns
columns_to_drop = ['G', 'GS', 'CG', 'W', 'L', 'SV', 'SHO', 'BAA', 'STRIKE %', 'WP']
merged_pitching.drop(columns=columns_to_drop, inplace=True, errors='ignore')


merged_pitching['IP'] = merged_pitching['IP'].astype(str)
merged_pitching['IP'] = merged_pitching['IP'].str.replace(r'(\.1)$', '.33', regex=True)
merged_pitching['IP'] = merged_pitching['IP'].str.replace(r'(\.2)$', '.67', regex=True)
merged_pitching['IP'] = pd.to_numeric(merged_pitching['IP'], errors='coerce').fillna(0)

#for col in ['HR', 'BB', 'HBP', 'SO', 'ER']:
#    merged_pitching[col] = pd.to_numeric(merged_pitching[col], errors='coerce').fillna(0)

# Filter for valid innings
merged_pitching = merged_pitching[merged_pitching['IP'] > 0].copy()

# Calculate league totals
total_ER = merged_pitching['ER'].sum()
total_IP = merged_pitching['IP'].sum()
total_HR = merged_pitching['HR'].sum()
total_BB = merged_pitching['BB'].sum()
total_HBP = merged_pitching['HBP'].sum()
total_SO = merged_pitching['SO'].sum()

# League ERA
league_ERA = (9 * total_ER) / total_IP

# League Raw FIP
league_raw_fip = (13 * total_HR + 3 * (total_BB + total_HBP) - 2 * total_SO) / total_IP

# FIP Constant
fip_constant = league_ERA - league_raw_fip

# Calculate FIP for each player
merged_pitching['FIP'] = (
    (13 * merged_pitching['HR'] +
     3 * (merged_pitching['BB'] + merged_pitching['HBP']) -
     2 * merged_pitching['SO']) / merged_pitching['IP']
) + fip_constant

merged_pitching['FIP'] = merged_pitching['FIP'].round(2)

# Save updated file
merged_pitching.to_csv("C:/Users/franc/OneDrive/Hawks25/necbl_combined_pitching_stats.csv", index=False)


# Preview a few rows with all remaining stats
print("✅ Final cleaned pitching stats:")
print(merged_pitching.head())
print(len(merged_pitching))