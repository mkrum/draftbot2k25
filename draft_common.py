"""Common functions for draft assistants."""

import asyncio
import glob
import json
import re
from typing import Dict, List, Optional

from openai import AsyncOpenAI

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


def parse_draft_selection(response_content: str) -> Optional[str]:
    """Parse the AI response to extract the draft selection from [[]] brackets."""
    # Look for text inside double brackets [[]]
    match = re.search(r"\[\[(.*?)\]\]", response_content)
    if match:
        selection = match.group(1).strip()
        return selection
    return None


async def get_draft_recommendation(message: str, inference_id: int = 1) -> dict:
    """Get a single draft recommendation from the AI."""
    try:
        print(f"[Inference {inference_id}] Starting analysis...")

        client = AsyncOpenAI()
        response = await client.responses.create(
            model="gpt-5",
            reasoning={"effort": "high"},
            tools=[{"type": "web_search_preview"}],
            input=message,
        )

        response_content = response.output_text
        selection = parse_draft_selection(response_content)

        print(
            f"[Inference {inference_id}] Completed - Pick: {selection or 'FAILED TO PARSE'}"
        )

        return {
            "inference_id": inference_id,
            "full_response": response_content,
            "parsed_selection": selection,
            "success": selection is not None,
        }

    except Exception as e:
        print(f"[Inference {inference_id}] Error: {e}")
        return {
            "inference_id": inference_id,
            "full_response": f"Error: {e}",
            "parsed_selection": None,
            "success": False,
            "error": str(e),
        }


async def run_multiple_inferences(message: str, num_inferences: int = 1) -> List[dict]:
    """Run multiple AI inferences in parallel."""
    print(f"\nRunning {num_inferences} inference{'s' if num_inferences > 1 else ''}...")

    # Create tasks for all inferences
    tasks = [get_draft_recommendation(message, i + 1) for i in range(num_inferences)]

    # Run all inferences concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions
    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                {
                    "inference_id": i + 1,
                    "full_response": f"Exception: {result}",
                    "parsed_selection": None,
                    "success": False,
                    "error": str(result),
                }
            )
        else:
            processed_results.append(result)  # type: ignore[arg-type]

    return processed_results


def analyze_inference_results(results: List[dict]) -> dict:
    """Analyze results from multiple inferences."""
    successful_results = [r for r in results if r["success"]]

    if not successful_results:
        return {
            "consensus_pick": None,
            "confidence": 0,
            "picks_count": {},
            "total_inferences": len(results),
            "successful_inferences": 0,
        }

    # Count occurrences of each pick
    picks_count: Dict[str, int] = {}
    for result in successful_results:
        pick = result["parsed_selection"]
        picks_count[pick] = picks_count.get(pick, 0) + 1

    # Find the most common pick
    consensus_pick = max(picks_count.items(), key=lambda x: x[1])
    confidence = consensus_pick[1] / len(successful_results)

    return {
        "consensus_pick": consensus_pick[0],
        "confidence": confidence,
        "picks_count": picks_count,
        "total_inferences": len(results),
        "successful_inferences": len(successful_results),
    }


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
    best_by_position = ba.get_best_available_by_position(taken_ids, limit=10)

    # Format the summary
    summary = "\n## CURRENT ROSTER\n"
    for pos, count in current_roster.items():
        summary += f"{pos}: {count} | "
    summary = summary.rstrip(" | ")

    summary += "\n\n## BEST AVAILABLE PLAYERS\n\n"

    # Create detailed sections for each position
    priority_positions = ["QB", "RB", "WR", "TE"]

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


