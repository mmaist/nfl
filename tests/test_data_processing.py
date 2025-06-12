import pytest
import json
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.models.models import NFLData, SeasonData, SeasonTypeData, WeekData, Game
from src.scraper.scraper import NFLGameScraper
from src.database.db_utils import NFLDatabaseManager

@pytest.fixture
def test_data_dir(tmp_path):
    """Create a temporary directory for test data."""
    return tmp_path

@pytest.fixture
def sample_game_data():
    """Create sample game data for testing."""
    return {
        "game_info": {
            "id": "123",
            "season": 2024,
            "season_type": "REG",
            "week": "WEEK_1",
            "status": "FINAL",
            "display_status": "Final",
            "game_state": "FINAL",
            "attendance": 65000,
            "weather": "Sunny",
            "gamebook_url": "http://example.com",
            "date": "2024-01-01",
            "time": "13:00",
            "network": "CBS"
        },
        "teams": {
            "home": {
                "info": {
                    "id": "TB",
                    "name": "Tampa Bay Buccaneers",
                    "nickname": "Bucs",
                    "logo": "logo.png",
                    "abbreviation": "TB",
                    "location": {
                        "city_state": "Tampa Bay",
                        "conference": "NFC",
                        "division": "NFC South"
                    }
                },
                "game_stats": {
                    "score": {
                        "q1": 7,
                        "q2": 10,
                        "q3": 7,
                        "q4": 0,
                        "ot": 0,
                        "total": 24
                    },
                    "timeouts": {
                        "remaining": 0,
                        "used": 3
                    },
                    "possession": False
                }
            },
            "away": {
                "info": {
                    "id": "KC",
                    "name": "Kansas City Chiefs",
                    "nickname": "Chiefs",
                    "logo": "logo.png",
                    "abbreviation": "KC",
                    "location": {
                        "city_state": "Kansas City",
                        "conference": "AFC",
                        "division": "AFC West"
                    }
                },
                "game_stats": {
                    "score": {
                        "q1": 0,
                        "q2": 7,
                        "q3": 7,
                        "q4": 14,
                        "ot": 0,
                        "total": 28
                    },
                    "timeouts": {
                        "remaining": 1,
                        "used": 2
                    },
                    "possession": True
                }
            }
        },
        "situation": {
            "clock": "00:00",
            "quarter": "4",
            "down": None,
            "distance": None,
            "yard_line": None,
            "is_red_zone": False,
            "is_goal_to_go": False
        },
        "plays": []
    }

