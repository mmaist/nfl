import pytest
import os
import sys
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.scraper.scraper import NFLGameScraper
from src.database.database import db, DBGame, DBPlay, DBPlayer
from src.database.db_utils import NFLDatabaseManager

@pytest.fixture(scope="session")
def load_env():
    """Load environment variables for testing."""
    load_dotenv()
    return {
        "email": os.getenv("NFL_EMAIL"),
        "password": os.getenv("NFL_PASSWORD"),
        "bearer_token": os.getenv("BEARER_TOKEN")
    }

@pytest.fixture
def api_scraper():
    """Create an API-only scraper instance for testing."""
    return NFLGameScraper(api_only=True)

@pytest.fixture
def full_scraper(load_env):
    """Create a full scraper instance for testing."""
    return NFLGameScraper(
        email=load_env["email"],
        password=load_env["password"],
        api_only=False
    )

@pytest.fixture
def test_game_id():
    """Return a test game ID."""
    return "7d403c8c-1312-11ef-afd1-646009f18b2e"

@pytest.fixture
def test_play_id():
    """Return a test play ID."""
    return 39

@pytest.fixture
def test_db():
    """Create a test database instance."""
    test_db_path = "test_nfl.db"
    # Clean up any existing test db
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    # Create fresh test database
    db_manager = NFLDatabaseManager(test_db_path)
    yield db_manager
    
    # Cleanup after test
    db_manager.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.fixture
def sample_game_data():
    """Return sample game data for testing."""
    return {
        "id": "2024010101",
        "season": 2024,
        "season_type": "REG",
        "week": "1",
        "status": "FINAL",
        "home_team_id": "TB",
        "away_team_id": "KC",
        "home_score_total": 21,
        "away_score_total": 14
    } 