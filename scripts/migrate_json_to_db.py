#!/usr/bin/env python3
"""
Migrate existing JSON data files to SQLite database.
"""
import argparse
import json
import os
from glob import glob
from db_utils import NFLDatabaseManager
from models import NFLData, Game
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_json_file(json_path: str, db_manager: NFLDatabaseManager) -> int:
    """Migrate a single JSON file to the database."""
    logger.info(f"Processing {json_path}...")
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Validate data structure
        nfl_data = NFLData.model_validate(data)
        
        # Count games migrated
        game_count = 0
        
        # Iterate through all games in the data
        for season_data in nfl_data.seasons.values():
            for season_type_data in season_data.types.values():
                for week_data in season_type_data.weeks.values():
                    for game in week_data.games:
                        try:
                            db_manager.save_game(game)
                            game_count += 1
                        except Exception as e:
                            logger.error(f"Error saving game {game.game_info.id}: {e}")
        
        logger.info(f"Migrated {game_count} games from {json_path}")
        return game_count
        
    except Exception as e:
        logger.error(f"Error processing {json_path}: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='Migrate NFL JSON data to SQLite database')
    parser.add_argument('--json-dir', type=str, default='data', help='Directory containing JSON files')
    parser.add_argument('--json-file', type=str, help='Specific JSON file to migrate')
    parser.add_argument('--db-path', type=str, default='nfl_data.db', help='Path to SQLite database')
    parser.add_argument('--pattern', type=str, default='*.json', help='File pattern to match')
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = NFLDatabaseManager(args.db_path)
    
    try:
        total_games = 0
        
        if args.json_file:
            # Migrate specific file
            total_games = migrate_json_file(args.json_file, db_manager)
        else:
            # Find all JSON files in directory
            json_files = glob(os.path.join(args.json_dir, args.pattern))
            logger.info(f"Found {len(json_files)} JSON files to process")
            
            for json_file in sorted(json_files):
                game_count = migrate_json_file(json_file, db_manager)
                total_games += game_count
        
        logger.info(f"\nMigration complete! Total games migrated: {total_games}")
        
        # Show database summary
        session = db_manager.db.get_session()
        from database import DBGame
        db_games = session.query(DBGame).count()
        session.close()
        
        logger.info(f"Database now contains {db_games} games")
        
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()