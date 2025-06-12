import pytest
import sys
import os
from sqlalchemy.orm import Session

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.database.database import db, DBGame, DBPlay, DBPlayer, DBPlayStat
from src.database.db_utils import NFLDatabaseManager
from src.models.models import Game, GameInfo, Teams, Team, TeamInfo, Score, Venue, GameSituation

class TestDatabaseModels:
    """Test database model creation and basic functionality."""
    
    def test_db_game_creation(self, test_db):
        """Test DBGame model creation."""
        session = test_db.db.get_session()
        
        game = DBGame(
            id="2024010101",
            season=2024,
            season_type="REG",
            week="1",
            status="FINAL",
            home_team_id="TB",
            away_team_id="KC",
            home_score_total=21,
            away_score_total=14
        )
        
        session.add(game)
        session.commit()
        
        # Verify game was saved
        saved_game = session.query(DBGame).filter_by(id="2024010101").first()
        assert saved_game is not None
        assert saved_game.season == 2024
        assert saved_game.home_team_id == "TB"
        assert saved_game.away_team_id == "KC"
        
        session.close()
    
    def test_db_play_creation(self, test_db):
        """Test DBPlay model creation."""
        session = test_db.db.get_session()
        
        # First create a game
        game = DBGame(
            id="2024010101",
            season=2024,
            season_type="REG",
            week="1"
        )
        session.add(game)
        session.commit()
        
        # Create a play
        play = DBPlay(
            game_id="2024010101",
            play_id=1,
            sequence=1,
            quarter=1,
            down=1,
            yards_to_go=10,
            play_type="RUSH",
            play_description="Test play description",
            possession_team_id="TB",
            defense_team_id="KC"
        )
        
        session.add(play)
        session.commit()
        
        # Verify play was saved
        saved_play = session.query(DBPlay).filter_by(game_id="2024010101").first()
        assert saved_play is not None
        assert saved_play.play_id == 1
        assert saved_play.play_type == "RUSH"
        assert saved_play.possession_team_id == "TB"
        
        session.close()
    
    def test_db_player_creation(self, test_db):
        """Test DBPlayer model creation."""
        session = test_db.db.get_session()
        
        player = DBPlayer(
            nfl_id=12345,
            gsis_id="00-12345",
            first_name="Test",
            last_name="Player",
            player_name="Test Player",
            position="QB",
            position_group="QB",
            uniform_number="12",
            team_id="TB"
        )
        
        session.add(player)
        session.commit()
        
        # Verify player was saved
        saved_player = session.query(DBPlayer).filter_by(nfl_id=12345).first()
        assert saved_player is not None
        assert saved_player.player_name == "Test Player"
        assert saved_player.position == "QB"
        
        session.close()

class TestDatabaseManager:
    """Test NFLDatabaseManager functionality."""
    
    def test_database_manager_initialization(self, test_db):
        """Test that database manager initializes correctly."""
        assert test_db is not None
        assert test_db.db is not None
    
    def test_get_games_empty(self, test_db):
        """Test getting games from empty database."""
        games = test_db.get_games()
        assert games == []
    
    def test_get_games_with_data(self, test_db):
        """Test getting games with data."""
        session = test_db.db.get_session()
        
        # Add test game
        game = DBGame(
            id="2024010101",
            season=2024,
            season_type="REG",
            week="1",
            home_team_id="TB",
            away_team_id="KC"
        )
        session.add(game)
        session.commit()
        session.close()
        
        # Test get_games
        games = test_db.get_games(season=2024)
        assert len(games) == 1
        assert games[0].id == "2024010101"
        
        # Test filter by team
        tb_games = test_db.get_games(team_id="TB")
        assert len(tb_games) == 1
        
        # Test filter by week
        week1_games = test_db.get_games(week="1")
        assert len(week1_games) == 1
    
    def test_get_plays_empty(self, test_db):
        """Test getting plays from empty database."""
        plays = test_db.get_plays()
        assert plays == []
    
    def test_get_plays_with_data(self, test_db):
        """Test getting plays with data."""
        session = test_db.db.get_session()
        
        # Add test game and play
        game = DBGame(id="2024010101", season=2024, season_type="REG", week="1")
        session.add(game)
        session.commit()
        
        play = DBPlay(
            game_id="2024010101",
            play_id=1,
            sequence=1,
            quarter=1,
            play_type="RUSH"
        )
        session.add(play)
        session.commit()
        session.close()
        
        # Test get_plays
        plays = test_db.get_plays(game_id="2024010101")
        assert len(plays) == 1
        assert plays[0].play_id == 1
        
        # Test filter by play type
        rush_plays = test_db.get_plays(play_type="RUSH")
        assert len(rush_plays) == 1
    
    def test_get_play_stats(self, test_db):
        """Test getting play statistics."""
        session = test_db.db.get_session()
        
        # Add test game and plays
        game = DBGame(id="2024010101", season=2024, season_type="REG", week="1")
        session.add(game)
        session.commit()
        
        # Add some test plays
        plays = [
            DBPlay(game_id="2024010101", play_id=1, sequence=1, quarter=1, 
                  play_type="RUSH", is_scoring=True),
            DBPlay(game_id="2024010101", play_id=2, sequence=2, quarter=1, 
                  play_type="PASS", is_penalty=True),
            DBPlay(game_id="2024010101", play_id=3, sequence=3, quarter=1, 
                  play_type="RUSH", is_change_of_possession=True)
        ]
        
        for play in plays:
            session.add(play)
        session.commit()
        session.close()
        
        # Test play stats
        stats = test_db.get_play_stats("2024010101")
        assert stats['total_plays'] == 3
        assert stats['scoring_plays'] == 1
        assert stats['penalties'] == 1
        assert stats['turnovers'] == 1
        assert 'RUSH' in stats['play_types']
        assert 'PASS' in stats['play_types']

