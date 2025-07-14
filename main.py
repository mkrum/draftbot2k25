import os
import sys
from typing import Dict, List

import requests
from litellm import completion

POSITIONS = ["RB", "TE", "WR", "QB"]


def make_team_table(picks: List) -> str:
    team_table = "## Starters\n"
    pos = ["QB1", "QB2", "WR1", "WR2", "RB1", "RB2", "TE", "WR/TE", "RB/WR/TE"]
    bench: List[Dict] = []

    team_map = {p: None for p in pos}
    for p in picks:

        if p["metadata"]["position"] == "QB":
            if not team_map["QB1"]:
                team_map["QB1"] = p

            elif not team_map["QB2"]:
                team_map["QB2"] = p

            else:
                bench.append(p)

        elif p["metadata"]["position"] == "RB":
            if not team_map["RB1"]:
                team_map["RB1"] = p

            elif not team_map["RB2"]:
                team_map["RB2"] = p

            elif not team_map["RB/WR/TE"]:
                team_map["RB/WR/TE"] = p

            else:
                bench.append(p)

        elif p["metadata"]["position"] == "WR":
            if not team_map["WR1"]:
                team_map["WR1"] = p

            elif not team_map["WR2"]:
                team_map["WR2"] = p

            elif not team_map["WR/TE"]:
                team_map["WR/TE"] = p

            elif not team_map["RB/WR/TE"]:
                team_map["RB/WR/TE"] = p

            else:
                bench.append(p)

        elif p["metadata"]["position"] == "TE":
            if not team_map["TE"]:
                team_map["TE"] = p

            elif not team_map["WR/TE"]:
                team_map["WR/TE"] = p

            elif not team_map["RB/WR/TE"]:
                team_map["RB/WR/TE"] = p

            else:
                bench.append(p)

    for p in pos:
        player = team_map[p]
        if player is None:
            name = "None"
            team = "None"
        else:
            name = (
                player["metadata"]["first_name"] + " " + player["metadata"]["last_name"]
            )
            team = player["metadata"]["team"]
        team_table += f"| {p} | {name} | {team} | \n"

    while len(bench) < 5:
        bench.append({})

    team_table += "\n## Bench\n"
    for player in bench:
        if player is {}:
            name = "Empty"
            position = "None"
            team = "None"
        else:
            name = (
                player["metadata"]["first_name"] + " " + player["metadata"]["last_name"]
            )
            position = player["metadata"]["position"]
            team = player["metadata"]["team"]

        team_table += f"| {position} | {name} | {team} |\n"

    return team_table


def render_draft_state(player_id: str, draft_id: str) -> str:
    state = requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}/picks").json()
    my_picks = list(filter(lambda x: x["picked_by"] == player_id, state))
    return make_team_table(my_picks)


if __name__ == "__main__":
    draft_id = sys.argv[1]
    player_id = os.getenv("PLAYER_ID")
    state = render_draft_state(player_id, draft_id)

    response = completion(
        model="openai/gpt-4o-search-preview",
        messages=[
            {
                "role": "user",
                "content": state
                + "\n\nWho should I draft next in my Fantasy Football league? Give a final selection in [[]], so it can be easily parsed.",
            }
        ],
        web_search_options={
            "search_context_size": "medium"  # Options: "low", "medium", "high"
        },
    )

    print(response)
