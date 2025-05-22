import pytest
import os
from dotenv import load_dotenv
from scrapeVideos import NFLGameScraper

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