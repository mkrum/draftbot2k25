#!/usr/bin/env python3
"""Parse ADP data and match with Sleeper player IDs."""

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ADPPlayer:
    rank: int
    name: str
    team: str
    bye_week: int
    position: str
    position_rank: int
    yahoo_rank: int
    sleeper_rank: int
    rtsports_rank: int
    avg_rank: float
    sleeper_id: Optional[str] = None


def parse_adp_file(filename: str = "data") -> List[ADPPlayer]:
    """Parse the ADP data file."""
    players = []

    with open(filename, "r") as f:
        lines = f.readlines()

    # Skip header line
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue

        # Split by tabs
        parts = line.split("\t")
        if len(parts) < 7:
            continue

        # Parse rank
        rank = int(parts[0])

        # Parse player info (name, team, bye)
        player_info = parts[1]
        # Pattern: "Player Name TEAM (BYE)" or just "Player Name" for free agents
        match = re.match(r"(.+?)\s+([A-Z]{2,3})\s+\((\d+)\)", player_info)
        if match:
            name = match.group(1).strip()
            team = match.group(2)
            bye_week = int(match.group(3))
        else:
            # Handle free agents or players without team info
            name = player_info.strip()
            team = "FA"  # Free Agent
            bye_week = 0  # No bye week
            print(f"Parsed as free agent: {name}")

        # Parse position and position rank
        pos_info = parts[2]
        # Pattern: "POS#" like "WR1", "RB2", "QB1"
        pos_match = re.match(r"([A-Z]+)(\d+)", pos_info)
        if pos_match:
            position = pos_match.group(1)
            position_rank = int(pos_match.group(2))
        else:
            position = pos_info
            position_rank = 0

        # Parse rankings from different sources
        yahoo_rank = int(parts[3]) if parts[3].isdigit() else 999
        sleeper_rank = int(parts[4]) if parts[4].isdigit() else 999
        rtsports_rank = int(parts[5]) if parts[5].isdigit() else 999
        avg_rank = float(parts[6]) if len(parts) > 6 else 999.0

        players.append(
            ADPPlayer(
                rank=rank,
                name=name,
                team=team,
                bye_week=bye_week,
                position=position,
                position_rank=position_rank,
                yahoo_rank=yahoo_rank,
                sleeper_rank=sleeper_rank,
                rtsports_rank=rtsports_rank,
                avg_rank=avg_rank,
            )
        )

    return players


def load_sleeper_players() -> Dict:
    """Load Sleeper players database."""
    with open("players.json", "r") as f:
        return json.load(f)