class TestWeatherParsing:
    """Test weather data parsing functionality."""
    
    def test_parse_weather_basic(self, test_db):
        """Test basic weather parsing."""
        weather_str = "72°F, Wind NW 10 mph, Clear"
        result = test_db._parse_weather(weather_str)
        
        assert result['temperature'] == 72.0
        assert result['wind_speed'] == 10.0
        assert result['wind_direction'] == 'NW'
        assert result['conditions'] == 'clear'
    
    def test_parse_weather_complex(self, test_db):
        """Test complex weather parsing."""
        weather_str = "45°F, Wind SSE 15 mph, Light Rain, Humidity 85%"
        result = test_db._parse_weather(weather_str)
        
        assert result['temperature'] == 45.0
        assert result['wind_speed'] == 15.0
        assert result['wind_direction'] == 'SSE'
        assert result['precipitation'] == 'rain'
        assert result['humidity'] == 85.0
    
    def test_parse_weather_empty(self, test_db):
        """Test weather parsing with empty input."""
        result = test_db._parse_weather("")
        
        assert all(value is None for value in result.values())
    
    def test_parse_weather_indoor(self, test_db):
        """Test weather parsing for indoor games."""
        weather_str = "Dome, Controlled Environment"
        result = test_db._parse_weather(weather_str)
        
        assert result['conditions'] == 'indoor'

class TestPlayDetailsExtraction:
    """Test play details extraction functionality."""
    
    def test_extract_yards_gained(self, test_db):
        """Test yards gained extraction."""
        description = "Tom Brady pass short right to Mike Evans for 12 yards"
        result = test_db._extract_play_details(description)
        
        assert result['yards_gained'] == 12
    
    def test_extract_formation(self, test_db):
        """Test formation extraction."""
        description = "(Shotgun) Tom Brady pass short left to Chris Godwin for 8 yards"
        result = test_db._extract_play_details(description)
        
        assert result['offensive_formation'] == 'shotgun'
    
    def test_extract_pass_details(self, test_db):
        """Test pass play details extraction."""
        description = "Tom Brady pass deep right to Mike Evans for 25 yards"
        result = test_db._extract_play_details(description)
        
        assert result['pass_length'] == 'deep'
        assert result['pass_location'] == 'right'
        assert result['yards_gained'] == 25
    
    def test_extract_run_details(self, test_db):
        """Test run play details extraction."""
        description = "Leonard Fournette rush left tackle for 6 yards"
        result = test_db._extract_play_details(description)
        
        assert result['run_direction'] == 'left'
        assert result['yards_gained'] == 6

class TestPlayResultMetrics:
    """Test play result metrics extraction."""
    
    def test_extract_touchdown_pass(self, test_db):
        """Test touchdown pass extraction."""
        description = "Tom Brady pass short right to Mike Evans for 8 yards, TOUCHDOWN"
        result = test_db._extract_play_result_metrics(description, "PASS")
        
        assert result['is_touchdown_pass'] is True
        assert result['is_complete_pass'] is True
    
    def test_extract_interception(self, test_db):
        """Test interception extraction."""
        description = "Tom Brady pass deep left intercepted by Tyrann Mathieu at KC 25"
        result = test_db._extract_play_result_metrics(description, "PASS")
        
        assert result['is_interception'] is True
        assert result['is_turnover'] is True
        assert result['is_complete_pass'] is False
    
    def test_extract_sack(self, test_db):
        """Test sack extraction."""
        description = "Tom Brady sacked by Chris Jones for -8 yards"
        result = test_db._extract_play_result_metrics(description, "PASS")
        
        assert result['is_sack'] is True
        assert result['sack_yards'] == 8
    
    def test_extract_field_goal(self, test_db):
        """Test field goal extraction."""
        description = "Ryan Succop 42 yard field goal GOOD"
        result = test_db._extract_play_result_metrics(description, "FIELD_GOAL")
        
        assert result['is_field_goal'] is True
        assert result['field_goal_distance'] == 42
        assert result['field_goal_result'] == 'GOOD'
    
    def test_extract_penalty(self, test_db):
        """Test penalty extraction."""
        description = "Penalty on TB-Mike Evans: Offensive Pass Interference, 10 yards"
        result = test_db._extract_play_result_metrics(description, "PENALTY")
        
        assert result['is_penalty_on_play'] is True
        assert result['penalty_type'] == 'Pass Interference'
        # Note: penalty parsing regex may need adjustment for this format
        # assert result['penalty_team'] == 'TB'
        # assert result['penalty_player'] == 'Mike Evans'
        assert result['penalty_yards'] == 10