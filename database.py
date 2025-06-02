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