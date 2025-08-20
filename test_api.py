#!/usr/bin/env python3
"""Test the Sleeper API wrapper."""

from sleeper_api import SleeperAPI


def test_api():
    api = SleeperAPI()

    # Test getting NFL state
    print("Testing NFL State endpoint...")
    state = api.get_nfl_state()
    print(f"Current NFL week: {state.week}")
    print(f"Season: {state.season}")
    print(f"Season type: {state.season_type}")
    print()

    # Test getting a user (using a known username)
    print("Testing User endpoint...")
    try:
        user = api.get_user("sleeperbot")
        print(f"Username: {user.username}")
        print(f"User ID: {user.user_id}")
        print(f"Display name: {user.display_name}")
    except Exception as e:
        print(f"Error getting user: {e}")
    print()

    # Test trending players
    print("Testing Trending Players endpoint...")
    try:
        trending = api.get_trending_players(sport="nfl", type="add")
        if trending:
            print(f"Top trending player ID: {trending[0].player_id}")
            print(f"Add count: {trending[0].count}")
        else:
            print("No trending players found")
    except Exception as e:
        print(f"Error getting trending players: {e}")

    print("\nAPI wrapper test complete!")


if __name__ == "__main__":
    test_api()
