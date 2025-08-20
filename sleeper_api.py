from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel


class LeagueStatus(str, Enum):
    PRE_DRAFT = "pre_draft"
    DRAFTING = "drafting"
    IN_SEASON = "in_season"
    COMPLETE = "complete"


class SeasonType(str, Enum):
    REGULAR = "regular"
    PRE = "pre"
    POST = "post"


class DraftStatus(str, Enum):
    PRE_DRAFT = "pre_draft"
    DRAFTING = "drafting"
    PAUSED = "paused"
    COMPLETE = "complete"


class DraftType(str, Enum):
    SNAKE = "snake"
    LINEAR = "linear"
    AUCTION = "auction"


class TransactionType(str, Enum):
    TRADE = "trade"
    FREE_AGENT = "free_agent"
    WAIVER = "waiver"


class TransactionStatus(str, Enum):
    COMPLETE = "complete"
    PENDING = "pending"
    FAILED = "failed"


class User(BaseModel):
    username: str
    user_id: str
    display_name: str
    avatar: Optional[str] = None


class LeagueUser(BaseModel):
    user_id: str
    username: str
    display_name: str
    avatar: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_owner: Optional[bool] = None


class LeagueSettings(BaseModel):
    class Config:
        extra = "allow"


class ScoringSettings(BaseModel):
    class Config:
        extra = "allow"


class League(BaseModel):
    total_rosters: int
    status: LeagueStatus
    sport: str
    settings: Optional[LeagueSettings] = None
    season_type: SeasonType
    season: str
    scoring_settings: Optional[ScoringSettings] = None
    roster_positions: Optional[List[str]] = None
    previous_league_id: Optional[str] = None
    name: str
    league_id: str
    draft_id: Optional[str] = None
    avatar: Optional[str] = None


class RosterSettings(BaseModel):
    wins: Optional[int] = 0
    waiver_position: Optional[int] = None
    waiver_budget_used: Optional[int] = 0
    total_moves: Optional[int] = 0
    ties: Optional[int] = 0
    losses: Optional[int] = 0
    fpts_decimal: Optional[float] = None
    fpts_against_decimal: Optional[float] = None
    fpts_against: Optional[float] = None
    fpts: Optional[float] = None


class Roster(BaseModel):
    starters: Optional[List[str]] = None
    settings: Optional[RosterSettings] = None
    roster_id: int
    reserve: Optional[List[str]] = None
    players: Optional[List[str]] = None
    owner_id: Optional[str] = None
    league_id: str


class Matchup(BaseModel):
    starters: Optional[List[str]] = None
    roster_id: int
    players: Optional[List[str]] = None
    matchup_id: Optional[int] = None
    points: Optional[float] = None
    custom_points: Optional[float] = None


class DraftPick(BaseModel):
    season: str
    round: int
    roster_id: int
    previous_owner_id: int
    owner_id: int


class Transaction(BaseModel):
    type: TransactionType
    transaction_id: str
    status_updated: Optional[int] = None
    status: TransactionStatus
    settings: Optional[Dict[str, Any]] = None
    roster_ids: List[int]
    metadata: Optional[Dict[str, Any]] = None
    leg: Optional[int] = None
    drops: Optional[Dict[str, int]] = None
    draft_picks: Optional[List[DraftPick]] = None
    creator: Optional[str] = None
    created: Optional[int] = None
    consenter_ids: Optional[List[int]] = None
    adds: Optional[Dict[str, int]] = None
    waiver_budget: Optional[List[Dict[str, Any]]] = None


class NFLState(BaseModel):
    week: int
    season_type: SeasonType
    season_start_date: str
    season: str
    previous_season: str
    leg: int
    league_season: str
    league_create_season: str
    display_week: int


class DraftSettings(BaseModel):
    teams: int
    slots_wr: Optional[int] = None
    slots_te: Optional[int] = None
    slots_rb: Optional[int] = None
    slots_qb: Optional[int] = None
    slots_k: Optional[int] = None
    slots_flex: Optional[int] = None
    slots_def: Optional[int] = None
    slots_bn: Optional[int] = None
    rounds: int
    pick_timer: Optional[int] = None


class DraftMetadata(BaseModel):
    scoring_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class Draft(BaseModel):
    type: DraftType
    status: DraftStatus
    start_time: Optional[int] = None
    sport: str
    settings: DraftSettings
    season_type: SeasonType
    season: str
    metadata: Optional[DraftMetadata] = None
    league_id: Optional[str] = None
    last_picked: Optional[int] = None
    last_message_time: Optional[int] = None
    last_message_id: Optional[str] = None
    draft_order: Optional[Dict[str, int]] = None
    slot_to_roster_id: Optional[Dict[str, int]] = None
    draft_id: str
    creators: Optional[List[str]] = None
    created: Optional[int] = None


class PlayerMetadata(BaseModel):
    team: Optional[str] = None
    status: Optional[str] = None
    sport: Optional[str] = None
    position: Optional[str] = None
    player_id: Optional[str] = None
    number: Optional[str] = None
    news_updated: Optional[str] = None
    last_name: Optional[str] = None
    injury_status: Optional[str] = None
    first_name: Optional[str] = None


class DraftPickData(BaseModel):
    player_id: Optional[str] = None
    picked_by: Optional[str] = None
    roster_id: Optional[str] = None
    round: int
    draft_slot: int
    pick_no: int
    metadata: Optional[PlayerMetadata] = None
    is_keeper: Optional[bool] = None
    draft_id: str


