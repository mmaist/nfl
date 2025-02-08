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

class Player(BaseModel):
    nfl_id: int = Field(alias='nflId')
    gsis_id: str = Field(alias='gsisId')
    position: str
    position_group: str = Field(alias='positionGroup')
    uniform_number: str = Field(alias='uniformNumber')
    team_id: str = Field(alias='teamId')
    first_name: str = Field(alias='firstName')
    last_name: str = Field(alias='lastName')
    player_name: str = Field(alias='playerName')

class PlayStat(BaseModel):
    play_id: int = Field(alias='playId')
    club_code: str = Field(alias='clubCode')
    player_name: Optional[str] = Field(None, alias='playerName')
    stat_id: int = Field(alias='statId')
    yards: int
    gsis_id: Optional[str] = Field(None, alias='gsisId')

class PlaySummary(BaseModel):
    game_id: int = Field(alias='gameId')
    game_key: int = Field(alias='gameKey')
    gsis_play_id: int = Field(alias='gsisPlayId')
    play: 'PlayDetails'
    play_id: int = Field(alias='playId')
    schedule: 'GameSchedule'
    home_is_offense: bool = Field(alias='homeIsOffense')
    away: List[Player]
    home: List[Player]

class PlayDetails(BaseModel):
    game_id: int = Field(alias='gameId')
    play_id: int = Field(alias='playId')
    sequence: int
    down: int
    game_clock: str = Field(alias='gameClock')
    game_key: int = Field(alias='gameKey')
    home_score: int = Field(alias='homeScore')
    is_big_play: bool = Field(alias='isBigPlay')
    is_end_quarter: bool = Field(alias='isEndQuarter')
    is_goal_to_go: bool = Field(alias='isGoalToGo')
    is_no_play: bool = Field(alias='isNoPlay')
    is_penalty: bool = Field(alias='isPenalty')
    is_playtime_play: bool = Field(alias='isPlaytimePlay')
    is_st_play: bool = Field(alias='isSTPlay')
    is_scoring: bool = Field(alias='isScoring')
    play_description: str = Field(alias='playDescription')
    play_description_with_jersey_numbers: str = Field(alias='playDescriptionWithJerseyNumbers')
    play_state: str = Field(alias='playState')
    play_stats: Optional[List[PlayStat]] = Field(default_factory=list)
    play_type: str = Field(alias='playType')
    play_type_code: int = Field(alias='playTypeCode')
    possession_team_id: str = Field(alias='possessionTeamId')
    pre_snap_home_score: int = Field(alias='preSnapHomeScore')
    pre_snap_visitor_score: int = Field(alias='preSnapVisitorScore')
    quarter: int
    time_of_day_utc: str = Field(alias='timeOfDayUTC')
    visitor_score: int = Field(alias='visitorScore')
    yardline: str
    yardline_number: int = Field(alias='yardlineNumber')
    yardline_side: Optional[str] = Field(None, alias='yardlineSide')
    yards_to_go: int = Field(alias='yardsToGo')
    expected_points: float = Field(alias='expectedPoints')
    absolute_yardline_number: int = Field(alias='absoluteYardlineNumber')
    actual_yardline_for_first_down: Optional[Union[str, float]] = Field(None, alias='actualYardlineForFirstDown')
    actual_yards_to_go: Optional[Union[int, float]] = Field(None, alias='actualYardsToGo')
    end_game_clock: Optional[str] = Field(None, alias='endGameClock')
    is_change_of_possession: bool = Field(alias='isChangeOfPossession')
    is_played_out_play: bool = Field(alias='isPlayedOutPlay')
    is_redzone_play: bool = Field(alias='isRedzonePlay')
    play_direction: str = Field(alias='playDirection')
    start_game_clock: Optional[str] = Field(None, alias='startGameClock')
    expected_points_added: float = Field(alias='expectedPointsAdded')
    pre_snap_home_team_win_probability: float = Field(alias='preSnapHomeTeamWinProbability')
    pre_snap_visitor_team_win_probability: float = Field(alias='preSnapVisitorTeamWinProbability')
    post_play_home_team_win_probability: float = Field(alias='postPlayHomeTeamWinProbability')
    post_play_visitor_team_win_probability: float = Field(alias='postPlayVisitorTeamWinProbability')
    home_timeouts_left: int = Field(alias='homeTimeoutsLeft')
    visitor_timeouts_left: int = Field(alias='visitorTimeoutsLeft')

