import os
import sys
from typing import Dict, List, Optional

from litellm import completion

from sleeper_api import DraftPickData, SleeperAPI


def make_team_table(picks: List[DraftPickData]) -> str:
    team_table = "## Starters\n"
    pos = ["QB1", "QB2", "WR1", "WR2", "RB1", "RB2", "TE", "WR/TE", "RB/WR/TE", "DEF"]
    bench: List[DraftPickData] = []

    team_map: Dict[str, Optional[DraftPickData]] = {p: None for p in pos}
    for p in picks:

        if p.metadata and p.metadata.position == "QB":
            if not team_map["QB1"]:
                team_map["QB1"] = p

            elif not team_map["QB2"]:
                team_map["QB2"] = p

            else:
                bench.append(p)

        elif p.metadata and p.metadata.position == "RB":
            if not team_map["RB1"]:
                team_map["RB1"] = p

            elif not team_map["RB2"]:
                team_map["RB2"] = p

            elif not team_map["RB/WR/TE"]:
                team_map["RB/WR/TE"] = p

            else:
                bench.append(p)

        elif p.metadata and p.metadata.position == "WR":
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

        elif p.metadata and p.metadata.position == "TE":
            if not team_map["TE"]:
                team_map["TE"] = p

            elif not team_map["WR/TE"]:
                team_map["WR/TE"] = p

            elif not team_map["RB/WR/TE"]:
                team_map["RB/WR/TE"] = p

            else:
                bench.append(p)

        elif p.metadata and p.metadata.position == "DEF":
            if not team_map["DEF"]:
                team_map["DEF"] = p
            else:
                bench.append(p)

    for p in pos:
        player = team_map[p]
        if player is None:
            name = "None"
            team = "None"
        else:
            if player.metadata:
                name = f"{player.metadata.first_name} {player.metadata.last_name}"
                team = player.metadata.team or "None"
            else:
                name = "Unknown"
                team = "None"
        team_table += f"| {p} | {name} | {team} | \n"

    while len(bench) < 5:
        bench.append(None)  # type: ignore

    team_table += "\n## Bench\n"
    for player in bench:
        if player is None:
            name = "Empty"
            position = "None"
            team = "None"
        elif player.metadata:
            name = f"{player.metadata.first_name} {player.metadata.last_name}"
            position = player.metadata.position or "None"
            team = player.metadata.team or "None"
        else:
            name = "Unknown"
            position = "None"
            team = "None"

        team_table += f"| {position} | {name} | {team} |\n"

    return team_table


def render_draft_state(player_id: str, draft_id: str) -> Dict[str, str]:
    api = SleeperAPI()
    picks = api.get_draft_picks(draft_id)

    draft_slots: set[int] = set(p.draft_slot for p in picks)
    teams: Dict[str, str] = {}

    for slot in draft_slots:
        slot_picks = [p for p in picks if p.draft_slot == slot]
        teams[str(slot)] = make_team_table(slot_picks)

    return teams


if __name__ == "__main__":
    draft_id = sys.argv[1]
    player_id = os.getenv("PLAYER_ID")
    state = render_draft_state(player_id, draft_id)

    taken_players = "\n".join([v for k, v in state.items() if k != player_id])
    message = (
        "Taken Players:\n"
        + taken_players
        + "\n\nCurrent Team:\n\n"
        + state.get(player_id, "")
        + "\n\nWho should I draft next in my Fantasy Football league? Give a final selection in [[]], so it can be easily parsed."
    )

    print(message)
    response = completion(
        model="openai/gpt-4o-search-preview",
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        web_search_options={
            "search_context_size": "medium"  # Options: "low", "medium", "high"
        },
    )

    print(response)
