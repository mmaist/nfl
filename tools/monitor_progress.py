#!/usr/bin/env python3
"""Monitor production scraper progress."""

import sqlite3
import time
import sys
from datetime import datetime

def get_stats(db_path):
    """Get current statistics from the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("SELECT COUNT(*) FROM games")
    total_games = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM plays")
    total_plays = cursor.fetchone()[0]
    
    # By season and type
    cursor.execute("""
        SELECT season, season_type, COUNT(*) as games, 
               (SELECT COUNT(*) FROM plays p WHERE p.game_id IN 
                (SELECT id FROM games g2 WHERE g2.season = g.season AND g2.season_type = g.season_type))
               as plays
        FROM games g
        GROUP BY season, season_type
        ORDER BY season, season_type
    """)
    
    season_stats = cursor.fetchall()
    conn.close()
    
    return total_games, total_plays, season_stats

def main():
    db_path = "nfl_production.db"
    
    print("NFL Production Scraper Progress Monitor")
    print("Press Ctrl+C to exit")
    print("="*60)
    
    last_games = 0
    last_plays = 0
    
    while True:
        try:
            total_games, total_plays, season_stats = get_stats(db_path)
            
            # Calculate rates
            games_added = total_games - last_games
            plays_added = total_plays - last_plays
            
            # Clear screen and show stats
            print("\033[2J\033[H")  # Clear screen
            print(f"NFL Production Scraper Progress - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*60)
            print(f"Total Games: {total_games:,} (+{games_added})")
            print(f"Total Plays: {total_plays:,} (+{plays_added})")
            print()
            print("Season Breakdown:")
            print("-"*40)
            print("Season | Type | Games | Plays")
            print("-"*40)
            
            for season, season_type, games, plays in season_stats:
                print(f"{season:6} | {season_type:4} | {games:5} | {plays:,}")
            
            print("-"*40)
            print()
            print("Estimated Progress:")
            # Rough estimates: 272 games per season REG, 11-13 games POST
            expected_reg_games = 272 * 3  # 3 seasons
            expected_post_games = 36  # ~12 per season
            expected_total = expected_reg_games + expected_post_games
            
            progress = (total_games / expected_total) * 100
            print(f"[{'█' * int(progress/2)}{' ' * (50-int(progress/2))}] {progress:.1f}%")
            
            last_games = total_games
            last_plays = total_plays
            
            time.sleep(10)  # Update every 10 seconds
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()