def match_player_to_sleeper(adp_player: ADPPlayer, sleeper_db: Dict) -> Optional[str]:
    """Match an ADP player to a Sleeper player ID."""

    # Handle DST/Defense specially
    if adp_player.position == "DST":
        # Map team names to Sleeper DST IDs
        dst_mappings = {
            "Denver Broncos": "DEN",
            "Philadelphia Eagles": "PHI",
            "Pittsburgh Steelers": "PIT",
            "Baltimore Ravens": "BAL",
            "Minnesota Vikings": "MIN",
            "Buffalo Bills": "BUF",
            "Kansas City Chiefs": "KC",
            "New Orleans Saints": "NO",
            "Houston Texans": "HOU",
            "Cincinnati Bengals": "CIN",
            "Cleveland Browns": "CLE",
            "Seattle Seahawks": "SEA",
            "New York Jets": "NYJ",
            "Green Bay Packers": "GB",
            "Indianapolis Colts": "IND",
            "Los Angeles Chargers": "LAC",
            "San Francisco 49ers": "SF",
            "Chicago Bears": "CHI",
            "Washington Football Team": "WAS",
            "Washington Commanders": "WAS",
            "Tampa Bay Buccaneers": "TB",
            "Dallas Cowboys": "DAL",
            "Detroit Lions": "DET",
            "Miami Dolphins": "MIA",
            "New York Giants": "NYG",
            "Arizona Cardinals": "ARI",
            "Atlanta Falcons": "ATL",
            "Carolina Panthers": "CAR",
            "Jacksonville Jaguars": "JAC",
            "Las Vegas Raiders": "LV",
            "Los Angeles Rams": "LAR",
            "New England Patriots": "NE",
            "Tennessee Titans": "TEN",
        }

        if adp_player.name in dst_mappings:
            return dst_mappings[adp_player.name]

    # Clean up name for matching
    name = adp_player.name.strip()

    # Handle special cases
    name_mappings = {
        "Patrick Mahomes II": "Patrick Mahomes",
        "Aaron Jones Sr.": "Aaron Jones",
        "Deebo Samuel Sr.": "Deebo Samuel",
        "Travis Etienne Jr.": "Travis Etienne",
        "Brian Robinson Jr.": "Brian Robinson",
        "Tyrone Tracy Jr.": "Tyrone Tracy",
        "Marvin Harrison Jr.": "Marvin Harrison",
        "Kenneth Walker III": "Kenneth Walker",
        "Brian Thomas Jr.": "Brian Thomas",
        "Michael Pittman Jr.": "Michael Pittman",
        "Kyle Pitts Sr.": "Kyle Pitts",
        "Luther Burden III": "Luther Burden",
        "Marvin Mims Jr.": "Marvin Mims",
        "Michael Wilson Jr.": "Michael Wilson",
        "Odell Beckham Jr.": "Odell Beckham",
        "Cedric Tillman Jr.": "Cedric Tillman",
        "Roman Wilson Jr.": "Roman Wilson",
        "Keaton Mitchell Jr.": "Keaton Mitchell",
        "Calvin Austin III": "Calvin Austin",
        "Greg Dortch Jr.": "Greg Dortch",
    }

    # Also handle hardcoded player IDs for known mismatches
    direct_id_mappings = {
        ("Michael Pittman Jr.", "WR", "IND"): "6819",
        ("Kyle Pitts Sr.", "TE", "ATL"): "7553",
        ("Luther Burden III", "WR", "CHI"): "12519",
        ("Cam Ward", "QB", "TEN"): "12522",  # Cameron Ward
        ("Michael Penix Jr.", "QB", "ATL"): "11559",
        ("Tre' Harris", "WR", "LAC"): "12509",
        ("Marquise Brown", "WR", "KC"): "5848",  # Hollywood Brown
        ("Anthony Richardson Sr.", "QB", "IND"): "9229",
        ("Dont'e Thornton Jr.", "WR", "LV"): "12541",
        ("Ollie Gordon II", "RB", "MIA"): "12495",
        ("Ray-Ray McCloud III", "WR", "ATL"): "5096",
        ("Harold Fannin Jr.", "TE", "CLE"): "12506",
        ("Efton Chism III", "WR", "NE"): "12542",
        ("Chris Rodriguez Jr.", "RB", "WAS"): "10219",
        ("Oronde Gadsden II", "TE", "LAC"): "12493",
        ("Chris Tyree", "RB", "NO"): "13043",  # Listed as WR in DB but RB in ADP
        # Free agents without team info in ADP data
        ("Zack Moss", "RB", "FA"): "6845",
        ("Amari Cooper", "WR", "FA"): "2309",
    }

    # Check direct mappings first
    key = (adp_player.name, adp_player.position, adp_player.team)
    if key in direct_id_mappings:
        return direct_id_mappings[key]

    if name in name_mappings:
        name = name_mappings[name]

    # Split name into parts
    name_parts = name.split()

    # Try exact match first
    for player_id, player_data in sleeper_db.items():
        first_name = player_data.get("first_name", "")
        last_name = player_data.get("last_name", "")
        player_team = player_data.get("team", "")
        player_position = player_data.get("position", "")

        # Check for exact name match
        full_name = f"{first_name} {last_name}".strip()

        if full_name.lower() == name.lower():
            # Verify team matches (handle team changes)
            if player_team == adp_player.team or not player_team:
                # Verify position matches
                if player_position == adp_player.position:
                    return player_id

    # Try partial matches
    for player_id, player_data in sleeper_db.items():
        first_name = (player_data.get("first_name") or "").lower()
        last_name = (player_data.get("last_name") or "").lower()
        player_team = player_data.get("team", "")
        player_position = player_data.get("position", "")

        # Match by first and last name
        if len(name_parts) >= 2:
            if (
                first_name == name_parts[0].lower()
                and last_name == name_parts[-1].lower()
            ):
                # Verify position
                if player_position == adp_player.position:
                    # Team might not match due to trades/signings
                    return player_id

    return None


def create_rankings_json():
    """Create a JSON file with ADP rankings matched to Sleeper IDs."""

    print("Parsing ADP data...")
    adp_players = parse_adp_file()
    print(f"Found {len(adp_players)} players in ADP data")

    print("Loading Sleeper database...")
    sleeper_db = load_sleeper_players()

    print("Matching players to Sleeper IDs...")
    matched = 0
    unmatched = []

    rankings = []

    for player in adp_players:
        sleeper_id = match_player_to_sleeper(player, sleeper_db)

        if sleeper_id:
            player.sleeper_id = sleeper_id
            matched += 1

            rankings.append(
                {
                    "rank": player.rank,
                    "sleeper_id": sleeper_id,
                    "name": player.name,
                    "team": player.team,
                    "position": player.position,
                    "position_rank": player.position_rank,
                    "bye_week": player.bye_week,
                    "yahoo_rank": player.yahoo_rank,
                    "sleeper_rank": player.sleeper_rank,
                    "rtsports_rank": player.rtsports_rank,
                    "avg_rank": player.avg_rank,
                }
            )
        else:
            unmatched.append(player)

    print(f"\nMatched: {matched}/{len(adp_players)} players")

    if unmatched:
        print("\nUnmatched players:")
        for p in unmatched[:10]:  # Show first 10
            print(f"  - {p.name} ({p.position}, {p.team})")

    # Save rankings to JSON
    with open("adp_rankings.json", "w") as f:
        json.dump(rankings, f, indent=2)

    print("\nSaved rankings to adp_rankings.json")

    return rankings


if __name__ == "__main__":
    rankings = create_rankings_json()

    print("\nTop 10 Players:")
    print("-" * 60)
    for player in rankings[:10]:
        print(
            f"{player['rank']:3}. {player['name']:<25} {player['position']:<4} {player['team']:<4} AVG: {player['avg_rank']:5.1f}"
        )
