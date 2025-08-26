#!/usr/bin/env python3
"""Standard Fantasy Football Draft Assistant."""

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
    """Main async function to handle draft recommendations for standard leagues."""
    parser = argparse.ArgumentParser(
        description="AI Fantasy Football Draft Assistant - Standard League"
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

    # Load standard league strategy
    with open("standard_league_strategy.md", "r") as f:
        standard_strategy = f.read()

    # Get draft state
    api = SleeperAPI()
    picks = api.get_draft_picks(draft_id)
    state = render_draft_state(player_id, draft_id, "standard")

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
        "# 🚨 LIVE DRAFT - MY PICK IS NOW! 🚨\n\n"
        + "I am currently on the clock in a LIVE DRAFT. I need to make my selection IMMEDIATELY.\n"
        + "All players shown as available ARE currently available - no one else can pick before me.\n"
        + "This is MY TURN to pick RIGHT NOW.\n\n"
        + "# STANDARD FANTASY FOOTBALL DRAFT\n\n"
        + standard_strategy
        + "\n\n"
        + "# Current Team:\n\n"
        + state.get(player_id, "")
        + best_available_summary
        + "\n\n## IMMEDIATE DRAFT DECISION REQUIRED\n\n"
        + "**IMPORTANT: Please use web search to find the most current 2025 NFL information including:**\n"
        + "- Recent injuries, health updates, or player status changes\n"
        + "- Current team depth charts and projected roles\n"
        + "- Training camp reports and preseason performance\n"
        + "- Offensive line changes or coaching system updates\n"
        + "- Any breaking news affecting player fantasy value\n\n"
        + "Based on the Standard League strategy above, the detailed player analyses, "
        + "and CURRENT WEB INFORMATION, who should I draft with THIS PICK?\n\n"
        + "**Key Considerations:**\n"
        + "1. Best player available vs positional need\n"
        + "2. Balance of floor and ceiling for roster construction\n"
        + "3. Full season value including playoff weeks\n"
        + "4. Positional scarcity in 13-team league\n"
        + "5. Recent developments that affect player rankings\n\n"
        + "**REMEMBER:**\n"
        + "- This is a LIVE DRAFT - I need your pick NOW\n"
        + "- All listed players ARE available for me to pick\n"
        + "- No one can 'snipe' these players - it's MY turn\n\n"
        + "Use web search to quickly verify current player situations, then give me the BEST PICK "
        + "from the AVAILABLE PLAYERS shown above. "
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
