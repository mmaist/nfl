from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Union
from datetime import datetime

class MoneyLine(BaseModel):
    home_price: Optional[str] = Field(None, alias='homePrice')
    away_price: Optional[str] = Field(None, alias='awayPrice')

class Spread(BaseModel):
    away_handicap: Optional[str] = Field(None, alias='awayHandicap')
    home_handicap: Optional[str] = Field(None, alias='homeHandicap')
    home_price: Optional[str] = Field(None, alias='homePrice')
    away_price: Optional[str] = Field(None, alias='awayPrice')

class Totals(BaseModel):
    under_handicap: Optional[float] = Field(None, alias='underHandicap')
    over_handicap: Optional[float] = Field(None, alias='overHandicap')
    over_price: Optional[int] = Field(None, alias='overPrice')
    under_price: Optional[int] = Field(None, alias='underPrice')

class BettingOdds(BaseModel):
    moneyline: Optional[MoneyLine] = None
    spread: Optional[Spread] = None
    totals: Optional[Totals] = None
    updated_at: Optional[str] = Field(None, alias='updatedAt')

class Score(BaseModel):
    q1: Optional[int] = 0
    q2: Optional[int] = 0
    q3: Optional[int] = 0
    q4: Optional[int] = 0
    ot: Optional[int] = 0
    total: Optional[int] = 0

class Timeouts(BaseModel):
    remaining: Optional[int] = 3
    used: Optional[int] = 0

class TeamLocation(BaseModel):
    city_state: Optional[str] = None
    conference: Optional[str] = None
    division: Optional[str] = None

class TeamInfo(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    nickname: Optional[str] = None
    logo: Optional[str] = None
    abbreviation: Optional[str] = None
    location: Optional[TeamLocation] = None

class TeamGameStats(BaseModel):
    score: Score = Field(default_factory=Score)
    timeouts: Timeouts = Field(default_factory=Timeouts)
    possession: bool = False

class Team(BaseModel):
    info: TeamInfo
    game_stats: TeamGameStats = Field(alias='game_stats')

class Teams(BaseModel):
    home: Team
    away: Team

class GameSituation(BaseModel):
    clock: Optional[str] = None
    quarter: Optional[str] = None
    down: Optional[int] = None
    distance: Optional[int] = None
    yard_line: Optional[str] = None
    is_red_zone: Optional[bool] = Field(None, alias='is_red_zone')
    is_goal_to_go: Optional[bool] = Field(None, alias='is_goal_to_go')

class Venue(BaseModel):
    smart_id: Optional[str] = Field(None, alias='smartId')
    site_id: Optional[int] = Field(None, alias='siteId')
    site_full_name: Optional[str] = Field(None, alias='siteFullName')
    site_city: Optional[str] = Field(None, alias='siteCity')
    site_state: Optional[str] = Field(None, alias='siteState')
    postal_code: Optional[str] = Field(None, alias='postalCode')
    roof_type: Optional[str] = Field(None, alias='roofType')

class GameInfo(BaseModel):
    id: str
    season: int
    season_type: str = Field(alias='season_type')
    week: str
    status: Optional[str] = None
    display_status: Optional[str] = Field(None, alias='display_status')
    game_state: Optional[str] = Field(None, alias='game_state')
    attendance: Optional[int] = None
    weather: Optional[str] = None
    gamebook_url: Optional[str] = Field(None, alias='gamebook_url')
    date: Optional[str] = None
    time: Optional[str] = None
    network: Optional[str] = None

class Game(BaseModel):
    game_info: GameInfo = Field(alias='game_info')
    venue: Optional[Venue] = None
    broadcast: Optional[Dict] = {}
    teams: Teams
    situation: GameSituation
    betting: Optional[BettingOdds] = Field(default_factory=BettingOdds)
    metadata: Optional[Dict] = {}

class WeekData(BaseModel):
    metadata: Dict
    games: List[Game]

class SeasonTypeData(BaseModel):
    weeks: Dict[str, WeekData]

class SeasonData(BaseModel):
    types: Dict[str, SeasonTypeData]

class NFLData(BaseModel):
    seasons: Dict[int, SeasonData]
    metadata: Dict 