#!/usr/bin/env python3
"""
Query utility for the NFL SQLite database.
"""
import argparse
import sys
import os
import json
from typing import Optional

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.db_utils import NFLDatabaseManager
from src.database.database import DBGame, DBPlay

def print_game_summary(game: DBGame):
    """Print a summary of a game"""
    print(f"\nGame ID: {game.id}")
    print(f"Date: {game.date} {game.time}")
    print(f"{game.away_team_name} @ {game.home_team_name}")
    print(f"Score: {game.away_score_total} - {game.home_score_total}")
    print(f"Status: {game.status}")
    if game.venue_site_full_name:
        print(f"Venue: {game.venue_site_full_name}, {game.venue_site_city}, {game.venue_site_state}")

def print_play_summary(play: DBPlay):
    """Print a summary of a play"""
    print(f"\nQ{play.quarter} {play.game_clock} - {play.play_type}")
    print(f"Down: {play.down}, Distance: {play.yards_to_go}, Yard Line: {play.yardline}")
    print(f"Description: {play.play_description[:100]}...")
    if play.is_scoring:
        print("SCORING PLAY")

def main():
    parser = argparse.ArgumentParser(description='Query NFL database')
    parser.add_argument('--db-path', type=str, default='nfl_data.db', help='Path to SQLite database')
    
    # Query filters
    parser.add_argument('--season', type=int, help='Filter by season')
    parser.add_argument('--week', type=str, help='Filter by week')
    parser.add_argument('--team', type=str, help='Filter by team ID')
    parser.add_argument('--game-id', type=str, help='Filter by specific game ID')
    
    # Query type
    parser.add_argument('--games', action='store_true', help='List games')
    parser.add_argument('--plays', action='store_true', help='List plays')
    parser.add_argument('--stats', action='store_true', help='Show statistics for a game')
    parser.add_argument('--export', type=str, help='Export results to JSON file')
    
    # Play filters
    parser.add_argument('--play-type', type=str, help='Filter plays by type')
    parser.add_argument('--down', type=int, help='Filter plays by down')
    parser.add_argument('--quarter', type=int, help='Filter plays by quarter')
    parser.add_argument('--scoring-only', action='store_true', help='Show only scoring plays')
    parser.add_argument('--limit', type=int, default=50, help='Limit number of results')
    
    args = parser.parse_args()
    
    # Initialize database manager
    db_manager = NFLDatabaseManager(args.db_path)
    
    try:
        if args.games:
            # Query games
            games = db_manager.get_games(
                season=args.season,
                week=args.week,
                team_id=args.team
            )
            
            print(f"\nFound {len(games)} games")
            for game in games[:args.limit]:
                print_game_summary(game)
                
            if args.export:
                # Export to JSON
                export_data = []
                for game in games:
                    export_data.append({
                        'id': game.id,
                        'season': game.season,
                        'week': game.week,
                        'date': game.date,
                        'home_team': game.home_team_name,
                        'away_team': game.away_team_name,
                        'home_score': game.home_score_total,
                        'away_score': game.away_score_total,
                        'status': game.status
                    })
                with open(args.export, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"\nExported {len(export_data)} games to {args.export}")
                
        elif args.plays:
            # Query plays
            if not args.game_id:
                print("Please specify --game-id to query plays")
                return
                
            plays = db_manager.get_plays(
                game_id=args.game_id,
                play_type=args.play_type,
                down=args.down,
                quarter=args.quarter
            )
            
            # Filter scoring plays if requested
            if args.scoring_only:
                plays = [p for p in plays if p.is_scoring]
            
            print(f"\nFound {len(plays)} plays")
            for play in plays[:args.limit]:
                print_play_summary(play)
                
            if args.export:
                # Export to JSON
                export_data = []
                for play in plays:
                    export_data.append({
                        'play_id': play.play_id,
                        'quarter': play.quarter,
                        'game_clock': play.game_clock,
                        'down': play.down,
                        'yards_to_go': play.yards_to_go,
                        'yardline': play.yardline,
                        'play_type': play.play_type,
                        'description': play.play_description,
                        'is_scoring': play.is_scoring,
                        'expected_points': play.expected_points,
                        'expected_points_added': play.expected_points_added
                    })
                with open(args.export, 'w') as f:
                    json.dump(export_data, f, indent=2)
                print(f"\nExported {len(export_data)} plays to {args.export}")
                
        elif args.stats:
            # Show game statistics
            if not args.game_id:
                print("Please specify --game-id to show statistics")
                return
                
            stats = db_manager.get_play_stats(args.game_id)
            
            print(f"\nGame Statistics for {args.game_id}")
            print(f"Total Plays: {stats['total_plays']}")
            print(f"Scoring Plays: {stats['scoring_plays']}")
            print(f"Penalties: {stats['penalties']}")
            print(f"Turnovers: {stats['turnovers']}")
            print(f"Red Zone Plays: {stats['red_zone_plays']}")
            
            print("\nPlay Type Breakdown:")
            for play_type, count in sorted(stats['play_types'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {play_type}: {count}")
                
            print("\nDown Breakdown:")
            for down in sorted(stats['downs'].keys()):
                if stats['downs'][down] > 0:
                    print(f"  {down} down: {stats['downs'][down]}")
                    
            if args.export:
                with open(args.export, 'w') as f:
                    json.dump(stats, f, indent=2)
                print(f"\nExported statistics to {args.export}")
                
        else:
            # Show database summary
            session = db_manager.db.get_session()
            total_games = session.query(DBGame).count()
            total_plays = session.query(DBPlay).count()
            seasons = session.query(DBGame.season).distinct().all()
            session.close()
            
            print(f"\nNFL Database Summary")
            print(f"Path: {args.db_path}")
            print(f"Total Games: {total_games}")
            print(f"Total Plays: {total_plays}")
            print(f"Seasons: {', '.join(str(s[0]) for s in sorted(seasons))}")
            print("\nUse --games, --plays, or --stats to query specific data")
            
    finally:
        db_manager.close()

if __name__ == "__main__":
    main()