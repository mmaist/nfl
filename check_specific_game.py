#!/usr/bin/env python3
"""
Check specific game data that was just scraped.
"""
import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.database.db_utils import NFLDatabaseManager

def main():
    db_manager = NFLDatabaseManager('nfl_data.db')
    
    # Check the specific game we just scraped
    game_id = "45c16f16-1313-11ef-afd1-646009f18b2e"
    
    print(f"🎯 Checking Game: {game_id}")
    print("=" * 60)
    
    # Get the specific game
    games = db_manager.get_games()
    target_game = None
    for game in games:
        if game.id == game_id:
            target_game = game
            break
    
    if target_game:
        print(f"✅ Game Found!")
        print(f"  Teams: {target_game.away_team_id} @ {target_game.home_team_id}")
        print(f"  Score: {target_game.away_score_total} - {target_game.home_score_total}")
        print(f"  Status: {target_game.status}")
        print(f"  Season: {target_game.season} {target_game.season_type} Week {target_game.week}")
        
        # Check new fields
        print(f"\n🌤️  Weather Data:")
        if hasattr(target_game, 'weather_temperature') and target_game.weather_temperature:
            print(f"  Temperature: {target_game.weather_temperature}°F")
            print(f"  Wind: {target_game.weather_wind_speed} mph {target_game.weather_wind_direction}")
            print(f"  Conditions: {target_game.weather_conditions}")
        else:
            print(f"  No weather data found")
        
        # Check team stats
        print(f"\n📊 Team Stats:")
        if hasattr(target_game, 'home_team_wins') and target_game.home_team_wins is not None:
            print(f"  Home Team Record: {target_game.home_team_wins}-{target_game.home_team_losses}")
            print(f"  Away Team Record: {target_game.away_team_wins}-{target_game.away_team_losses}")
        else:
            print(f"  No team stats found")
        
        # Get plays for this game
        plays = db_manager.get_plays(game_id=game_id)
        print(f"\n🏈 Plays: {len(plays)} total")
        
        if plays:
            print(f"\n📝 Sample Plays (first 3):")
            for i, play in enumerate(plays[:3]):
                print(f"  {i+1}. Q{play.quarter} - {play.play_description[:60]}...")
                
                # Check new play fields
                if hasattr(play, 'offensive_formation') and play.offensive_formation:
                    print(f"     Formation: {play.offensive_formation}")
                if hasattr(play, 'yards_gained') and play.yards_gained is not None:
                    print(f"     Yards: {play.yards_gained}")
                if hasattr(play, 'pass_length') and play.pass_length:
                    print(f"     Pass: {play.pass_length} {play.pass_location or ''}")
                print()
                
            # Play type breakdown
            play_types = {}
            formations = {}
            for play in plays:
                if play.play_type:
                    play_types[play.play_type] = play_types.get(play.play_type, 0) + 1
                if hasattr(play, 'offensive_formation') and play.offensive_formation:
                    formations[play.offensive_formation] = formations.get(play.offensive_formation, 0) + 1
            
            print(f"📈 Play Type Summary:")
            for play_type, count in sorted(play_types.items()):
                print(f"  • {play_type}: {count}")
            
            if formations:
                print(f"\n🏗️  Formation Summary:")
                for formation, count in sorted(formations.items()):
                    print(f"  • {formation}: {count}")
        
    else:
        print(f"❌ Game {game_id} not found in database")
        print(f"Available games:")
        for game in games[-5:]:
            print(f"  • {game.id}")

if __name__ == "__main__":
    main()