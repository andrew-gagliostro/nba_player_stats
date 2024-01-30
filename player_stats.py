from datetime import datetime, timedelta, time
import json
from nba_api.stats.endpoints import commonplayerinfo, leagueseasonmatchups, leaguegamefinder, teamgamelogs, playergamelogs
from nba_api.stats.static import players, teams
import json
from collections import Counter, defaultdict
import csv
import pandas as pd
from openpyxl.utils import get_column_letter
from openpyxl.styles import PatternFill

def get_player_ids(player_names):
    target_players = [name.strip() for name in player_names.split(",")]
    player_ids = dict()
    for player in players.get_active_players():
        if player['full_name'] in target_players:
            player_ids[player['full_name']] = player['id']

    # print(player_ids)
    return player_ids

def check_games(players_ids, player_data, games):
    games_counter = Counter()
    for player_id in players_ids:
        for player in player_data["PlayerGameLogs"]:
            if player["PLAYER_ID"] == player_id:
                games_counter[player["GAME_ID"]] += 1
    
    return [game for game, count in games_counter.items() if count == len(players_ids)]

while True:
    player_names = input("Enter player names separated by commas in the format 'P1, P2, P3': ")
    if player_names == "":
        break
    season = input("Enter the season in the format 'YYYY-YY': ")

    verbose_output = input("Do you want verbose output for player activity of each game (y/n)?: ")


    # Assuming games_data and player_data are your datasets
    games_data = teamgamelogs.TeamGameLogs(season_nullable=season).get_normalized_json()
    # players_data = player_info = playergamelogs.PlayerGameLogs(player_id_nullable=201142, season_nullable="2023-24").get_normalized_json()

    player_ids = get_player_ids(player_names)
    all_player_info = playergamelogs.PlayerGameLogs(season_nullable=season).get_normalized_dict()

    games_counter = Counter()
    games_dict = dict()
    game_player_activity_dict = defaultdict(dict)
    for player_name, player_id in player_ids.items():
        games = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable=season).get_normalized_dict()["PlayerGameLogs"]
        for game in games:
            if game["MIN"] != 0:
                games_counter[game["GAME_ID"]] += 1
                game_player_activity_dict[game["GAME_ID"]][player_name] = game
                if games_counter[game["GAME_ID"]] == len(player_ids):
                    games_dict[game["GAME_ID"]] = game

    with open('game_player_activity_dict.json', 'w') as f:
        json.dump(game_player_activity_dict, f)

    breakdown = []
    wins = 0
    losses = 0

    for game in games_dict:
        date = datetime.strptime(games_dict[game]["GAME_DATE"],"%Y-%m-%dT%H:%M:%S").strftime("%m-%d-%Y")
        if games_dict[game]["WL"] == "W":
            wins += 1
        else:
            losses += 1

        summary = [date, games_dict[game]["MATCHUP"], games_dict[game]["WL"]]
        # print(summary)
        breakdown.append(summary)

    def get_date(game):
        date_str = game[0]
        return datetime.strptime(date_str, '%m-%d-%Y')

    sorted_games = sorted(breakdown, key=get_date)
    filename= "".join(player_names.split(", ")).replace(" ", "") + datetime.now().strftime("%m-%d-%Y") + ".csv"
    # with open(filename, 'w') as f:
    #     f.write(f"Players: {player_names}\n")
    #     f.write(f"Games: {wins + losses}\n")
    #     f.write(f"Record: {wins}-{losses}\n")
    #     for game in sorted_games:
    #         f.write(game + "\n")
    #     f.close()
        
    # create dataframe
    df_games = pd.DataFrame(sorted_games, columns=["Date", "Matchup", "Win/Loss"])

    summary_df = pd.DataFrame([["Players", "Season", "Games", "Record"],
                               [player_names, season, f"{wins + losses}", f"{wins}-{losses}"]],
                            columns=None)

    filename_excel = "".join(player_names.split(", ")).replace(" ", "") + datetime.now().strftime("%m-%d-%Y") + ".xlsx"
    with pd.ExcelWriter(filename_excel, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, header=False, sheet_name='Sheet1')
        df_games.to_excel(writer, index=False, sheet_name='Sheet1', startrow=4)


    from openpyxl import load_workbook
    wb = load_workbook(filename_excel)
    sheet = wb['Sheet1']

    # Set the alignment for game field
    from openpyxl.styles import Alignment
    for row in sheet.iter_rows(min_row=1, max_row=3):
        for cell in row:
            cell.alignment = Alignment(horizontal='center')

    # bold cells
    from openpyxl.styles import Font
    bold_font = Font(bold=True)
    for cell in sheet[1]:
        cell.font = bold_font

    # adjust columns widths
    for column_cells in sheet.columns:
        max_length = 0
        column = get_column_letter(column_cells[0].column)  # convert column index to letter
        for cell in column_cells:
            try:  # Necessary to avoid error on empty cells
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 5)
        sheet.column_dimensions[column].width = adjusted_width
        
    fill = PatternFill(start_color="FFC7CE",
                    end_color="FFC7CE",
                    fill_type="solid")

    # Apply color fill to headers
    for cell in sheet[1]:
        cell.fill = fill
    for cell in sheet.iter_cols(min_col=1, max_col=3, min_row=5, max_row=5):
        cell[0].fill = fill

    wb.save(filename_excel)
    print(f"Output saved as {filename_excel}")
    print("Press enter To exit, or enter player names to continue with another query")


