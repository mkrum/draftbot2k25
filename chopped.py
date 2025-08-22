#!/usr/bin/env python3
"""Chopped League Fantasy Football Draft Assistant."""

import argparse
import asyncio
import os

from best_available import format_best_available_summary
from draft_common import (
    analyze_inference_results,
    display_results,
    format_best_available_with_bios,
    load_player_bios,
    render_draft_state,
    run_multiple_inferences,
)
from sleeper_api import SleeperAPI


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

    # Load chopped league strategy
    with open("chopped_league_strategy.md", "r") as f:
        chopped_strategy = f.read()

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
        "# CHOPPED LEAGUE DRAFT - ELIMINATION FORMAT\n\n"
        "## CRITICAL: This is a SURVIVAL league where the LOWEST scoring team each week is ELIMINATED.\n\n"
        + chopped_strategy
        + "\n\n"
        + "# Current Team:\n\n"
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

    print(message)
    print("\n" + "=" * 80)

    # Run multiple inferences
    results = await run_multiple_inferences(message, num_inferences)

    # Analyze results
    analysis = analyze_inference_results(results)

    # Display results
    display_results(analysis, results, verbose)


if __name__ == "__main__":
    asyncio.run(main())
