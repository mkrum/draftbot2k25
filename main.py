import glob
import json
import os
import re
import sys
from typing import Dict, List, Optional

from litellm import completion

from best_available import format_best_available_summary
from sleeper_api import DraftPickData, SleeperAPI


def load_player_bios() -> Dict[str, dict]:
    """Load player analysis data from the most recent analysis file."""
    # Find the most recent player analysis file
    analysis_files = glob.glob("player_analyses_*.json")
    if not analysis_files:
        return {}

    # Get the most recent file by sorting by name (timestamp in filename)
    latest_file = sorted(analysis_files)[-1]

    try:
        with open(latest_file, "r") as f:
            analyses = json.load(f)

        # Create a lookup by sleeper_id
        bios = {}
        for analysis in analyses:
            if "sleeper_id" in analysis and "error" not in analysis:
                bios[analysis["sleeper_id"]] = analysis

        print(f"Loaded {len(bios)} player bios from {latest_file}")
        return bios
    except Exception as e:
        print(f"Error loading player bios: {e}")
        return {}


def remove_sources(text: str) -> str:
    """Remove source citations from text using regex."""
    # Remove markdown links like ([domain.com](url))
    text = re.sub(r"\s*\(\[[\w\.-]+\]\([^)]+\)\)", "", text)
    # Remove any remaining parenthetical citations
    text = re.sub(r"\s*\([^)]*(?:\.com|\.org|\.net)[^)]*\)", "", text)
    return text.strip()


def format_player_bio(analysis: dict) -> str:
    """Format a single player's analysis into a readable bio."""
    if "error" in analysis:
        return f"**{analysis['player_name']}** - Analysis unavailable"

    bio = (
        f"**{analysis['player_name']} ({analysis['position']}, {analysis['team']})**\n"
    )
    bio += f"*ADP Rank: {analysis['rank']} | Position Rank: {analysis['position']}{analysis['position_rank']}*\n\n"

    # Add summary (remove sources)
    if analysis.get("summary"):
        clean_summary = remove_sources(analysis["summary"])
        bio += f"{clean_summary}\n\n"

    # Add bull case (limit to top 2 points for brevity)
    if analysis.get("bull_case"):
        bio += "**Strengths:**\n"
        for point in analysis["bull_case"][:2]:
            clean_point = remove_sources(point)
            bio += f"• {clean_point}\n"
        bio += "\n"

    # Add bear case (limit to top 2 points for brevity)
    if analysis.get("bear_case"):
        bio += "**Concerns:**\n"
        for point in analysis["bear_case"][:2]:
            clean_point = remove_sources(point)
            bio += f"• {clean_point}\n"
        bio += "\n"

    # Add bottom line (remove sources)
    if analysis.get("bottom_line"):
        clean_bottom_line = remove_sources(analysis["bottom_line"])
        bio += f"**Bottom Line:** {clean_bottom_line}\n"

    return bio


def format_best_available_with_bios(
    draft_picks, player_slot: str, player_bios: Dict[str, dict]
) -> str:
    """Create a summary of best available players with detailed bios."""
    from best_available import BestAvailable

    ba = BestAvailable()
    taken_ids = ba.get_taken_player_ids(draft_picks)

    # Get current player's picks
    current_picks = [p for p in draft_picks if p.picked_by == player_slot]

    # Analyze current roster
    current_roster = ba.analyze_current_roster(current_picks)

    # Get best available by position (limit to 3 for detailed bios)
    best_by_position = ba.get_best_available_by_position(taken_ids, limit=3)

    # Format the summary
    summary = "\n## CURRENT ROSTER\n"
    for pos, count in current_roster.items():
        summary += f"{pos}: {count} | "
    summary = summary.rstrip(" | ")

    summary += "\n\n## BEST AVAILABLE PLAYERS\n\n"

    # Create detailed sections for each position
    priority_positions = ["QB", "RB", "WR", "TE", "K", "DST"]

    for pos in priority_positions:
        if pos in best_by_position and best_by_position[pos]:
            players = best_by_position[pos]

            summary += f"### {pos}\n\n"

            for player in players:
                # Try to get detailed bio, fall back to basic info
                if player.sleeper_id in player_bios:
                    summary += format_player_bio(player_bios[player.sleeper_id]) + "\n"
                else:
                    # Fallback to basic player info
                    summary += f"**{player.name} ({player.position}, {player.team})**\n"
                    summary += f"*ADP Rank: {player.rank} | Position Rank: {player.position}{player.position_rank}*\n\n"

                summary += "---\n\n"

    return summary


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

    player_ids: set[str] = set(p.picked_by for p in picks if p.picked_by)
    teams: Dict[str, str] = {}

    for pid in player_ids:
        player_picks = [p for p in picks if p.picked_by == pid]
        teams[pid] = make_team_table(player_picks)

    return teams


if __name__ == "__main__":
    draft_id = sys.argv[1]
    player_id = os.getenv("PLAYER_ID")

    # Load player bios
    player_bios = load_player_bios()

    # Get draft state
    api = SleeperAPI()
    picks = api.get_draft_picks(draft_id)
    state = render_draft_state(player_id, draft_id)

    # Get best available analysis with detailed bios
    if player_bios:
        best_available_summary = format_best_available_with_bios(
            picks, player_id, player_bios
        )
    else:
        # Fallback to basic summary if no bios available
        best_available_summary = format_best_available_summary(picks, player_id)
        print("Warning: No player bios found, using basic format")

    message = (
        "# Current Team:\n\n"
        + state.get(player_id, "")
        + best_available_summary
        + "\n\nBased on the detailed player analyses above, who should I draft next in my Fantasy Football league? Consider each player's strengths, concerns, and fit with my current roster needs. Give a final selection in [[]], so it can be easily parsed."
    )

    print(message)
    response = completion(
        model="openai/gpt-5",
        messages=[
            {
                "role": "user",
                "content": message,
            }
        ],
        # web_search_options={
        #    "search_context_size": "high"  # Options: "low", "medium", "high"
        # },
    )

    print(response)