class Player(BaseModel):
    player_id: str
    hashtag: Optional[str] = None
    depth_chart_position: Optional[int] = None
    status: Optional[str] = None
    sport: Optional[str] = None
    fantasy_positions: Optional[List[str]] = None
    number: Optional[int] = None
    search_last_name: Optional[str] = None
    injury_start_date: Optional[str] = None
    weight: Optional[str] = None
    position: Optional[str] = None
    practice_participation: Optional[str] = None
    sportradar_id: Optional[Any] = None  # Can be string or int
    team: Optional[str] = None
    last_name: Optional[str] = None
    college: Optional[str] = None
    fantasy_data_id: Optional[int] = None
    injury_status: Optional[str] = None
    height: Optional[str] = None
    search_full_name: Optional[str] = None
    age: Optional[int] = None
    stats_id: Optional[Any] = None  # Can be string or int
    birth_country: Optional[str] = None
    espn_id: Optional[Any] = None  # Can be string or int
    search_rank: Optional[int] = None
    first_name: Optional[str] = None
    depth_chart_order: Optional[int] = None
    years_exp: Optional[int] = None
    rotowire_id: Optional[Any] = None  # Can be string or int
    rotoworld_id: Optional[int] = None
    search_first_name: Optional[str] = None
    yahoo_id: Optional[Any] = None  # Can be string or int


class TrendingPlayer(BaseModel):
    player_id: str
    count: int


class SleeperAPI:
    BASE_URL = "https://api.sleeper.app/v1"

    def __init__(self):
        self.session = requests.Session()

    def _get(self, endpoint: str) -> Any:
        """Make a GET request to the Sleeper API."""
        url = f"{self.BASE_URL}{endpoint}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    # User endpoints
    def get_user(self, username_or_id: str) -> User:
        """Get user by username or user_id."""
        data = self._get(f"/user/{username_or_id}")
        return User(**data)

    # League endpoints
    def get_user_leagues(
        self, user_id: str, sport: str = "nfl", season: str = "2024"
    ) -> List[League]:
        """Get all leagues for a user."""
        data = self._get(f"/user/{user_id}/leagues/{sport}/{season}")
        return [League(**league) for league in data]

    def get_league(self, league_id: str) -> League:
        """Get a specific league."""
        data = self._get(f"/league/{league_id}")
        return League(**data)

    def get_league_rosters(self, league_id: str) -> List[Roster]:
        """Get all rosters in a league."""
        data = self._get(f"/league/{league_id}/rosters")
        return [Roster(**roster) for roster in data]

    def get_league_users(self, league_id: str) -> List[LeagueUser]:
        """Get all users in a league."""
        data = self._get(f"/league/{league_id}/users")
        return [LeagueUser(**user) for user in data]

    def get_league_matchups(self, league_id: str, week: int) -> List[Matchup]:
        """Get matchups for a specific week."""
        data = self._get(f"/league/{league_id}/matchups/{week}")
        return [Matchup(**matchup) for matchup in data]

    def get_transactions(self, league_id: str, week: int) -> List[Transaction]:
        """Get transactions for a specific week."""
        data = self._get(f"/league/{league_id}/transactions/{week}")
        return [Transaction(**transaction) for transaction in data]

    def get_traded_picks(self, league_id: str) -> List[DraftPick]:
        """Get all traded picks in a league."""
        data = self._get(f"/league/{league_id}/traded_picks")
        return [DraftPick(**pick) for pick in data]

    # State endpoints
    def get_nfl_state(self) -> NFLState:
        """Get current NFL state."""
        data = self._get("/state/nfl")
        return NFLState(**data)

    # Draft endpoints
    def get_user_drafts(
        self, user_id: str, sport: str = "nfl", season: str = "2024"
    ) -> List[Draft]:
        """Get all drafts for a user."""
        data = self._get(f"/user/{user_id}/drafts/{sport}/{season}")
        return [Draft(**draft) for draft in data]

    def get_league_drafts(self, league_id: str) -> List[Draft]:
        """Get all drafts for a league."""
        data = self._get(f"/league/{league_id}/drafts")
        return [Draft(**draft) for draft in data]

    def get_draft(self, draft_id: str) -> Draft:
        """Get a specific draft."""
        data = self._get(f"/draft/{draft_id}")
        return Draft(**data)

    def get_draft_picks(self, draft_id: str) -> List[DraftPickData]:
        """Get all picks in a draft."""
        data = self._get(f"/draft/{draft_id}/picks")
        return [DraftPickData(**pick) for pick in data]

    def get_draft_traded_picks(self, draft_id: str) -> List[DraftPick]:
        """Get traded picks in a draft."""
        data = self._get(f"/draft/{draft_id}/traded_picks")
        return [DraftPick(**pick) for pick in data]

    # Player endpoints
    def get_all_players(self, sport: str = "nfl") -> Dict[str, Player]:
        """Get all players. Use sparingly - this is a large response (~5MB)."""
        data = self._get(f"/players/{sport}")
        return {
            player_id: Player(**player_data) for player_id, player_data in data.items()
        }

    def get_trending_players(
        self, sport: str = "nfl", type: str = "add"
    ) -> List[TrendingPlayer]:
        """Get trending players based on add/drop activity."""
        data = self._get(f"/players/{sport}/trending/{type}")
        return [TrendingPlayer(**player) for player in data]
