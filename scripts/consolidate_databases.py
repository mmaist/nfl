#!/usr/bin/env python3
"""
Consolidate multiple season databases into a single unified database.
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.db_utils import NFLDatabaseManager
from src.database.database import DBGame, DBPlay, DBPlayer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def consolidate_databases(source_dbs, target_db_path, backup=True):
    """
    Consolidate multiple databases into a single target database.
    
    Args:
        source_dbs: List of source database paths
        target_db_path: Path to the target consolidated database
        backup: Whether to create backups of existing databases
    """
    print(f"Starting database consolidation at {datetime.now()}")
    
    # Create backup if requested
    if backup and os.path.exists(target_db_path):
        backup_path = f"{target_db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy2(target_db_path, backup_path)
    
    # Initialize target database
    print(f"Initializing target database: {target_db_path}")
    target_manager = NFLDatabaseManager(target_db_path)
    
    # Track statistics
    total_games = 0
    total_plays = 0
    total_players = 0
    errors = []
    
    # Process each source database
    for source_db in source_dbs:
        if not os.path.exists(source_db):
            print(f"Warning: Source database not found: {source_db}")
            continue
            
        print(f"\nProcessing: {source_db}")
        
        try:
            # Connect to source database
            source_conn = sqlite3.connect(source_db)
            source_conn.row_factory = sqlite3.Row
            cursor = source_conn.cursor()
            
            # Get statistics
            game_count = cursor.execute("SELECT COUNT(*) FROM games").fetchone()[0]
            play_count = cursor.execute("SELECT COUNT(*) FROM plays").fetchone()[0]
            player_count = cursor.execute("SELECT COUNT(*) FROM players").fetchone()[0]
            
            print(f"  Found: {game_count} games, {play_count} plays, {player_count} players")
            
            # Get a session from target manager
            target_session = target_manager.db.get_session()
            
            # Copy games
            print("  Copying games...")
            games_copied = 0
            cursor.execute("SELECT * FROM games")
            for row in cursor:
                game_data = dict(row)
                try:
                    # Check if game already exists
                    existing = target_session.query(DBGame).filter_by(
                        id=game_data['id']
                    ).first()
                    
                    if not existing:
                        # Convert date strings to datetime objects
                        date_fields = ['date', 'created_at', 'updated_at', 'betting_updated_at']
                        for field in date_fields:
                            if field in game_data and game_data[field]:
                                try:
                                    if isinstance(game_data[field], str):
                                        # Parse ISO format date
                                        game_data[field] = datetime.fromisoformat(game_data[field].replace('Z', '+00:00'))
                                except Exception:
                                    # If parsing fails, set to None
                                    game_data[field] = None
                        
                        # ID field is the game_id in the database, no need to modify
                        
                        game = DBGame(**game_data)
                        target_session.add(game)
                        games_copied += 1
                except Exception as e:
                    errors.append(f"Error copying game {game_data.get('id')}: {str(e)}")
            
            target_session.commit()
            print(f"  Copied {games_copied} new games")
            
            # Copy plays
            print("  Copying plays...")
            plays_copied = 0
            cursor.execute("SELECT * FROM plays")
            for row in cursor:
                play_data = dict(row)
                try:
                    # Check if play already exists
                    existing = target_session.query(DBPlay).filter_by(
                        game_id=play_data['game_id'],
                        play_id=play_data['play_id']
                    ).first()
                    
                    if not existing:
                        # Convert date strings to datetime objects
                        date_fields = ['time_of_day_utc', 'created_at']
                        for field in date_fields:
                            if field in play_data and play_data[field]:
                                try:
                                    if isinstance(play_data[field], str):
                                        # Parse ISO format date
                                        play_data[field] = datetime.fromisoformat(play_data[field].replace('Z', '+00:00'))
                                except Exception:
                                    # If parsing fails, set to None
                                    play_data[field] = None
                        
                        # Convert JSON string fields if needed
                        json_fields = ['play_stats_json', 'home_personnel_json', 'away_personnel_json']
                        for field in json_fields:
                            if field in play_data and play_data[field] and isinstance(play_data[field], str):
                                try:
                                    play_data[field] = json.loads(play_data[field])
                                except Exception:
                                    # If parsing fails, keep as is
                                    pass
                        
                        # Remove ID field to let database auto-generate it
                        if 'id' in play_data:
                            del play_data['id']
                        
                        play = DBPlay(**play_data)
                        target_session.add(play)
                        plays_copied += 1
                except Exception as e:
                    errors.append(f"Error copying play {play_data.get('play_id')}: {str(e)}")
            
            target_session.commit()
            print(f"  Copied {plays_copied} new plays")
            
            # Copy players
            print("  Copying players...")
            players_copied = 0
            cursor.execute("SELECT * FROM players")
            for row in cursor:
                player_data = dict(row)
                try:
                    # Check if player already exists
                    existing = target_session.query(DBPlayer).filter_by(
                        gsis_id=player_data['gsis_id']
                    ).first()
                    
                    if not existing:
                        # Convert date strings to datetime objects
                        date_fields = ['created_at', 'updated_at']
                        for field in date_fields:
                            if field in player_data and player_data[field]:
                                try:
                                    if isinstance(player_data[field], str):
                                        # Parse ISO format date
                                        player_data[field] = datetime.fromisoformat(player_data[field].replace('Z', '+00:00'))
                                except Exception:
                                    # If parsing fails, set to None
                                    player_data[field] = None
                        
                        # Remove ID field to let database auto-generate it
                        if 'id' in player_data:
                            del player_data['id']
                        
                        player = DBPlayer(**player_data)
                        target_session.add(player)
                        players_copied += 1
                except Exception as e:
                    errors.append(f"Error copying player {player_data.get('gsis_id')}: {str(e)}")
            
            target_session.commit()
            print(f"  Copied {players_copied} new players")
            
            # Close the session for this source database
            target_session.close()
            
            # Update totals
            total_games += games_copied
            total_plays += plays_copied
            total_players += players_copied
            
            source_conn.close()
            
        except Exception as e:
            print(f"Error processing {source_db}: {str(e)}")
            errors.append(f"Database error {source_db}: {str(e)}")
            continue
    
    # Final statistics
    print("\n" + "="*50)
    print("Consolidation Complete!")
    print(f"Total new games added: {total_games}")
    print(f"Total new plays added: {total_plays}")
    print(f"Total new players added: {total_players}")
    
    # Verify final counts
    final_session = target_manager.db.get_session()
    final_games = final_session.query(DBGame).count()
    final_plays = final_session.query(DBPlay).count()
    final_players = final_session.query(DBPlayer).count()
    final_session.close()
    
    print(f"\nFinal database totals:")
    print(f"  Games: {final_games}")
    print(f"  Plays: {final_plays}")
    print(f"  Players: {final_players}")
    
    if errors:
        print(f"\nErrors encountered ({len(errors)}):")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
    
    target_manager.close()
    return total_games, total_plays, total_players, errors


def main():
    # Define source databases
    databases_dir = Path("databases")
    source_databases = [
        databases_dir / "nfl_2022_complete.db",
        databases_dir / "nfl_2023_complete.db", 
        databases_dir / "nfl_2024_complete.db",
        "nfl_production.db"  # Include production database too
    ]
    
    # Target consolidated database
    target_database = "nfl_consolidated.db"
    
    print("NFL Database Consolidation")
    print("=" * 50)
    print(f"Source databases:")
    for db in source_databases:
        if os.path.exists(db):
            size_mb = os.path.getsize(db) / (1024 * 1024)
            print(f"  ✓ {db} ({size_mb:.1f} MB)")
        else:
            print(f"  ✗ {db} (not found)")
    
    print(f"\nTarget database: {target_database}")
    print("\nStarting consolidation...")
    
    # Run consolidation
    games, plays, players, errors = consolidate_databases(
        source_databases, 
        target_database,
        backup=True
    )
    
    print("\nConsolidation completed successfully!" if not errors else 
          f"\nConsolidation completed with {len(errors)} errors.")


if __name__ == "__main__":
    main()