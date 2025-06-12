#!/usr/bin/env python3
"""Test script to verify new data collection fields."""

import os
import sys
from dotenv import load_dotenv
from scrapeVideos import NFLGameScraper
from database import db, DBGame, DBPlay
from sqlalchemy import create_engine, inspect
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_new_fields():
    """Test that all new fields are being populated correctly."""
    
    # Create a test database
    test_db_path = "test_nfl_data.db"
    
    # Remove old test database if it exists
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        logger.info(f"Removed existing test database: {test_db_path}")
    
    # Initialize scraper with test database
    scraper = NFLGameScraper(
        api_only=True,
        use_database=True,
        db_path=test_db_path
    )
    
    # Test scraping a single game
    test_game_id = "2024010101"  # Example game ID
    logger.info(f"\nTesting single game scrape for game ID: {test_game_id}")
    
    game = scraper.scrape_single_game(test_game_id)
    if game:
        logger.info(f"Successfully scraped game: {game.game_info.id}")
        
        # Save the game to database
        scraper.db_manager.save_game(game)
        logger.info("Saved game to database")
        
        # Query the database to verify fields
        session = scraper.db_manager.db.get_session()
        
        # Check game fields
        db_game = session.query(DBGame).filter_by(id=test_game_id).first()
        if db_game:
            logger.info("\n=== Game Fields ===")
            logger.info(f"Weather: {db_game.weather}")
            logger.info(f"Weather Temperature: {db_game.weather_temperature}")
            logger.info(f"Weather Wind Speed: {db_game.weather_wind_speed}")
            logger.info(f"Weather Wind Direction: {db_game.weather_wind_direction}")
            logger.info(f"Weather Precipitation: {db_game.weather_precipitation}")
            logger.info(f"Weather Humidity: {db_game.weather_humidity}")
            logger.info(f"Weather Conditions: {db_game.weather_conditions}")
            
            logger.info(f"\nHome Team Stats:")
            logger.info(f"  Wins: {db_game.home_team_wins}")
            logger.info(f"  Losses: {db_game.home_team_losses}")
            logger.info(f"  Win Streak: {db_game.home_team_win_streak}")
            
            logger.info(f"\nAway Team Stats:")
            logger.info(f"  Wins: {db_game.away_team_wins}")
            logger.info(f"  Losses: {db_game.away_team_losses}")
            logger.info(f"  Win Streak: {db_game.away_team_win_streak}")
            
            # Check play fields
            plays = session.query(DBPlay).filter_by(game_id=test_game_id).limit(5).all()
            logger.info(f"\n=== First 5 Plays ===")
            for i, play in enumerate(plays, 1):
                logger.info(f"\nPlay {i}:")
                logger.info(f"  Description: {play.play_description[:100]}...")
                logger.info(f"  Offensive Formation: {play.offensive_formation}")
                logger.info(f"  Defensive Formation: {play.defensive_formation}")
                logger.info(f"  Defensive Package: {play.defensive_package}")
                logger.info(f"  Defensive Personnel: {play.defensive_dl_count} DL, {play.defensive_lb_count} LB, {play.defensive_db_count} DB")
                logger.info(f"  Defensive Box Count: {play.defensive_box_count}")
                logger.info(f"  Yards Gained: {play.yards_gained}")
                logger.info(f"  Pass Length: {play.pass_length}")
                logger.info(f"  Pass Location: {play.pass_location}")
                logger.info(f"  Run Direction: {play.run_direction}")
                
                # Play result metrics
                if play.is_complete_pass is not None:
                    logger.info(f"  Pass Complete: {play.is_complete_pass}")
                if play.pass_target:
                    logger.info(f"  Pass Target: {play.pass_target}")
                if play.is_sack:
                    logger.info(f"  Sack: {play.is_sack} ({play.sack_yards} yards)")
                if play.is_fumble:
                    logger.info(f"  Fumble: {play.is_fumble}")
                if play.is_interception:
                    logger.info(f"  Interception: {play.is_interception}")
                if play.is_touchdown_pass or play.is_touchdown_run:
                    logger.info(f"  Touchdown: Pass={play.is_touchdown_pass}, Run={play.is_touchdown_run}")
                if play.is_penalty_on_play:
                    logger.info(f"  Penalty: {play.penalty_type} on {play.penalty_team}")
                if play.is_field_goal:
                    logger.info(f"  Field Goal: {play.field_goal_distance} yards - {play.field_goal_result}")
                
                logger.info(f"  Score Differential: {play.score_differential}")
                logger.info(f"  Time Remaining Half: {play.time_remaining_half}")
                logger.info(f"  Time Remaining Game: {play.time_remaining_game}")
                logger.info(f"  Is Two Minute Drill: {play.is_two_minute_drill}")
                logger.info(f"  Is Must Score Situation: {play.is_must_score_situation}")
                
                # Game context features
                if play.drive_number:
                    logger.info(f"  Drive Info: Drive #{play.drive_number}, Play #{play.drive_play_number}")
                if play.field_position_category:
                    logger.info(f"  Field Position: {play.field_position_category} ({play.yards_from_own_endzone} yards from own endzone)")
                if play.is_winning_team is not None:
                    status = "Winning" if play.is_winning_team else ("Losing" if play.is_losing_team else "Tied")
                    logger.info(f"  Game Status: {status}")
                if play.is_comeback_situation:
                    logger.info(f"  Comeback Situation: {play.is_comeback_situation}")
                if play.is_blowout_situation:
                    logger.info(f"  Blowout Situation: {play.is_blowout_situation}")
                if play.game_competitive_index is not None:
                    logger.info(f"  Game Competitiveness: {play.game_competitive_index:.2f}")
                if play.turnover_margin is not None:
                    logger.info(f"  Turnover Margin: {play.turnover_margin}")
                if play.weather_impact_score is not None:
                    logger.info(f"  Weather Impact: {play.weather_impact_score:.2f}")
                if play.is_indoor_game is not None:
                    logger.info(f"  Indoor Game: {play.is_indoor_game}")
        
        session.close()
    else:
        logger.error("Failed to scrape game")
    
    # Clean up
    scraper.close()
    
    logger.info("\n=== Test completed ===")
    logger.info(f"Test database saved at: {test_db_path}")
    logger.info("You can examine the database with: python query_db.py --db-path test_nfl_data.db")

if __name__ == "__main__":
    test_new_fields()