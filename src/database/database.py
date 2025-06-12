from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

class DBGame(Base):
    __tablename__ = 'games'
    
    id = Column(String, primary_key=True)
    season = Column(Integer, nullable=False, index=True)
    season_type = Column(String, nullable=False, index=True)
    week = Column(String, nullable=False, index=True)
    status = Column(String)
    display_status = Column(String)
    game_state = Column(String)
    attendance = Column(Integer)
    weather = Column(String)
    gamebook_url = Column(String)
    date = Column(String)
    time = Column(String)
    network = Column(String)
    
    # Venue info
    venue_smart_id = Column(String)
    venue_site_id = Column(Integer)
    venue_site_full_name = Column(String)
    venue_site_city = Column(String)
    venue_site_state = Column(String)
    venue_postal_code = Column(String)
    venue_roof_type = Column(String)
    
    # Weather data (structured)
    weather_temperature = Column(Float)
    weather_wind_speed = Column(Float)
    weather_wind_direction = Column(String)
    weather_precipitation = Column(String)
    weather_humidity = Column(Float)
    weather_conditions = Column(String)
    
    # Team info (denormalized for quick access)
    home_team_id = Column(String, index=True)
    home_team_name = Column(String)
    home_team_nickname = Column(String)
    home_team_abbreviation = Column(String)
    away_team_id = Column(String, index=True)
    away_team_name = Column(String)
    away_team_nickname = Column(String)
    away_team_abbreviation = Column(String)
    
    # Scores
    home_score_q1 = Column(Integer, default=0)
    home_score_q2 = Column(Integer, default=0)
    home_score_q3 = Column(Integer, default=0)
    home_score_q4 = Column(Integer, default=0)
    home_score_ot = Column(Integer, default=0)
    home_score_total = Column(Integer, default=0)
    away_score_q1 = Column(Integer, default=0)
    away_score_q2 = Column(Integer, default=0)
    away_score_q3 = Column(Integer, default=0)
    away_score_q4 = Column(Integer, default=0)
    away_score_ot = Column(Integer, default=0)
    away_score_total = Column(Integer, default=0)
    
    # Current situation
    clock = Column(String)
    quarter = Column(String)
    down = Column(Integer)
    distance = Column(Integer)
    yard_line = Column(String)
    is_red_zone = Column(Boolean)
    is_goal_to_go = Column(Boolean)
    
    # Betting odds
    moneyline_home_price = Column(String)
    moneyline_away_price = Column(String)
    spread_home_handicap = Column(String)
    spread_away_handicap = Column(String)
    spread_home_price = Column(String)
    spread_away_price = Column(String)
    totals_under_handicap = Column(Float)
    totals_over_handicap = Column(Float)
    totals_over_price = Column(Integer)
    totals_under_price = Column(Integer)
    betting_updated_at = Column(String)
    
    # Team stats (from standings and historical analysis)
    home_team_wins = Column(Integer)
    home_team_losses = Column(Integer)
    home_team_win_streak = Column(Integer)
    home_team_offensive_rank = Column(Integer)
    home_team_defensive_rank = Column(Integer)
    away_team_wins = Column(Integer)
    away_team_losses = Column(Integer)
    away_team_win_streak = Column(Integer)
    away_team_offensive_rank = Column(Integer)
    away_team_defensive_rank = Column(Integer)
    
    # Home team offensive stats
    home_team_points_per_game = Column(Float)
    home_team_yards_per_game = Column(Float)
    home_team_pass_yards_per_game = Column(Float)
    home_team_rush_yards_per_game = Column(Float)
    home_team_third_down_pct = Column(Float)
    home_team_red_zone_pct = Column(Float)
    home_team_turnover_rate = Column(Float)
    home_team_time_of_possession = Column(Float)
    
    # Home team defensive stats
    home_team_points_allowed_per_game = Column(Float)
    home_team_yards_allowed_per_game = Column(Float)
    home_team_pass_yards_allowed_per_game = Column(Float)
    home_team_rush_yards_allowed_per_game = Column(Float)
    home_team_third_down_def_pct = Column(Float)
    home_team_red_zone_def_pct = Column(Float)
    home_team_takeaway_rate = Column(Float)
    home_team_sacks_per_game = Column(Float)
    
    # Away team offensive stats
    away_team_points_per_game = Column(Float)
    away_team_yards_per_game = Column(Float)
    away_team_pass_yards_per_game = Column(Float)
    away_team_rush_yards_per_game = Column(Float)
    away_team_third_down_pct = Column(Float)
    away_team_red_zone_pct = Column(Float)
    away_team_turnover_rate = Column(Float)
    away_team_time_of_possession = Column(Float)
    
    # Away team defensive stats
    away_team_points_allowed_per_game = Column(Float)
    away_team_yards_allowed_per_game = Column(Float)
    away_team_pass_yards_allowed_per_game = Column(Float)
    away_team_rush_yards_allowed_per_game = Column(Float)
    away_team_third_down_def_pct = Column(Float)
    away_team_red_zone_def_pct = Column(Float)
    away_team_takeaway_rate = Column(Float)
    away_team_sacks_per_game = Column(Float)
    
    # Recent form (last 3 games)
    home_team_last3_wins = Column(Integer)
    home_team_last3_points_per_game = Column(Float)
    home_team_last3_points_allowed = Column(Float)
    away_team_last3_wins = Column(Integer)
    away_team_last3_points_per_game = Column(Float)
    away_team_last3_points_allowed = Column(Float)
    
    # Recent form (last 5 games)
    home_team_last5_wins = Column(Integer)
    home_team_last5_points_per_game = Column(Float)
    home_team_last5_points_allowed = Column(Float)
    away_team_last5_wins = Column(Integer)
    away_team_last5_points_per_game = Column(Float)
    away_team_last5_points_allowed = Column(Float)
    
    # Head-to-head stats
    head_to_head_home_wins = Column(Integer)  # Home team wins in last 5 H2H games
    head_to_head_away_wins = Column(Integer)  # Away team wins in last 5 H2H games
    head_to_head_avg_total_points = Column(Float)  # Average total points in recent H2H
    
    # Metadata
    metadata_json = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plays = relationship("DBPlay", back_populates="game", cascade="all, delete-orphan")

