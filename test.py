import argparse
import re
from typing import List, Optional

from litellm import completion
from pydantic import BaseModel

# Constants
DEFAULT_NUM_PLAYERS = 10
DEFAULT_MAX_RETRIES = 3
MODEL_NAME = "openai/gpt-4o-search-preview"


class PlayerAnalysis(BaseModel):
    player_name: str
    summary: str
    bull_case: List[str]
    bear_case: List[str]
    bottom_line: str


def parse_player_analysis(response_text: str) -> Optional[PlayerAnalysis]:
    """Parse the LLM response into a structured PlayerAnalysis object."""

    # Clean up the response text
    text = response_text.strip()

    # Extract player name (# Player Name)
    name_match = re.search(r"^#\s+(.+?)$", text, re.MULTILINE)
    if not name_match:
        return None
    player_name = name_match.group(1).strip()

    # Extract summary (text between player name and ## Bull Case)
    summary_pattern = r"^#\s+.+?\n\n(.*?)(?=##\s+Bull Case)"
    summary_match = re.search(summary_pattern, text, re.DOTALL | re.MULTILINE)
    summary = summary_match.group(1).strip() if summary_match else ""

    # Extract Bull Case bullet points
    bull_case_pattern = r"##\s+Bull Case\s*\n(.*?)(?=##\s+Bear Case)"
    bull_case_match = re.search(bull_case_pattern, text, re.DOTALL)
    bull_case = []
    if bull_case_match:
        bull_text = bull_case_match.group(1)
        # Find all bullet points (- followed by text)
        bull_points = re.findall(r"^-\s+(.+?)$", bull_text, re.MULTILINE)
        bull_case = [point.strip() for point in bull_points]

    # Extract Bear Case bullet points
    bear_case_pattern = r"##\s+Bear Case\s*\n(.*?)(?=##\s+Bottom Line)"
    bear_case_match = re.search(bear_case_pattern, text, re.DOTALL)
    bear_case = []
    if bear_case_match:
        bear_text = bear_case_match.group(1)
        # Find all bullet points (- followed by text)
        bear_points = re.findall(r"^-\s+(.+?)$", bear_text, re.MULTILINE)
        bear_case = [point.strip() for point in bear_points]

    # Extract Bottom Line
    bottom_line_pattern = r"##\s+Bottom Line\s*\n(.*?)$"
    bottom_line_match = re.search(bottom_line_pattern, text, re.DOTALL)
    bottom_line = bottom_line_match.group(1).strip() if bottom_line_match else ""

    # Create and return the structured object
    return PlayerAnalysis(
        player_name=player_name,
        summary=summary,
        bull_case=bull_case,
        bear_case=bear_case,
        bottom_line=bottom_line,
    )


RESPONSE_FORMAT = """
# Player Name

Brief summary of their 2025 fantasy outlook.

## Bull Case
- Key reasons to draft this player
- What could go right

## Bear Case
- Key concerns or risks
- What could go wrong

## Bottom Line
Draft recommendation and target round.
"""


def create_player_prompt(name: str, position: str, team: str) -> str:
    """Create analysis prompt for a specific player."""
    return f"""
You are a fantasy football expert analyzing players for a 12-team, 2QB, half-PPR league draft.

Research everything relevant about this player's 2025 fantasy football outlook. Focus on information that would
actually influence a draft decision - things like projected role, opportunity, efficiency, health, competition,
team changes, etc.

Find the most important and current information available. Present both the optimistic case for drafting them and
the realistic concerns.

Use this format: ```{RESPONSE_FORMAT}```

Player: {name}, {position}, {team}
"""


def get_player_analysis_with_retry(
    prompt: str, max_retries: int = DEFAULT_MAX_RETRIES
) -> Optional[PlayerAnalysis]:
    """Get player analysis with retry logic if parsing fails."""

    for attempt in range(max_retries):
        print(f"\nAttempt {attempt + 1}/{max_retries}...")

        try:
            response = completion(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            prompt
                            if attempt == 0
                            else f"{prompt}\n\nIMPORTANT: Please follow the exact format specified above with proper markdown headers (# and ##) and bullet points (-)."
                        ),
                    }
                ],
                web_search_options={"search_context_size": "high"},
            )

            content = response.choices[0].message.content
            print(f"Raw response length: {len(content)} characters")

            parsed = parse_player_analysis(content)
            if parsed:
                print(f"Successfully parsed on attempt {attempt + 1}")
                return parsed
            else:
                print(f"Failed to parse attempt {attempt + 1}")
                print("Raw response preview:")
                print(content[:500] + "..." if len(content) > 500 else content)

        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")

    return None


