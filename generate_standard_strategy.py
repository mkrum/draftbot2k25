#!/usr/bin/env python3
"""Generate an improved Standard League strategy using GPT-5 with high reasoning."""

from openai import OpenAI


def generate_standard_strategy():
    """Generate a new standard league strategy using GPT-5."""

    prompt = """You are an expert fantasy football strategist tasked with creating the ultimate draft strategy for a complex standard fantasy football league.

## League Context:
- **Format**: Season-long standard fantasy football (no eliminations)
- **12 Teams**: Standard league size
- **Roster**: 1QB, 2RB, 2WR, 1TE, 1FLEX, 1REC_FLEX, 1SUPER_FLEX, 1K, 1DEF, 5BN
- **Scoring**: Half-PPR (0.5 per reception)
- **Snake Draft**: Multiple rounds
- **Playoffs**: Top teams make playoffs (weeks 15-17)

## Unique Roster Requirements:
1. **FLEX** (RB/WR/TE): Standard flex position
2. **REC_FLEX** (WR/TE only): Receiving-focused flex
3. **SUPER_FLEX** (QB/RB/WR/TE): Can start a second QB here
4. **Kicker and Defense**: Traditional positions required

## Key Strategic Considerations:
1. **Super Flex Impact**: Essentially a 2QB league - QB scarcity is critical
2. **Receiving Flex**: WR/TE depth becomes more valuable
3. **Full Season Value**: Must plan for 17+ weeks including playoffs
4. **Balanced Roster**: Need depth across all positions including K/DEF
5. **Playoff Focus**: Weeks 15-17 schedules and matchups matter

## Your Task:
Create a comprehensive, strategic guide that addresses:

1. **Core Philosophy**: How does SUPER_FLEX change everything?
2. **Quarterback Strategy**: When and how many QBs to draft
3. **Positional Priorities**: Balancing FLEX, REC_FLEX, and SUPER_FLEX
4. **Round-by-Round Strategy**: Specific approach for each round range
5. **Player Archetypes**: Who to target/avoid with examples
6. **Roster Construction**: Optimal player distribution
7. **Bye Week Management**: Planning for full season
8. **Playoff Preparation**: Late-season considerations
9. **Kicker/Defense Strategy**: When and how to approach these positions
10. **Trade Considerations**: Building for in-season moves
11. **Depth vs Stars**: Balance for 12-team competition
12. **Risk Management**: Injury and bust protection

Think deeply about:
- How SUPER_FLEX fundamentally changes draft values
- The mathematics of QB scarcity in a 12-team league
- Optimal timing for each position
- How REC_FLEX affects WR/TE values
- Playoff schedule strength analysis
- When to prioritize ceiling vs floor

Consider scenarios like:
- What if you don't get a second starting QB?
- How does draft position affect QB strategy?
- Should you ever start a non-QB in SUPER_FLEX?
- How much should playoff matchups influence draft day?

Create a strategy that maximizes championship probability through optimal roster construction and value extraction.

Format as a comprehensive markdown guide that can be used during live drafts."""

    client = OpenAI()

    print("Generating improved Standard League strategy with GPT-5 high reasoning...")
    print("This may take a while due to high reasoning effort...")

    response = client.responses.create(
        model="gpt-5",
        reasoning={"effort": "high"},
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )

    strategy_content = response.output_text

    # Save the new strategy
    output_file = "standard_league_strategy_v2.md"
    with open(output_file, "w") as f:
        f.write(strategy_content)

    print(f"\n✅ New strategy generated and saved to: {output_file}")
    print(f"Strategy length: {len(strategy_content)} characters")

    # Show a preview
    lines = strategy_content.split("\n")
    print("\n📋 Preview (first 20 lines):")
    print("-" * 50)
    for line in lines[:20]:
        print(line)
    if len(lines) > 20:
        print("...")
    print("-" * 50)


if __name__ == "__main__":
    generate_standard_strategy()
