#!/usr/bin/env python3
"""Best available players analysis using ADP rankings."""

import json
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set


@dataclass
class RankedPlayer:
    sleeper_id: str
    name: str
    position: str
    team: str
    rank: int
    avg_rank: float
    position_rank: int
    bye_week: int = 0


class BestAvailable:
    def __init__(self):
        self.adp_rankings = self._load_adp_rankings()
        self.players_by_position = self._group_by_position()

    def _load_adp_rankings(self) -> List[RankedPlayer]:
        """Load ADP rankings from JSON file."""
        with open("adp_rankings.json", "r") as f:
            data = json.load(f)

        rankings = []
        for item in data:
            rankings.append(
                RankedPlayer(
                    sleeper_id=item["sleeper_id"],
                    name=item["name"],
                    position=item["position"],
                    team=item["team"],
                    rank=item["rank"],
                    avg_rank=item["avg_rank"],
                    position_rank=item["position_rank"],
                    bye_week=item.get("bye_week", 0),
                )
            )

        return rankings

    def _group_by_position(self) -> Dict[str, List[RankedPlayer]]:
        """Group players by position, sorted by rank."""
        by_position: Dict[str, List[RankedPlayer]] = {}

        for player in self.adp_rankings:
            pos = player.position
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)

        # Sort each position by rank
        for pos in by_position:
            by_position[pos].sort(key=lambda p: p.rank)

        return by_position

    def get_taken_player_ids(self, draft_picks) -> Set[str]:
        """Extract set of already drafted player IDs."""
        taken = set()
        for pick in draft_picks:
            if pick.player_id:
                taken.add(pick.player_id)
        return taken

    def get_best_available_by_position(
        self, taken_ids: Set[str], limit: int = 5
    ) -> Dict[str, List[RankedPlayer]]:
        """Get best available players for each position."""
        best_by_pos = {}

        for position, players in self.players_by_position.items():
            available = []
            for player in players:
                if player.sleeper_id not in taken_ids:
                    available.append(player)
                    if len(available) >= limit:
                        break

            if available:
                best_by_pos[position] = available

        return best_by_pos

    def analyze_current_roster(self, current_picks) -> Dict[str, int]:
        """Analyze current roster composition."""
        position_counts = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "DST": 0, "K": 0}

        for pick in current_picks:
            if pick.metadata and pick.metadata.position:
                pos = pick.metadata.position
                if pos in position_counts:
                    position_counts[pos] += 1

        return position_counts


def format_best_available_summary(
    draft_picks, player_slot: str, shuffle_seed: Optional[int] = None
) -> str:
    """Create a summary of best available players for the prompt."""

    ba = BestAvailable()
    taken_ids = ba.get_taken_player_ids(draft_picks)

    # Get current player's picks
    current_picks = [p for p in draft_picks if p.picked_by == player_slot]

    # Analyze current roster
    current_roster = ba.analyze_current_roster(current_picks)

    # Get best available by position
    best_by_position = ba.get_best_available_by_position(taken_ids, limit=5)

    # Format the summary
    summary = "\n## CURRENT ROSTER\n"
    for pos, count in current_roster.items():
        summary += f"{pos}: {count} | "
    summary = summary.rstrip(" | ")

    summary += "\n\n## BEST AVAILABLE PLAYERS\n\n"

    # Create tables for each position
    priority_positions = ["QB", "RB", "WR", "TE", "K", "DST"]

    # Shuffle positions if seed provided
    if shuffle_seed is not None:
        rng = random.Random(shuffle_seed)
        priority_positions = priority_positions.copy()
        rng.shuffle(priority_positions)

    for pos in priority_positions:
        if pos in best_by_position and best_by_position[pos]:
            players = best_by_position[pos].copy()

            # Shuffle players within position if seed provided
            if shuffle_seed is not None:
                rng.shuffle(players)

            summary += f"### {pos}\n"
            summary += "| Rank | Player | Team |\n"
            summary += "|------|--------|------|\n"

            for player in players:
                summary += f"| {player.position}{player.position_rank} | {player.name} | {player.team} |\n"

            summary += "\n"

    return summary
