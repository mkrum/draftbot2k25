import json
import random
from dataclasses import dataclass
from typing import List

import htmltabletomd
import openai
import pandas as pd
import requests
from bs4 import BeautifulSoup
from joblib import Memory

POSITIONS = ["RB", "TE", "WR", "QB"]

memory = Memory("cache")


def get_data(url: str):
    data = requests.get(url)
    return data


def get_completion(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
        )
    except openai.error.APIError:
        print("\n[red]API is down[red]")
        exit()

    return response["choices"][0]["message"]["content"]


@dataclass
class Player:
    name: str
    team: str
    position: str
    rankings: str
    adp: str
    projections: str
    stats: str
    expert_note: str
    sleeper_id: str
    news: List[str]

    @classmethod
    @memory.cache
    def from_url(cls, url: str, team: str, position: str, sleeper_id: str):

        data = requests.get("https://www.fantasypros.com/nfl/players/" + url)
        soup = BeautifulSoup(data.text, "html.parser")

        name = str(soup.find("title").get_text()).split("Fantasy")[0]

        tables = [str(t) for t in soup.findAll("table")]
        rankings_table = htmltabletomd.convert_table(tables[1])
        adp_table = htmltabletomd.convert_table(tables[2])
        projections_table = htmltabletomd.convert_table(tables[3])
        stats_table = htmltabletomd.convert_table(tables[4])

        content = soup.findAll("div", {"class": "content"})
        expert_note = content[0].get_text()
        news = content[1].get_text()
        return cls(
            name,
            team,
            position,
            rankings_table,
            adp_table,
            projections_table,
            stats_table,
            expert_note,
            sleeper_id,
            [news],
        )

    def __str__(self):
        return f"## {self.name}({self.team}, {self.position})\n\n### Expert Note\n{self.expert_note}\n\n### News\n{self.news[0]}\n\n### 2022 Stats\n{self.stats}\n### Projections\n{self.projections}\n### ADP\n{self.adp}"


def get_players(rankings_df, state, num_per_position=3):
    urls = []
    teams = []
    poses = []
    for s in state:
        rankings_df = rankings_df[rankings_df["sleeper_id"] != s["player_id"]]

    for p in POSITIONS:
        mask = rankings_df["player_position_id"] == p
        pos_df = rankings_df[mask]
        urls += pos_df.head(num_per_position)["player_filename"].tolist()
        teams += pos_df.head(num_per_position)["player_team_id"].tolist()
        poses += [p] * num_per_position

    return list(zip(urls, teams, poses))


def make_team_table(picks):
    team_table = "## Starters\n"
    pos = ["QB1", "QB2", "WR1", "WR2", "RB1", "RB2", "TE", "WR/TE", "RB/WR/TE"]
    bench = []

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
        bench.append(None)

    team_table += "\n## Bench\n"
    for player in bench:
        if player is None:
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


def get_pick(player_id, draft_id):
    state = (
        []
    )  # requests.get(f"https://api.sleeper.app/v1/draft/{draft_id}/picks").json()

    my_picks = list(filter(lambda x: x["picked_by"] == player_id, state))

    team_table = make_team_table(my_picks)

    df = pd.read_json("rankings.json")
    sleeper_id_map = json.load(open("sleeper_map.json", "r"))
    df["sleeper_id"] = df["player_filename"].apply(
        lambda x: sleeper_id_map.get(x, None)
    )
    urls = get_players(df, state, num_per_position=3)
    players = []
    for url in urls:
        try:
            players.append(Player.from_url(*url, sleeper_id_map[url[0]]))
        except Exception:
            print(url)

    random.shuffle(players)

    input_str = (
        "# Available Players\n"
        + "\n".join([str(p) for p in players])
        + f"\n# Current Team\n{team_table}\nQuestion: Which player should I pick?"
    )
    messages = [
        {
            "role": "system",
            "content": "You are a Fantasy Football Draft bot. Users give you information about their team and players, and you tell them who to pick. Before you answer, you should always think through and consider the options before you make a decision. It is required that you give a specific recommendation of a single player to draft, even if you are not entirely sure. The league is a half-PPR two QB league. Make the last line just the recommended player name.",
        },
        {"role": "user", "content": input_str},
    ]
    print(input_str)
    return team_table + "\n" + get_completion(messages)


if __name__ == "__main__":
    player_id = "867176465991655424"
    draft_id = "1005142738406387712"
    print(get_pick(player_id, draft_id))
