import pytest
import json
import os
from datetime import datetime
from unittest.mock import Mock, patch
from scrapeVideos import NFLGameScraper
from models import NFLData, PlaySummary, PlaysResponse

# Test data
MOCK_PLAY_SUMMARY = {
    "gameId": 123,
    "gameKey": 456,
    "gsisPlayId": 789,
    "play": {
        "gameId": 123,
        "playId": 1,
        "sequence": 1,
        "down": 1,
        "gameClock": "15:00",
        "playDescription": "Test play",
        "playType": "RUSH",
        "quarter": 1,
        "yardline": "TB 30",
        "yardsToGo": 10
    },
    "playId": 1,
    "schedule": {
        "gameKey": 456,
        "gameDate": "2024-01-01",
        "gameId": 123,
        "gameTime": "13:00",
        "gameTimeEastern": "13:00",
        "gameType": "REG",
        "homeTeam": {
            "teamId": "TB",
            "smartId": "TB",
            "logo": "logo.png",
            "abbr": "TB",
            "cityState": "Tampa Bay",
            "fullName": "Tampa Bay Buccaneers",
            "nick": "Bucs",
            "teamType": "TEAM",
            "conferenceAbbr": "NFC",
            "divisionAbbr": "NFC South"
        },
        "visitorTeam": {
            "teamId": "KC",
            "smartId": "KC",
            "logo": "logo.png",
            "abbr": "KC",
            "cityState": "Kansas City",
            "fullName": "Kansas City Chiefs",
            "nick": "Chiefs",
            "teamType": "TEAM",
            "conferenceAbbr": "AFC",
            "divisionAbbr": "AFC West"
        },
        "score": {
            "time": "15:00",
            "phase": "1",
            "visitorTeamScore": {
                "pointTotal": 0,
                "pointQ1": 0,
                "pointQ2": 0,
                "pointQ3": 0,
                "pointQ4": 0,
                "pointOT": 0,
                "timeoutsRemaining": 3
            },
            "homeTeamScore": {
                "pointTotal": 0,
                "pointQ1": 0,
                "pointQ2": 0,
                "pointQ3": 0,
                "pointQ4": 0,
                "pointOT": 0,
                "timeoutsRemaining": 3
            }
        }
    },
    "homeIsOffense": True,
    "away": [],
    "home": []
}

MOCK_PLAYS_RESPONSE = {
    "count": 1,
    "plays": [
        {
            "selectedParamValues": {},
            "season": 2024,
            "seasonType": "REG",
            "week": 1,
            "weekSlug": "WEEK_1",
            "gameId": 123,
            "fapiGameId": "123",
            "playId": 1,
            "sequence": 1,
            "quarter": 1,
            "down": 1,
            "yardsToGo": 10,
            "yardline": "TB 30",
            "playDescription": "Test play",
            "gameClock": "15:00",
            "playType": "RUSH",
            "homeTeamAbbr": "TB",
            "homeTeamId": "TB",
            "visitorTeamAbbr": "KC",
            "visitorTeamId": "KC",
            "possessionTeamId": "TB",
            "defenseTeamId": "KC"
        }
    ]
}

@pytest.fixture
def scraper():
    """Create a scraper instance for testing."""
    return NFLGameScraper(api_only=True)

@pytest.fixture
def mock_session():
    """Create a mock session for testing API calls."""
    with patch('requests.Session') as mock:
        session = Mock()
        mock.return_value = session
        yield session

def test_get_play_summary(scraper, mock_session):
    """Test fetching play summary."""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = MOCK_PLAY_SUMMARY
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    
    # Set bearer token
    scraper.bearer_token = "test_token"
    scraper.session = mock_session  # Use the mock session
    
    # Call the method
    result = scraper.get_play_summary("123", 1)
    
    # Verify the result
    assert result is not None
    assert isinstance(result, PlaySummary)
    assert result.game_id == 123
    assert result.play_id == 1
    assert result.play.play_description == "Test play"

def test_get_plays_data(scraper, mock_session):
    """Test fetching plays data."""
    # Setup mock response
    mock_response = Mock()
    mock_response.json.return_value = MOCK_PLAYS_RESPONSE
    mock_response.raise_for_status.return_value = None
    mock_session.get.return_value = mock_response
    
    # Set bearer token
    scraper.bearer_token = "test_token"
    scraper.session = mock_session  # Use the mock session
    
    # Call the method
    result = scraper.get_plays_data(2024, "REG", "WEEK_1", "123")
    
    # Verify the result
    assert result is not None
    assert isinstance(result, PlaysResponse)
    assert result.count == 1
    assert len(result.plays) == 1
    assert result.plays[0].play_id == 1
    assert result.plays[0].play_description == "Test play"

def test_get_play_summary_no_token(scraper):
    """Test fetching play summary without bearer token."""
    scraper.bearer_token = None
    result = scraper.get_play_summary("123", 1)
    assert result is None

def test_get_plays_data_no_token(scraper):
    """Test fetching plays data without bearer token."""
    scraper.bearer_token = None
    result = scraper.get_plays_data(2024, "REG", "WEEK_1", "123")
    assert result is None

def test_get_play_summary_api_error(scraper, mock_session):
    """Test handling API error in play summary."""
    # Setup mock to raise an exception
    mock_session.get.side_effect = Exception("API Error")
    scraper.bearer_token = "test_token"
    
    # Call the method
    result = scraper.get_play_summary("123", 1)
    assert result is None

def test_get_plays_data_api_error(scraper, mock_session):
    """Test handling API error in plays data."""
    # Setup mock to raise an exception
    mock_session.get.side_effect = Exception("API Error")
    scraper.bearer_token = "test_token"
    
    # Call the method
    result = scraper.get_plays_data(2024, "REG", "WEEK_1", "123")
    assert result is None 