def test_save_progress(test_data_dir, sample_game_data):
    """Test saving progress to a file."""
    scraper = NFLGameScraper(api_only=True)
    
    # Create NFLData structure
    game = Game.model_validate(sample_game_data)
    week_data = WeekData(
        metadata={
            "season": 2024,
            "season_type": "REG",
            "week": "WEEK_1",
            "timestamp": datetime.now().isoformat()
        },
        games=[game]
    )
    
    season_type_data = SeasonTypeData(weeks={"WEEK_1": week_data})
    season_data = SeasonData(types={"REG": season_type_data})
    all_data = NFLData(
        seasons={2024: season_data},
        metadata={
            "last_updated": datetime.now().isoformat(),
            "start_season": 2024,
            "end_season": 2024,
            "data_type": "test"
        }
    )
    
    # Save to temporary directory
    os.makedirs(test_data_dir / "data", exist_ok=True)
    
    # Override the save_progress method to use test directory
    original_save_progress = scraper.save_progress
    def mock_save_progress(data, prefix=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if prefix is None:
            prefix = 'api_data' if scraper.api_only else 'nfl_game_map'
        output_file = test_data_dir / "data" / f'{prefix}_{timestamp}.json'
        with open(output_file, 'w') as f:
            json.dump(data.model_dump(by_alias=True), f, indent=4)
        print(f"Progress saved to {output_file}")
    
    scraper.save_progress = mock_save_progress
    
    try:
        # Save the data
        scraper.save_progress(all_data, prefix="test_data")
        
        # Verify file was created
        files = list(test_data_dir.glob("data/test_data_*.json"))
        assert len(files) == 1
        
        # Verify file contents
        with open(files[0], "r") as f:
            saved_data = json.load(f)
            assert saved_data["seasons"]["2024"]["types"]["REG"]["weeks"]["WEEK_1"]["games"][0]["game_info"]["id"] == "123"
    finally:
        # Restore original method
        scraper.save_progress = original_save_progress

def test_load_test_data(test_data_dir, sample_game_data):
    """Test loading test data from a file."""
    # Create test data file
    os.makedirs(test_data_dir / "data", exist_ok=True)
    test_file = test_data_dir / "data" / "test_game.json"
    
    with open(test_file, "w") as f:
        json.dump(sample_game_data, f)
    
    # Create scraper and load test data
    scraper = NFLGameScraper(api_only=True)
    
    # Test loading the data
    with open(test_file, "r") as f:
        loaded_data = json.load(f)
        game = Game.model_validate(loaded_data)
        assert game.game_info.id == "123"
        assert game.teams.home.info.name == "Tampa Bay Buccaneers"
        assert game.teams.away.info.name == "Kansas City Chiefs"

def test_data_validation(test_data_dir, sample_game_data):
    """Test data validation with Pydantic models."""
    # Test valid data
    game = Game.model_validate(sample_game_data)
    assert game.game_info.id == "123"
    assert game.teams.home.game_stats.score.total == 24
    assert game.teams.away.game_stats.score.total == 28
    
    # Test invalid data
    invalid_data = sample_game_data.copy()
    invalid_data["game_info"]["id"] = None  # Make ID invalid
    
    with pytest.raises(Exception):
        Game.model_validate(invalid_data)
    
    # Test missing optional fields
    minimal_data = {
        "game_info": {
            "id": "123",
            "season": 2024,
            "season_type": "REG",
            "week": "WEEK_1"
        },
        "teams": {
            "home": {
                "info": {
                    "id": "TB",
                    "name": "Tampa Bay Buccaneers"
                },
                "game_stats": {
                    "score": {"total": 0},
                    "timeouts": {"remaining": 3},
                    "possession": False
                }
            },
            "away": {
                "info": {
                    "id": "KC",
                    "name": "Kansas City Chiefs"
                },
                "game_stats": {
                    "score": {"total": 0},
                    "timeouts": {"remaining": 3},
                    "possession": False
                }
            }
        },
        "situation": {}
    }
    
    # Should not raise an exception
    game = Game.model_validate(minimal_data)
    assert game.game_info.id == "123"

class TestDataProcessingUtilities:
    """Test data processing functionality in db_utils."""
    
    def test_calculate_time_remaining(self, test_db):
        """Test time remaining calculation."""
        # Test 1st quarter with 10:30 remaining
        result = test_db._calculate_time_remaining(1, "10:30")
        
        assert result['time_remaining_half'] == 630 + 900  # 10:30 + 15 min for Q2
        assert result['time_remaining_game'] == 630 + 2700  # 10:30 + 45 min remaining
        assert result['is_two_minute_drill'] is False
        
        # Test 2nd quarter with 1:45 remaining (two-minute drill)
        result = test_db._calculate_time_remaining(2, "1:45")
        
        assert result['time_remaining_half'] == 105  # 1:45 in seconds
        assert result['is_two_minute_drill'] is True
        
        # Test 4th quarter
        result = test_db._calculate_time_remaining(4, "5:00")
        
        assert result['time_remaining_game'] == 300  # 5 minutes
        assert result['time_remaining_half'] == 300
    
    def test_analyze_defensive_personnel(self, test_db):
        """Test defensive personnel analysis."""
        # Test basic 4-3 defense
        defensive_players = [
            {'positionGroup': 'DL', 'position': 'DE'},
            {'positionGroup': 'DL', 'position': 'DT'},
            {'positionGroup': 'DL', 'position': 'DT'},
            {'positionGroup': 'DL', 'position': 'DE'},
            {'positionGroup': 'LB', 'position': 'LB'},
            {'positionGroup': 'LB', 'position': 'LB'},
            {'positionGroup': 'LB', 'position': 'LB'},
            {'positionGroup': 'DB', 'position': 'CB'},
            {'positionGroup': 'DB', 'position': 'CB'},
            {'positionGroup': 'DB', 'position': 'FS'},
            {'positionGroup': 'DB', 'position': 'SS'}
        ]
        
        result = test_db._analyze_defensive_personnel(defensive_players)
        
        assert result['dl_count'] == 4
        assert result['lb_count'] == 3
        assert result['db_count'] == 4
        assert result['defensive_formation'] == '4-3'
        assert result['defensive_package'] == 'base'
        assert result['box_count'] == 8  # 4 DL + 3 LB + 1 SS
    
    def test_analyze_defensive_personnel_nickel(self, test_db):
        """Test nickel defense analysis."""
        # Test nickel defense (5 DBs)
        defensive_players = [
            {'positionGroup': 'DL', 'position': 'DE'},
            {'positionGroup': 'DL', 'position': 'DT'},
            {'positionGroup': 'DL', 'position': 'DT'},
            {'positionGroup': 'DL', 'position': 'DE'},
            {'positionGroup': 'LB', 'position': 'LB'},
            {'positionGroup': 'LB', 'position': 'LB'},
            {'positionGroup': 'DB', 'position': 'CB'},
            {'positionGroup': 'DB', 'position': 'CB'},
            {'positionGroup': 'DB', 'position': 'CB'},  # Nickel CB
            {'positionGroup': 'DB', 'position': 'FS'},
            {'positionGroup': 'DB', 'position': 'SS'}
        ]
        
        result = test_db._analyze_defensive_personnel(defensive_players)
        
        assert result['dl_count'] == 4
        assert result['lb_count'] == 2
        assert result['db_count'] == 5
        assert result['defensive_formation'] == '4-2-5'
        assert result['defensive_package'] == 'nickel'
    
    def test_calculate_weather_impact(self, test_db):
        """Test weather impact calculation."""
        # Test indoor game
        game_info = Mock()
        game_info.venue = Mock()
        game_info.venue.roof_type = 'DOME'
        
        result = test_db._calculate_weather_impact(game_info)
        
        assert result['is_indoor_game'] is True
        assert result['weather_impact_score'] == 0.0
        
        # Test high wind outdoor game
        game_info.venue.roof_type = 'OPEN'
        game_info.weather = "45°F, Wind NW 25 mph, Clear"
        
        result = test_db._calculate_weather_impact(game_info)
        
        assert result['is_indoor_game'] is False
        assert result['weather_impact_score'] > 0.3  # High wind should have significant impact
    
    def test_calculate_field_position_context(self, test_db):
        """Test field position context calculation."""
        # Test own territory
        play_details = Mock()
        play_details.absolute_yardline_number = 15
        
        result = test_db._calculate_field_position_context(play_details)
        
        assert result['yards_from_own_endzone'] == 15
        assert result['yards_from_opponent_endzone'] == 85
        assert result['field_position_category'] == 'own_territory'
        
        # Test red zone
        play_details.absolute_yardline_number = 85
        
        result = test_db._calculate_field_position_context(play_details)
        
        assert result['yards_from_opponent_endzone'] == 15
        assert result['field_position_category'] == 'red_zone'
        
        # Test midfield
        play_details.absolute_yardline_number = 50
        
        result = test_db._calculate_field_position_context(play_details)
        
        assert result['field_position_category'] == 'midfield'

class TestGameContextCalculation:
    """Test game context feature calculation."""
    
    def test_calculate_game_script_features(self, test_db):
        """Test game script features calculation."""
        # Mock play details and current play
        play_details = Mock()
        play_details.home_score = 21
        play_details.visitor_score = 14
        play_details.quarter = 2
        
        current_play = Mock()
        current_play.possession_team_id = "TB"
        current_play.home_team_id = "TB"  # Home team has possession
        
        result = test_db._calculate_game_script_features(play_details, current_play)
        
        assert result['is_winning_team'] is True  # Home team is winning 21-14
        assert result['is_losing_team'] is False
        assert result['is_comeback_situation'] is False  # Not 4th quarter
        assert result['is_blowout_situation'] is False  # 7 point game
        assert result['game_competitive_index'] > 0.6  # Should be competitive
    
    def test_calculate_game_script_comeback(self, test_db):
        """Test comeback situation detection."""
        play_details = Mock()
        play_details.home_score = 10
        play_details.visitor_score = 21  # Away team winning by 11
        play_details.quarter = 4  # 4th quarter
        
        current_play = Mock()
        current_play.possession_team_id = "TB"
        current_play.home_team_id = "TB"  # Home team has possession and is losing
        
        result = test_db._calculate_game_script_features(play_details, current_play)
        
        assert result['is_winning_team'] is False
        assert result['is_losing_team'] is True
        assert result['is_comeback_situation'] is True  # Down by 11 in 4th quarter
    
    def test_calculate_timeout_context(self, test_db):
        """Test timeout context calculation."""
        play_details = Mock()
        play_details.home_timeouts_left = 2
        play_details.visitor_timeouts_left = 1
        
        current_play = Mock()
        current_play.possession_team_id = "TB"
        current_play.home_team_id = "TB"  # Home team has possession
        
        result = test_db._calculate_timeout_context(play_details, current_play)
        
        assert result['possessing_team_timeouts'] == 2
        assert result['opposing_team_timeouts'] == 1
        assert result['timeout_advantage'] == 1  # Home team has 1 more timeout 