class DBPlay(Base):
    __tablename__ = 'plays'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(String, ForeignKey('games.id'), nullable=False, index=True)
    play_id = Column(Integer, nullable=False)
    sequence = Column(Integer, nullable=False)
    
    # Play details
    quarter = Column(Integer)
    down = Column(Integer)
    yards_to_go = Column(Integer)
    yardline = Column(String)
    game_clock = Column(String)
    play_type = Column(String, index=True)
    play_description = Column(Text)
    
    # Team info
    possession_team_id = Column(String, index=True)
    defense_team_id = Column(String, index=True)
    
    # Scores
    pre_snap_home_score = Column(Integer)
    pre_snap_visitor_score = Column(Integer)
    home_score = Column(Integer)
    visitor_score = Column(Integer)
    
    # Play attributes
    is_big_play = Column(Boolean, default=False)
    is_end_quarter = Column(Boolean, default=False)
    is_goal_to_go = Column(Boolean, default=False)
    is_no_play = Column(Boolean, default=False)
    is_penalty = Column(Boolean, default=False)
    is_scoring = Column(Boolean, default=False)
    is_st_play = Column(Boolean, default=False)
    is_change_of_possession = Column(Boolean, default=False)
    is_redzone_play = Column(Boolean, default=False)
    
    # Advanced stats
    expected_points = Column(Float)
    expected_points_added = Column(Float)
    pre_snap_home_team_win_probability = Column(Float)
    pre_snap_visitor_team_win_probability = Column(Float)
    post_play_home_team_win_probability = Column(Float)
    post_play_visitor_team_win_probability = Column(Float)
    
    # Timeouts
    home_timeouts_left = Column(Integer)
    visitor_timeouts_left = Column(Integer)
    
    # Additional play data
    play_state = Column(String)
    play_type_code = Column(Integer)
    yardline_number = Column(Integer)
    yardline_side = Column(String)
    absolute_yardline_number = Column(Integer)
    play_direction = Column(String)
    
    # Formation and play details (extracted from description)
    offensive_formation = Column(String)
    defensive_formation = Column(String)
    yards_gained = Column(Integer)
    pass_length = Column(String)  # short/medium/deep
    pass_location = Column(String)  # left/middle/right
    run_direction = Column(String)  # left/middle/right
    
    # Defensive personnel details
    defensive_package = Column(String)  # base/nickel/dime/heavy
    defensive_db_count = Column(Integer)  # Number of DBs
    defensive_lb_count = Column(Integer)  # Number of LBs
    defensive_dl_count = Column(Integer)  # Number of DLs
    defensive_box_count = Column(Integer)  # Players in the box
    
    # Game context features
    score_differential = Column(Integer)  # home_score - away_score at time of play
    time_remaining_half = Column(Integer)  # seconds remaining in half
    time_remaining_game = Column(Integer)  # seconds remaining in game
    is_two_minute_drill = Column(Boolean, default=False)
    is_must_score_situation = Column(Boolean, default=False)
    
    # Drive context
    drive_number = Column(Integer)  # Which drive of the game this is
    drive_play_number = Column(Integer)  # Which play of the current drive
    drive_start_yardline = Column(Integer)  # Where the drive started (0-100)
    drive_time_of_possession = Column(Integer)  # Seconds elapsed in current drive
    drive_plays_so_far = Column(Integer)  # Number of plays in current drive
    
    # Game script features
    is_winning_team = Column(Boolean)  # Is the possession team currently winning
    is_losing_team = Column(Boolean)  # Is the possession team currently losing
    is_comeback_situation = Column(Boolean)  # Down by 10+ points in 4th quarter
    is_blowout_situation = Column(Boolean)  # Up/down by 21+ points
    game_competitive_index = Column(Float)  # How competitive the game is (0-1)
    
    # Momentum indicators
    possessing_team_last_score = Column(Integer)  # Plays since possession team last scored
    opposing_team_last_score = Column(Integer)  # Plays since opposing team last scored
    possessing_team_turnovers = Column(Integer)  # Turnovers by possession team so far
    opposing_team_turnovers = Column(Integer)  # Turnovers by opposing team so far
    turnover_margin = Column(Integer)  # Possession team turnovers - opponent turnovers
    
    # Timeout context
    possessing_team_timeouts = Column(Integer)  # Timeouts remaining for possession team
    opposing_team_timeouts = Column(Integer)  # Timeouts remaining for opposing team
    timeout_advantage = Column(Integer)  # Possession team timeouts - opponent timeouts
    
    # Weather context
    weather_impact_score = Column(Float)  # 0-1 score of how much weather affects play
    is_indoor_game = Column(Boolean)  # Whether game is played indoors
    
    # Field position context
    field_position_category = Column(String)  # own_territory, midfield, opponent_territory, red_zone
    yards_from_own_endzone = Column(Integer)  # Distance from own goal line
    yards_from_opponent_endzone = Column(Integer)  # Distance from opponent goal line
    
    # Pass play details
    is_complete_pass = Column(Boolean)
    is_touchdown_pass = Column(Boolean)
    is_interception = Column(Boolean)
    pass_target = Column(String)  # Target receiver name
    pass_defender = Column(String)  # Defender(s) on the play
    is_sack = Column(Boolean)
    sack_yards = Column(Integer)
    quarterback_hit = Column(Boolean)
    quarterback_scramble = Column(Boolean)
    
    # Run play details
    run_gap = Column(String)  # left end, left tackle, left guard, middle, right guard, right tackle, right end
    yards_after_contact = Column(Integer)  # Estimated from description
    is_touchdown_run = Column(Boolean)
    is_fumble = Column(Boolean)
    fumble_recovered_by = Column(String)
    fumble_forced_by = Column(String)
    
    # Play outcome
    is_first_down = Column(Boolean)
    is_turnover = Column(Boolean)
    field_position_gained = Column(Integer)  # Net field position change
    
    # Penalty details
    is_penalty_on_play = Column(Boolean)
    penalty_type = Column(String)
    penalty_team = Column(String)
    penalty_player = Column(String)
    penalty_yards = Column(Integer)
    penalty_declined = Column(Boolean)
    penalty_offset = Column(Boolean)
    penalty_no_play = Column(Boolean)
    
    # Special teams details
    is_field_goal = Column(Boolean)
    field_goal_distance = Column(Integer)
    field_goal_result = Column(String)  # GOOD, NO GOOD, BLOCKED
    is_punt = Column(Boolean)
    punt_distance = Column(Integer)
    punt_return_yards = Column(Integer)
    is_kickoff = Column(Boolean)
    kickoff_return_yards = Column(Integer)
    is_touchback = Column(Boolean)
    
    # Play stats and personnel data as JSON
    play_stats_json = Column(JSON)
    home_personnel_json = Column(JSON)
    away_personnel_json = Column(JSON)
    
    # Timestamps
    time_of_day_utc = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    game = relationship("DBGame", back_populates="plays")
    stats = relationship("DBPlayStat", back_populates="play", cascade="all, delete-orphan")

class DBPlayStat(Base):
    __tablename__ = 'play_stats'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    play_id = Column(Integer, ForeignKey('plays.id'), nullable=False, index=True)
    club_code = Column(String)
    player_name = Column(String)
    stat_id = Column(Integer)
    yards = Column(Integer)
    gsis_id = Column(String)
    
    # Relationships
    play = relationship("DBPlay", back_populates="stats")

class DBPlayer(Base):
    __tablename__ = 'players'
    
    nfl_id = Column(Integer, primary_key=True)
    gsis_id = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    player_name = Column(String, index=True)
    position = Column(String)
    position_group = Column(String)
    uniform_number = Column(String)
    team_id = Column(String, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database connection and session management
class Database:
    def __init__(self, db_path: str = "nfl_data.db"):
        self.db_path = db_path
        self.engine = None
        self.SessionLocal = None
        
    def connect(self):
        """Initialize database connection and create tables if they don't exist"""
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_session(self):
        """Get a new database session"""
        if not self.SessionLocal:
            self.connect()
        return self.SessionLocal()
        
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()

# Singleton instance
db = Database()