class TeamScore(BaseModel):
    point_total: int = Field(alias='pointTotal')
    point_q1: int = Field(alias='pointQ1')
    point_q2: int = Field(alias='pointQ2')
    point_q3: int = Field(alias='pointQ3')
    point_q4: int = Field(alias='pointQ4')
    point_ot: int = Field(alias='pointOT')
    timeouts_remaining: int = Field(alias='timeoutsRemaining')

class GameScore(BaseModel):
    time: str
    phase: str
    visitor_team_score: TeamScore = Field(alias='visitorTeamScore')
    home_team_score: TeamScore = Field(alias='homeTeamScore')

class GameSite(BaseModel):
    smart_id: str = Field(alias='smartId')
    site_id: int = Field(alias='siteId')
    site_full_name: str = Field(alias='siteFullName')
    site_city: str = Field(alias='siteCity')
    site_state: str = Field(alias='siteState')
    postal_code: str = Field(alias='postalCode')
    roof_type: str = Field(alias='roofType')

class ScheduleTeam(BaseModel):
    team_id: str = Field(alias='teamId')
    smart_id: str = Field(alias='smartId')
    logo: str
    abbr: str
    city_state: str = Field(alias='cityState')
    full_name: str = Field(alias='fullName')
    nick: str
    team_type: str = Field(alias='teamType')
    conference_abbr: str = Field(alias='conferenceAbbr')
    division_abbr: str = Field(alias='divisionAbbr')

class GameSchedule(BaseModel):
    game_key: int = Field(alias='gameKey')
    game_date: str = Field(alias='gameDate')
    game_id: int = Field(alias='gameId')
    game_time: str = Field(alias='gameTime')
    game_time_eastern: str = Field(alias='gameTimeEastern')
    game_type: str = Field(alias='gameType')
    home_display_name: str = Field(alias='homeDisplayName')
    home_nickname: str = Field(alias='homeNickname')
    home_team: ScheduleTeam = Field(alias='homeTeam')
    home_team_abbr: str = Field(alias='homeTeamAbbr')
    home_team_id: str = Field(alias='homeTeamId')
    iso_time: int = Field(alias='isoTime')
    network_channel: str = Field(alias='networkChannel')
    ngs_game: bool = Field(alias='ngsGame')
    season: int
    season_type: str = Field(alias='seasonType')
    site: GameSite
    smart_id: str = Field(alias='smartId')
    visitor_display_name: str = Field(alias='visitorDisplayName')
    visitor_nickname: str = Field(alias='visitorNickname')
    visitor_team: ScheduleTeam = Field(alias='visitorTeam')
    visitor_team_abbr: str = Field(alias='visitorTeamAbbr')
    visitor_team_id: str = Field(alias='visitorTeamId')
    week: int
    week_name_abbr: str = Field(alias='weekNameAbbr')
    score: GameScore
    validated: bool
    released_to_clubs: bool = Field(alias='releasedToClubs')

class Play(BaseModel):
    selected_param_values: Dict = Field(default_factory=dict, alias='selectedParamValues')
    season: int
    season_type: str = Field(alias='seasonType')
    week: int
    week_slug: str = Field(alias='weekSlug')
    game_id: int = Field(alias='gameId')
    fapi_game_id: str = Field(alias='fapiGameId')
    play_id: int = Field(alias='playId')
    sequence: int
    quarter: int
    down: Optional[int] = None
    yards_to_go: Optional[int] = Field(None, alias='yardsToGo')
    yardline: Optional[str] = None
    play_description: str = Field(alias='playDescription')
    game_clock: str = Field(alias='gameClock')
    play_type: str = Field(alias='playType')
    home_team_abbr: str = Field(alias='homeTeamAbbr')
    home_team_id: str = Field(alias='homeTeamId')
    visitor_team_abbr: str = Field(alias='visitorTeamAbbr')
    visitor_team_id: str = Field(alias='visitorTeamId')
    possession_team_id: str = Field(alias='possessionTeamId')
    defense_team_id: str = Field(alias='defenseTeamId')
    summary: Optional[PlaySummary] = None

class PlaysResponse(BaseModel):
    count: int
    plays: List[Play]

class Game(BaseModel):
    game_info: GameInfo = Field(alias='game_info')
    venue: Optional[Venue] = None
    broadcast: Optional[Dict] = {}
    teams: Teams
    situation: GameSituation
    betting: Optional[BettingOdds] = Field(default_factory=BettingOdds)
    metadata: Optional[Dict] = {}
    plays: Optional[List[Play]] = Field(default_factory=list)

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