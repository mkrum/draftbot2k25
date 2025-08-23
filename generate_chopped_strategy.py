#!/usr/bin/env python3
"""Generate an improved Chopped League strategy using GPT-5 with high reasoning."""

from openai import OpenAI


def generate_chopped_strategy():
    """Generate a new chopped league strategy using GPT-5."""

    prompt = """You are an expert fantasy football strategist tasked with creating the ultimate draft strategy for a "Chopped" elimination league format.

## League Context:
- **Format**: Weekly elimination - LOWEST scoring team each week is ELIMINATED
- **13 Teams**: Competition starts with 13 teams
- **Roster**: 1QB, 2RB, 3WR, 1TE, 2FLEX, 6BN (No K/DEF)
- **Scoring**: Half-PPR (0.5 per reception)
- **Snake Draft**: 15 rounds
- **Critical Point**: You CANNOT win if you're eliminated. Survival is everything.

## Key Considerations:
1. **Elimination Risk**: One bad week = you're out. All your players go to waivers.
2. **Waiver Additions**: Every week, eliminated teams' players become available.
3. **Early Season Critical**: Weeks 1-6 are most dangerous (most eliminations).
4. **Floor vs Ceiling**: Consistent 100+ points > boom/bust 140 or 60 points.
5. **Position Scarcity**: 13 teams = less depth available than standard leagues.

## Your Task:
Create a comprehensive, strategic guide that addresses:

1. **Core Philosophy**: What fundamental principles should guide every draft decision?
2. **Round-by-Round Strategy**: Specific approach for rounds 1-15
3. **Positional Priorities**: How to balance 3WR + 2FLEX requirements
4. **Player Archetypes**: Specific types to target/avoid with examples
5. **Risk Management**: How to minimize elimination risk
6. **Waiver Strategy**: How the weekly additions affect draft approach
7. **Bye Week Planning**: Critical timing considerations
8. **Late-Round Strategy**: Maximizing final picks for survival
9. **Anti-Elimination Tactics**: Specific techniques to avoid being lowest scorer
10. **Week 1-4 Survival Plan**: Concrete steps for early season safety

Think deeply about the mathematical probability of elimination, the psychology of risk-averse vs aggressive drafting, and the unique dynamics of expanding player pools.

Consider edge cases like:
- What if multiple good teams are eliminated early?
- How does draft position affect strategy?
- Should you target players from likely weak teams?
- How much should early-season schedule matter?

Create a strategy that maximizes survival probability while maintaining upside for later in the season.

Format as a comprehensive markdown guide that can be used during live drafts."""

    client = OpenAI()

    print("Generating improved Chopped League strategy with GPT-5 high reasoning...")
    print("This may take a while due to high reasoning effort...")

    response = client.responses.create(
        model="gpt-5",
        reasoning={"effort": "high"},
        tools=[{"type": "web_search_preview"}],
        input=prompt,
    )

    strategy_content = response.output_text

    # Save the new strategy
    output_file = "chopped_league_strategy_v2.md"
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
    generate_chopped_strategy()
