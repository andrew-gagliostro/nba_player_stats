from datetime import datetime, timedelta, time
import json
from nba_api.stats.endpoints import commonplayerinfo, leagueseasonmatchups, leaguegamefinder, teamgamelogs, playergamelogs
from nba_api.stats.static import players, teams
import json
from collections import Counter

def get_player_ids(player_names):
    target_players = [name.strip() for name in player_names.split(",")]
    player_ids = dict()
    for player in players.get_active_players():
        if player['full_name'] in target_players:
            player_ids[player['full_name']] = player['id']

    print(player_ids)
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

    # Assuming games_data and player_data are your datasets
    games_data = teamgamelogs.TeamGameLogs(season_nullable=season).get_normalized_json()
    # players_data = player_info = playergamelogs.PlayerGameLogs(player_id_nullable=201142, season_nullable="2023-24").get_normalized_json()

    player_ids = get_player_ids(player_names)
    all_player_info = playergamelogs.PlayerGameLogs(season_nullable=season).get_normalized_dict()

    games_counter = Counter()
    games_dict = dict()
    for player_id in player_ids.values():
        games = playergamelogs.PlayerGameLogs(player_id_nullable=player_id, season_nullable=season).get_normalized_dict()["PlayerGameLogs"]
        for game in games:
            if game["MIN"] != 0:
                games_counter[game["GAME_ID"]] += 1
                games_dict[game["GAME_ID"]] = game

    # with open('games.json', 'w') as f:
    #     json.dump(games_counter, f)

    breakdown = []
    wins = 0
    losses = 0

    for game in games_counter:
        if games_counter[game] == len(player_ids):
            date = datetime.strptime(games_dict[game]["GAME_DATE"],"%Y-%m-%dT%H:%M:%S").strftime("%m-%d-%Y")
            if games_dict[game]["WL"] == "W":
                wins += 1
            else:
                losses += 1
            summary = " ".join([date, games_dict[game]["MATCHUP"], games_dict[game]["WL"]])
            print(summary)
            breakdown.append(summary)

    def get_date(game):
        date_str = game.split(' ')[0]
        return datetime.strptime(date_str, '%m-%d-%Y')

    sorted_games = sorted(breakdown, key=get_date)
    filename= "".join(player_names.split(", ")).replace(" ", "") + datetime.now().strftime("%m-%d-%Y") + ".txt"
    with open(filename, 'w') as f:
        f.write(f"Players: {player_names}\n")
        f.write(f"Games: {wins + losses}\n")
        f.write(f"Record: {wins}-{losses}\n")
        for game in sorted_games:
            f.write(game + "\n")
        f.close()

