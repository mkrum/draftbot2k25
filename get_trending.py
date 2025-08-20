#!/usr/bin/env python3
"""Get the top 10 trending players with their names."""

import json

from sleeper_api import SleeperAPI


def get_top_trending_players():
    api = SleeperAPI()

    # Get trending players
    print("Fetching top 10 trending players...")
    trending = api.get_trending_players(sport="nfl", type="add")[:10]

    # Load players from local file
    print("Loading player database from players.json...")
    with open("players.json", "r") as f:
        all_players = json.load(f)

    print("\nTop 10 Trending Players (by adds):\n")
    print(f"{'Rank':<5} {'Name':<25} {'Position':<8} {'Team':<6} {'Adds':<10}")
    print("-" * 60)

    for i, player in enumerate(trending, 1):
        player_data = all_players.get(player.player_id)

        if player_data:
            first_name = player_data.get("first_name", "")
            last_name = player_data.get("last_name", "")
            name = f"{first_name} {last_name}".strip()
            if not name:
                name = "Unknown"
            position = player_data.get("position") or "N/A"
            team = player_data.get("team") or "FA"
        else:
            name = f"Player ID: {player.player_id}"
            position = "N/A"
            team = "N/A"

        print(f"{i:<5} {name:<25} {position:<8} {team:<6} {player.count:<10,}")


if __name__ == "__main__":
    get_top_trending_players()
