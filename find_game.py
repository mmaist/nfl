#!/usr/bin/env python3
"""
Find the scraped game in the database.
"""
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.db_utils import NFLDatabaseManager

def main():
    db_manager = NFLDatabaseManager('nfl_data.db')
    
    # Target game ID
    target_id = "45c16f16-1313-11ef-afd1-646009f18b2e"
    
    print(f"🔍 Searching for game: {target_id}")
    print("=" * 60)
    
    # Get all games
    all_games = db_manager.get_games()
    print(f"Total games in database: {len(all_games)}")
    
    # Search for the game
    found_game = None
    for game in all_games:
        if target_id in game.id:
            found_game = game
            break
    
    if found_game:
        print(f"✅ Found game: {found_game.id}")
        
        # Get plays
        plays = db_manager.get_plays(game_id=found_game.id)
        print(f"Plays in this game: {len(plays)}")
        
        if plays:
            print(f"\nLast few plays added:")
            for play in plays[-3:]:
                print(f"  • {play.play_description[:80]}...")
    else:
        print(f"❌ Game not found")
        
        # Show recent games
        print(f"\nMost recent games:")
        for game in all_games[-10:]:
            print(f"  • {game.id} - {game.away_team_id} @ {game.home_team_id}")
            
        # Check if there are any games from week 15
        week15_games = [g for g in all_games if g.week == '15' or g.week == 'WEEK_15']
        print(f"\nWeek 15 games: {len(week15_games)}")
        for game in week15_games:
            print(f"  • {game.id} - {game.away_team_id} @ {game.home_team_id}")

if __name__ == "__main__":
    main()