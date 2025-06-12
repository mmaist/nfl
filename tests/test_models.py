import pytest
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.models.models import (
    PlaySummary, PlayDetails, PlayStat, Player,
    GameSchedule, TeamScore, GameScore, GameSite,
    ScheduleTeam, Play, PlaysResponse
)

def test_play_summary_validation():
    """Test PlaySummary model validation."""
    data = {
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
            "yardsToGo": 10,
            "playState": "COMPLETE",
            "playTypeCode": 1,
            "possessionTeamId": "TB",
            "preSnapHomeScore": 0,
            "preSnapVisitorScore": 0,
            "timeOfDayUTC": "2024-01-01T13:00:00Z",
            "visitorScore": 0,
            "yardlineNumber": 30,
            "expectedPoints": 0.0,
            "absoluteYardlineNumber": 30,
            "isChangeOfPossession": False,
            "isPlayedOutPlay": True,
            "isRedzonePlay": False,
            "playDirection": "RIGHT",
            "expectedPointsAdded": 0.0,
            "preSnapHomeTeamWinProbability": 0.5,
            "preSnapVisitorTeamWinProbability": 0.5,
            "postPlayHomeTeamWinProbability": 0.5,
            "postPlayVisitorTeamWinProbability": 0.5,
            "homeTimeoutsLeft": 3,
            "visitorTimeoutsLeft": 3,
            "gameKey": 456,
            "homeScore": 0,
            "isBigPlay": False,
            "isEndQuarter": False,
            "isGoalToGo": False,
            "isNoPlay": False,
            "isPenalty": False,
            "isPlaytimePlay": True,
            "isSTPlay": False,
            "isScoring": False,
            "playDescriptionWithJerseyNumbers": "Test play"
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
            },
            "site": {
                "smartId": "TB",
                "siteId": 1,
                "siteFullName": "Raymond James Stadium",
                "siteCity": "Tampa",
                "siteState": "FL",
                "postalCode": "33607",
                "roofType": "OPEN"
            },
            "season": 2024,
            "seasonType": "REG",
            "week": 1,
            "weekNameAbbr": "W1",
            "validated": True,
            "releasedToClubs": True,
            "homeDisplayName": "Tampa Bay Buccaneers",
            "homeNickname": "Bucs",
            "homeTeamAbbr": "TB",
            "homeTeamId": "TB",
            "isoTime": "2024-01-01T13:00:00Z",
            "networkChannel": "CBS",
            "ngsGame": True,
            "smartId": "TB",
            "visitorDisplayName": "Kansas City Chiefs",
            "visitorNickname": "Chiefs",
            "visitorTeamAbbr": "KC",
            "visitorTeamId": "KC"
        },
        "homeIsOffense": True,
        "away": [],
        "home": []
    }
    
    play_summary = PlaySummary.model_validate(data)
    assert play_summary.game_id == 123
    assert play_summary.play_id == 1
    assert play_summary.play.play_description == "Test play"
    assert play_summary.schedule.game_type == "REG"

def test_play_stat_validation():
    """Test PlayStat model validation."""
    data = {
        "playId": 1,
        "clubCode": "TB",
        "playerName": "Test Player",
        "statId": 1,
        "yards": 10,
        "gsisId": "12345"
    }
    
    play_stat = PlayStat.model_validate(data)
    assert play_stat.play_id == 1
    assert play_stat.club_code == "TB"
    assert play_stat.player_name == "Test Player"
    assert play_stat.yards == 10

def test_player_validation():
    """Test Player model validation."""
    data = {
        "nflId": 12345,
        "gsisId": "12345",
        "position": "QB",
        "positionGroup": "QB",
        "uniformNumber": "12",
        "teamId": "TB",
        "firstName": "Test",
        "lastName": "Player",
        "playerName": "Test Player"
    }
    
    player = Player.model_validate(data)
    assert player.nfl_id == 12345
    assert player.position == "QB"
    assert player.player_name == "Test Player"

def test_play_validation():
    """Test Play model validation."""
    data = {
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
    
    play = Play.model_validate(data)
    assert play.play_id == 1
    assert play.play_description == "Test play"
    assert play.play_type == "RUSH"

def test_plays_response_validation():
    """Test PlaysResponse model validation."""
    data = {
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
    
    plays_response = PlaysResponse.model_validate(data)
    assert plays_response.count == 1
    assert len(plays_response.plays) == 1
    assert plays_response.plays[0].play_id == 1 