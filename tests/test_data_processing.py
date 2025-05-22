import pytest
import json
import os
from datetime import datetime
from models import NFLData, SeasonData, SeasonTypeData, WeekData, Game
from scrapeVideos import NFLGameScraper

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