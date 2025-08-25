#!/usr/bin/env python3
"""Chopped League Fantasy Football Draft Assistant."""

import argparse
import asyncio
import os
from typing import List

from best_available import format_best_available_summary
from draft_common import (
    analyze_inference_results,
    display_results,
    format_best_available_with_bios,
    get_draft_recommendation,
    load_player_bios,
    render_draft_state,
)
from sleeper_api import SleeperAPI


async def run_multiple_strategies(base_message: str, num_inferences: int) -> List[dict]:
    """Run multiple inferences using different strategy files."""
    print(
        f"\nRunning {num_inferences} inference{'s' if num_inferences > 1 else ''} with different strategies..."
    )

    # Create tasks for all inferences, cycling through strategy files
    tasks = []
    for i in range(num_inferences):
        # Cycle through strategies 1-10
        strategy_num = i + 11
        strategy_file = f"chopped_strategy_{strategy_num}.md"

        # Try to load the strategy file
        try:
            with open(strategy_file, "r") as f:
                strategy_content = f.read()
            print(f"[Inference {i+1}] Using strategy: {strategy_file}")
        except FileNotFoundError:
            print(
                f"[Inference {i+1}] Warning: {strategy_file} not found, using default"
            )
            # Fall back to default strategy
            try:
                with open("chopped_league_strategy_v3.md", "r") as f:
                    strategy_content = f.read()
                strategy_file = "chopped_league_strategy_v3.md"
            except FileNotFoundError:
                print(f"[Inference {i+1}] Error: No strategy files found")
                continue

        # Build the full message with this strategy
        full_message = (
            "# CHOPPED LEAGUE DRAFT - ELIMINATION FORMAT\n\n"
            "## CRITICAL: This is a SURVIVAL league where the LOWEST scoring team each week is ELIMINATED.\n\n"
            + strategy_content
            + "\n\n"
            + base_message
        )

        # Create the task
        task = get_draft_recommendation(full_message, i + 1, strategy_file)
        tasks.append(task)

    if not tasks:
        return []

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
                    "strategy_used": f"chopped_strategy_{(i % 10) + 1}.md",
                }
            )
        else:
            processed_results.append(result)  # type: ignore[arg-type]

    return processed_results


async def main():
    """Main async function to handle draft recommendations for chopped leagues."""
    parser = argparse.ArgumentParser(
        description="AI Fantasy Football Draft Assistant - Chopped League"
    )
    parser.add_argument("draft_id", help="Sleeper draft ID")
    parser.add_argument(
        "--inferences",
        type=int,
        default=1,
        help="Number of parallel inferences to run (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show all inference responses, not just consensus",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="chopped_league_strategy_v3.md",
        help="Path to strategy markdown file (default: chopped_league_strategy_v3.md)",
    )

    args = parser.parse_args()

    draft_id = args.draft_id
    num_inferences = args.inferences
    verbose = args.verbose
    player_id = os.getenv("PLAYER_ID")

    if not player_id:
        print("ERROR: PLAYER_ID environment variable not set")
        return

    # Load player bios
    player_bios = load_player_bios()

    # Get draft state
    api = SleeperAPI()
    picks = api.get_draft_picks(draft_id)
    state = render_draft_state(player_id, draft_id, "chopped")

    # Get best available analysis with detailed bios
    if player_bios:
        best_available_summary = format_best_available_with_bios(
            picks, player_id, player_bios
        )
    else:
        # Fallback to basic summary if no bios available
        best_available_summary = format_best_available_summary(picks, player_id)
        print("Warning: No player bios found, using basic format")

    # Create base message template
    base_message = (
        "# Current Team:\n\n"
        + state.get(player_id, "")
        + best_available_summary
        + "\n\n## DRAFT DECISION REQUIRED\n\n"
        + "Based on the CHOPPED LEAGUE ELIMINATION strategy above and the detailed player analyses, who should I draft next?\n\n"
        + "**SURVIVAL CRITICAL FACTORS:**\n"
        + "1. Will this player help AVOID ELIMINATION in Weeks 1-4?\n"
        + "2. Do they have a SAFE WEEKLY FLOOR (10+ points minimum)?\n"
        + "3. Are they a PROVEN, CONSISTENT performer?\n"
        + "4. Do they fit the ANTI-ELIMINATION strategy?\n\n"
        + "**REMEMBER:** In Chopped leagues, one bad week = ELIMINATION. Prioritize SURVIVAL over upside!\n\n"
        + "Consider the player's FLOOR, consistency, and early-season schedule. "
        + "Give your final selection in [[Player Name]] format."
    )

    # Run multiple inferences with different strategies
    results = await run_multiple_strategies(base_message, num_inferences)

    # Analyze results
    analysis = analyze_inference_results(results)

    # Display results
    display_results(analysis, results, verbose)


if __name__ == "__main__":
    asyncio.run(main())