def make_team_table(picks: List[DraftPickData], league_type: str = "standard") -> str:
    team_table = "## Starters\n"

    if league_type == "chopped":
        # Chopped: 1QB, 2RB, 3WR, 1TE, 2FLEX, no K/DEF
        pos = ["QB", "RB1", "RB2", "WR1", "WR2", "WR3", "TE", "FLEX1", "FLEX2"]
    else:
        # Standard: 1QB, 2RB, 2WR, 1TE, 1FLEX, 1REC_FLEX, 1SUPER_FLEX, 1K, 1DEF
        pos = [
            "QB",
            "RB1",
            "RB2",
            "WR1",
            "WR2",
            "TE",
            "FLEX",
            "REC_FLEX",
            "SUPER_FLEX",
            "K",
            "DEF",
        ]

    bench: List[DraftPickData] = []

    team_map: Dict[str, Optional[DraftPickData]] = {p: None for p in pos}
    for p in picks:
        if not p.metadata:
            bench.append(p)
            continue

        position = p.metadata.position

        if league_type == "chopped":
            # Chopped league logic: 1QB, 2RB, 3WR, 1TE, 2FLEX
            if position == "QB":
                if not team_map["QB"]:
                    team_map["QB"] = p
                else:
                    bench.append(p)
            elif position == "RB":
                if not team_map["RB1"]:
                    team_map["RB1"] = p
                elif not team_map["RB2"]:
                    team_map["RB2"] = p
                elif not team_map["FLEX1"]:
                    team_map["FLEX1"] = p
                elif not team_map["FLEX2"]:
                    team_map["FLEX2"] = p
                else:
                    bench.append(p)
            elif position == "WR":
                if not team_map["WR1"]:
                    team_map["WR1"] = p
                elif not team_map["WR2"]:
                    team_map["WR2"] = p
                elif not team_map["WR3"]:
                    team_map["WR3"] = p
                elif not team_map["FLEX1"]:
                    team_map["FLEX1"] = p
                elif not team_map["FLEX2"]:
                    team_map["FLEX2"] = p
                else:
                    bench.append(p)
            elif position == "TE":
                if not team_map["TE"]:
                    team_map["TE"] = p
                elif not team_map["FLEX1"]:
                    team_map["FLEX1"] = p
                elif not team_map["FLEX2"]:
                    team_map["FLEX2"] = p
                else:
                    bench.append(p)
            else:
                bench.append(p)
        else:
            # Standard league logic: 1QB, 2RB, 2WR, 1TE, 1FLEX, 1REC_FLEX, 1SUPER_FLEX, 1K, 1DEF
            if position == "QB":
                if not team_map["QB"]:
                    team_map["QB"] = p
                elif not team_map["SUPER_FLEX"]:
                    team_map["SUPER_FLEX"] = p
                else:
                    bench.append(p)
            elif position == "RB":
                if not team_map["RB1"]:
                    team_map["RB1"] = p
                elif not team_map["RB2"]:
                    team_map["RB2"] = p
                elif not team_map["FLEX"]:
                    team_map["FLEX"] = p
                elif not team_map["SUPER_FLEX"]:
                    team_map["SUPER_FLEX"] = p
                else:
                    bench.append(p)
            elif position == "WR":
                if not team_map["WR1"]:
                    team_map["WR1"] = p
                elif not team_map["WR2"]:
                    team_map["WR2"] = p
                elif not team_map["REC_FLEX"]:
                    team_map["REC_FLEX"] = p
                elif not team_map["FLEX"]:
                    team_map["FLEX"] = p
                elif not team_map["SUPER_FLEX"]:
                    team_map["SUPER_FLEX"] = p
                else:
                    bench.append(p)
            elif position == "TE":
                if not team_map["TE"]:
                    team_map["TE"] = p
                elif not team_map["REC_FLEX"]:
                    team_map["REC_FLEX"] = p
                elif not team_map["FLEX"]:
                    team_map["FLEX"] = p
                elif not team_map["SUPER_FLEX"]:
                    team_map["SUPER_FLEX"] = p
                else:
                    bench.append(p)
            elif position == "K":
                if not team_map["K"]:
                    team_map["K"] = p
                else:
                    bench.append(p)
            elif position == "DEF":
                if not team_map["DEF"]:
                    team_map["DEF"] = p
                else:
                    bench.append(p)
            else:
                bench.append(p)

    for position in pos:
        player = team_map[position]
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
        team_table += f"| {position} | {name} | {team} | \n"

    while len(bench) < 5:
        bench.append(None)  # type: ignore[arg-type]

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


def render_draft_state(
    player_id: str, draft_id: str, league_type: str = "standard"
) -> Dict[str, str]:
    api = SleeperAPI()
    picks = api.get_draft_picks(draft_id)

    player_ids: set[str] = set(p.picked_by for p in picks if p.picked_by)
    teams: Dict[str, str] = {}

    for pid in player_ids:
        player_picks = [p for p in picks if p.picked_by == pid]
        teams[pid] = make_team_table(player_picks, league_type)

    return teams


def display_results(analysis: dict, results: List[dict], verbose: bool):
    """Display inference results."""
    print("\n" + "=" * 80)
    print("DRAFT RECOMMENDATION RESULTS")
    print("=" * 80)

    if analysis["consensus_pick"]:
        print(f"🎯 CONSENSUS PICK: {analysis['consensus_pick']}")
        print(
            f"📊 CONFIDENCE: {analysis['confidence']:.1%} ({analysis['picks_count'][analysis['consensus_pick']]}/{analysis['successful_inferences']} votes)"
        )

        if len(analysis["picks_count"]) > 1:
            print("\n📈 ALL PICKS:")
            sorted_picks = sorted(
                analysis["picks_count"].items(), key=lambda x: x[1], reverse=True
            )
            for pick, count in sorted_picks:
                percentage = count / analysis["successful_inferences"]
                print(f"  • {pick}: {count} votes ({percentage:.1%})")
    else:
        print("❌ NO CONSENSUS: All inferences failed to produce valid picks")

    print(
        f"\n✅ Success Rate: {analysis['successful_inferences']}/{analysis['total_inferences']}"
    )

    # Show detailed responses if verbose or if there were multiple different picks
    if verbose or (analysis["consensus_pick"] and len(analysis["picks_count"]) > 1):
        print("\n" + "=" * 80)
        print("DETAILED INFERENCE RESPONSES")
        print("=" * 80)

        for result in results:
            print(f"\n--- Inference {result['inference_id']} ---")
            if result["success"]:
                print(f"Pick: {result['parsed_selection']}")
                if verbose:
                    print("Full Response:")
                    print(result["full_response"])
            else:
                print(f"Failed: {result.get('error', 'Unknown error')}")

    print("=" * 80)