def create_success_result(player: dict, parsed: PlayerAnalysis) -> dict:
    """Create a successful analysis result."""
    from datetime import datetime

    return {
        "rank": player["rank"],
        "sleeper_id": player["sleeper_id"],
        "player_name": parsed.player_name,
        "position": player["position"],
        "team": player["team"],
        "position_rank": player["position_rank"],
        "bye_week": player["bye_week"],
        "yahoo_rank": player["yahoo_rank"],
        "sleeper_rank": player["sleeper_rank"],
        "rtsports_rank": player["rtsports_rank"],
        "avg_rank": player["avg_rank"],
        "summary": parsed.summary,
        "bull_case": parsed.bull_case,
        "bear_case": parsed.bear_case,
        "bottom_line": parsed.bottom_line,
        "timestamp": datetime.now().isoformat(),
    }


def create_error_result(player: dict) -> dict:
    """Create a failed analysis result."""
    from datetime import datetime

    return {
        "rank": player["rank"],
        "sleeper_id": player["sleeper_id"],
        "player_name": player["name"],
        "position": player["position"],
        "team": player["team"],
        "position_rank": player["position_rank"],
        "bye_week": player["bye_week"],
        "yahoo_rank": player["yahoo_rank"],
        "sleeper_rank": player["sleeper_rank"],
        "rtsports_rank": player["rtsports_rank"],
        "avg_rank": player["avg_rank"],
        "error": "Failed to parse analysis",
        "timestamp": datetime.now().isoformat(),
    }


def analyze_top_players(resume_from_file=None, num_players=DEFAULT_NUM_PLAYERS):
    """
    Analyze top players from ADP rankings and save results.

    Args:
        resume_from_file: Path to existing JSON file to resume from
        num_players: Number of top players to analyze (default 10)
    """
    import json
    import os
    from datetime import datetime

    # Load ADP rankings
    with open("adp_rankings.json", "r") as f:
        rankings = json.load(f)

    # Get top N players
    top_players = rankings[:num_players]

    # Load existing results if resuming
    results = []
    analyzed_players = set()

    if resume_from_file and os.path.exists(resume_from_file):
        print(f"Resuming from existing file: {resume_from_file}")
        with open(resume_from_file, "r") as f:
            results = json.load(f)

        # Track which players we've already analyzed
        for result in results:
            if "error" not in result:
                # Use name + position + team as unique identifier
                player_key = f"{result.get('player_name', '')}_{result.get('position', '')}_{result.get('team', '')}"
                analyzed_players.add(player_key)

        print(f"Found {len(analyzed_players)} already analyzed players")
        output_file = resume_from_file
    else:
        output_file = f"player_analyses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        print(f"Starting fresh analysis, will save to: {output_file}")

    # Analyze each player
    for i, player in enumerate(top_players, 1):
        player_key = f"{player['name']}_{player['position']}_{player['team']}"

        if player_key in analyzed_players:
            print(f"\n[{i}/{num_players}] Skipping {player['name']} - already analyzed")
            continue

        print(f"\n{'='*60}")
        print(
            f"Analyzing {i}/{num_players}: {player['name']} ({player['position']}, {player['team']})"
        )
        print(f"ADP Rank: {player['rank']}")
        print(f"{'='*60}")

        # Create prompt for this player
        player_prompt = create_player_prompt(
            player["name"], player["position"], player["team"]
        )

        # Get analysis with retry
        parsed = get_player_analysis_with_retry(player_prompt, max_retries=5)

        if parsed:
            result = create_success_result(player, parsed)
            results.append(result)
            print(f"SUCCESS - Analysis saved for {player['name']}")
        else:
            print(f"FAILED - Could not analyze {player['name']}")
            result = create_error_result(player)
            results.append(result)

    # Save results to JSON
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*60}")
    print("Analysis complete!")
    print(
        f"Successfully analyzed: {sum(1 for r in results if 'error' not in r)}/{len(results)} players"
    )
    print(f"Results saved to: {output_file}")
    print(f"{'='*60}")

    return results


# Run the analysis
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze top fantasy football players")
    parser.add_argument("--resume", type=str, help="Resume from existing JSON file")
    parser.add_argument(
        "--num-players",
        type=int,
        default=DEFAULT_NUM_PLAYERS,
        help=f"Number of top players to analyze (default: {DEFAULT_NUM_PLAYERS})",
    )

    args = parser.parse_args()

    results = analyze_top_players(
        resume_from_file=args.resume, num_players=args.num_players
    )
