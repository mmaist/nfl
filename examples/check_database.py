#!/usr/bin/env python3
"""
Quick script to check what data was collected in the database.
"""
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.db_utils import NFLDatabaseManager

def main():
    db_manager = NFLDatabaseManager('nfl_data.db')
    
    print("🏈 NFL Database Summary")
    print("=" * 50)
    
    # Get games
    games = db_manager.get_games()
    print(f"📊 Total Games: {len(games)}")
    
    if games:
        recent_games = games[-5:]  # Last 5 games
        print("\n📅 Recent Games:")
        for game in recent_games:
            print(f"  • {game.away_team_id} @ {game.home_team_id} ({game.season} {game.season_type} Week {game.week})")
            print(f"    Score: {game.away_score_total or 0} - {game.home_score_total or 0}")
            print(f"    Status: {game.status}")
            
            # Check if we have weather data
            if hasattr(game, 'weather_temperature') and game.weather_temperature:
                print(f"    Weather: {game.weather_temperature}°F")
            
            # Check plays for this game
            plays = db_manager.get_plays(game_id=game.id)
            print(f"    Plays: {len(plays)}")
            print()
    
    # Get total plays
    all_plays = db_manager.get_plays()
    print(f"🏃 Total Plays: {len(all_plays)}")
    
    if all_plays:
        print("\n📝 Sample Play Types:")
        play_types = {}
        for play in all_plays[-20:]:  # Last 20 plays
            if play.play_type:
                play_types[play.play_type] = play_types.get(play.play_type, 0) + 1
        
        for play_type, count in play_types.items():
            print(f"  • {play_type}: {count}")
    
    # Check players (if the method exists)
    try:
        players = db_manager.get_players()
        print(f"\n👥 Total Players: {len(players)}")
    except AttributeError:
        print(f"\n👥 Players method not available")
    
    # Test a specific query to verify schema works
    try:
        week15_games = db_manager.get_games(season=2024, week='15')
        print(f"\n🗓️  Week 15 2024 Games: {len(week15_games)}")
        
        if week15_games:
            game = week15_games[0]
            print(f"✅ Schema Test: Successfully queried game {game.id}")
            
            # Check if new columns exist and have data
            new_fields = []
            if hasattr(game, 'weather_temperature'):
                new_fields.append(f"weather_temperature: {game.weather_temperature}")
            if hasattr(game, 'home_team_wins'):
                new_fields.append(f"home_team_wins: {game.home_team_wins}")
            if hasattr(game, 'away_team_wins'):
                new_fields.append(f"away_team_wins: {game.away_team_wins}")
            
            if new_fields:
                print("🆕 New Fields Present:")
                for field in new_fields[:3]:  # Show first 3
                    print(f"  • {field}")
            
    except Exception as e:
        print(f"❌ Schema Test Failed: {e}")
    
    print("\n✅ Database check complete!")

if __name__ == "__main__":
    main()