#!/usr/bin/env python3
"""
Main entry point for the NFL Data Scraper.
"""

import sys
import os
from src.scraper.scraper import NFLGameScraper

def main():
    """Main entry point for the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='NFL Game Data Scraper')
    parser.add_argument('--api-only', action='store_true',
                        help='Use API-only mode (no web scraping)')
    parser.add_argument('--season', type=int, default=2024,
                        help='Season to scrape (default: 2024)')
    parser.add_argument('--week', type=str, default='current',
                        help='Week to scrape (default: current)')
    parser.add_argument('--test-data', action='store_true',
                        help='Use test data instead of live scraping')
    parser.add_argument('--game-id', type=str,
                        help='Scrape a specific game ID')
    parser.add_argument('--db-path', type=str, default='nfl_data.db',
                        help='Database path (default: nfl_data.db)')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = NFLGameScraper(
        api_only=args.api_only,
        use_database=True,
        db_path=args.db_path
    )
    
    try:
        if args.game_id:
            # Scrape single game
            print(f"Scraping single game: {args.game_id}")
            game = scraper.scrape_single_game(args.game_id)
            if game:
                print(f"Successfully scraped game: {game.game_info.id}")
                
                # Save to database if enabled
                if scraper.use_database and scraper.db_manager:
                    try:
                        scraper.db_manager.save_game(game)
                        print(f"Successfully saved game {game.game_info.id} to database")
                        
                        # Get play count for verification
                        play_count = len(game.plays) if game.plays else 0
                        print(f"Saved {play_count} plays to database")
                    except Exception as e:
                        print(f"Error saving to database: {e}")
            else:
                print("Failed to scrape game")
        elif args.test_data:
            # Use test data
            print("Using test data...")
            scraper.scrape_with_test_data()
        else:
            # Scrape season/week
            print(f"Scraping season {args.season}, week {args.week}")
            if args.week == 'current':
                # Scrape current week
                week_data = scraper.fetch_api_data(args.season, 'REG', 'current')
            else:
                # Scrape specific week
                week_str = f"WEEK_{args.week}" if args.week != 'current' else args.week
                week_data = scraper.fetch_api_data(args.season, 'REG', week_str)
            
            if week_data:
                print(f"Successfully scraped {len(week_data.games)} games")
            else:
                print("No data collected")
    
    finally:
        scraper.close()

if __name__ == "__main__":
    main()