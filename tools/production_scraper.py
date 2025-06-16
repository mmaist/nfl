#!/usr/bin/env python3
"""
Production NFL scraper for multiple seasons.
Scrapes all regular season and postseason games for specified years.
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import List, Dict
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_utils import NFLDatabaseManager
from tools.parallel_scraper import parallel_scrape_week
from src.scraper.scraper import NFLGameScraper


def get_games_for_week_type(season: int, week: int, season_type: str = "REG") -> List[str]:
    """Get list of game IDs for a specific week and season type."""
    try:
        scraper = NFLGameScraper(api_only=True)

        # Get live scores which contains all games for the week
        if season_type == "REG":
            week_str = f"WEEK_{week}"
        else:  # POST
            week_str = str(week)  # Postseason uses numeric weeks: 1, 2, 3, 4
        
        live_scores = scraper.get_live_scores(season, season_type, week_str)
        
        if not live_scores or "games" not in live_scores:
            logging.info("No games data in response")
            return []

        # Extract game IDs
        game_ids = []
        for game in live_scores["games"]:
            if "gameId" in game:
                game_ids.append(game["gameId"])

        logging.info(f"Found {len(game_ids)} games for {season} {season_type} Week {week}")
        return game_ids

    except Exception as e:
        logging.error(f"Error fetching games for week: {e}")
        return []


def setup_logging(log_file: str = None):
    """Setup logging configuration."""
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def scrape_season_type(
    season: int, 
    season_type: str, 
    db_path: str, 
    max_workers: int = 6,
    weeks: List[int] = None
) -> Dict:
    """
    Scrape all weeks for a specific season type.
    
    Args:
        season: NFL season year
        season_type: Either 'REG' or 'POST'
        db_path: Path to database file
        max_workers: Number of parallel workers
        weeks: List of week numbers to scrape (defaults to all)
        
    Returns:
        Dictionary with aggregated results
    """
    # Determine weeks to scrape
    if weeks is None:
        if season_type == 'REG':
            # Regular season: 18 weeks for 2021+, 17 weeks before
            weeks = list(range(1, 19))
        else:  # POST
            # Postseason: Wild Card (1), Divisional (2), Conference (3), Super Bowl (4)
            weeks = [1, 2, 3, 4]
    
    logging.info(f"Starting scrape for {season} {season_type} - {len(weeks)} weeks")
    
    total_results = {
        'season': season,
        'season_type': season_type,
        'weeks_processed': 0,
        'total_games': 0,
        'successful_games': 0,
        'failed_games': 0,
        'total_plays': 0,
        'errors': []
    }
    
    for week in weeks:
        logging.info(f"\n{'='*60}")
        logging.info(f"Processing {season} {season_type} Week {week}")
        logging.info(f"{'='*60}")
        
        try:
            # Check if week has games
            game_ids = get_games_for_week_type(season, week, season_type)
            
            if not game_ids:
                logging.info(f"No games found for Week {week} - skipping")
                continue
            
            # For postseason, we need to handle this differently since parallel_scrape_week expects REG
            if season_type == 'POST':
                # Directly scrape postseason games
                from concurrent.futures import ProcessPoolExecutor, as_completed
                from parallel_scraper import scrape_single_game
                
                week_results = {
                    'total': len(game_ids),
                    'success': 0,
                    'failed': 0,
                    'failed_games': []
                }
                
                scraper_config = {
                    "api_only": True,
                    "db_path": db_path,
                    "save_to_db": True,
                    "skip_play_summaries": False  # Get detailed play statistics
                }
                
                work_items = [(game_id, scraper_config) for game_id in game_ids]
                
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(scrape_single_game, item): item[0] 
                        for item in work_items
                    }
                    
                    for future in as_completed(futures):
                        game_id, success, error = future.result()
                        
                        if success:
                            week_results['success'] += 1
                        else:
                            week_results['failed'] += 1
                            week_results['failed_games'].append((game_id, error))
                            
                logging.info(f"Week {week} complete: {week_results['success']}/{week_results['total']} games successful")
                
            else:
                # Regular season - use parallel_scrape_week
                week_results = parallel_scrape_week(
                    season=season,
                    week=week,
                    max_workers=max_workers,
                    api_only=True,
                    db_path=db_path,
                    retry_failed=True
                )
            
            # Update totals
            total_results['weeks_processed'] += 1
            total_results['total_games'] += week_results['total']
            total_results['successful_games'] += week_results['success']
            total_results['failed_games'] += week_results['failed']
            
            if week_results.get('failed_games'):
                for game_id, error in week_results['failed_games']:
                    total_results['errors'].append({
                        'week': week,
                        'game_id': game_id,
                        'error': error
                    })
            
            # Small delay between weeks
            time.sleep(2)
            
        except Exception as e:
            logging.error(f"Error processing week {week}: {e}")
            total_results['errors'].append({
                'week': week,
                'error': str(e)
            })
    
    # Get play count from database
    try:
        db_manager = NFLDatabaseManager(db_path)
        with db_manager.get_session() as session:
            play_count = session.execute(
                f"SELECT COUNT(*) FROM plays WHERE game_id IN "
                f"(SELECT id FROM games WHERE season={season} AND season_type='{season_type}')"
            ).scalar()
            total_results['total_plays'] = play_count
    except Exception as e:
        logging.error(f"Error counting plays: {e}")
    
    return total_results


def scrape_multiple_seasons(
    seasons: List[int],
    db_path: str,
    max_workers: int = 6,
    season_types: List[str] = ['REG', 'POST']
) -> Dict:
    """
    Scrape multiple seasons and season types.
    
    Args:
        seasons: List of season years to scrape
        db_path: Path to database file
        max_workers: Number of parallel workers
        season_types: List of season types to scrape
        
    Returns:
        Dictionary with all results
    """
    all_results = {
        'start_time': datetime.now().isoformat(),
        'seasons': {},
        'summary': {
            'total_games': 0,
            'successful_games': 0,
            'failed_games': 0,
            'total_plays': 0
        }
    }
    
    for season in seasons:
        all_results['seasons'][season] = {}
        
        for season_type in season_types:
            logging.info(f"\n{'#'*80}")
            logging.info(f"STARTING {season} {season_type} SEASON")
            logging.info(f"{'#'*80}\n")
            
            results = scrape_season_type(
                season=season,
                season_type=season_type,
                db_path=db_path,
                max_workers=max_workers
            )
            
            all_results['seasons'][season][season_type] = results
            
            # Update summary
            all_results['summary']['total_games'] += results['total_games']
            all_results['summary']['successful_games'] += results['successful_games']
            all_results['summary']['failed_games'] += results['failed_games']
            all_results['summary']['total_plays'] += results['total_plays']
            
            # Log season type summary
            logging.info(f"\n{season} {season_type} Summary:")
            logging.info(f"  Games: {results['successful_games']}/{results['total_games']}")
            logging.info(f"  Plays: {results['total_plays']}")
            
            if results['errors']:
                logging.warning(f"  Errors: {len(results['errors'])}")
            
            # Longer delay between season types
            time.sleep(5)
    
    all_results['end_time'] = datetime.now().isoformat()
    
    return all_results


def print_final_report(results: Dict):
    """Print a comprehensive final report."""
    print("\n" + "="*80)
    print("PRODUCTION SCRAPE COMPLETE")
    print("="*80)
    
    print(f"\nTime Range: {results['start_time']} to {results['end_time']}")
    
    print("\nOVERALL SUMMARY:")
    print(f"  Total Games Processed: {results['summary']['total_games']}")
    print(f"  Successful Games: {results['summary']['successful_games']}")
    print(f"  Failed Games: {results['summary']['failed_games']}")
    print(f"  Success Rate: {results['summary']['successful_games']/max(results['summary']['total_games'], 1)*100:.1f}%")
    print(f"  Total Plays: {results['summary']['total_plays']:,}")
    
    print("\nSEASON BREAKDOWN:")
    for season, season_data in results['seasons'].items():
        print(f"\n{season} Season:")
        for season_type, type_data in season_data.items():
            print(f"  {season_type}: {type_data['successful_games']}/{type_data['total_games']} games, "
                  f"{type_data['total_plays']:,} plays")
            if type_data['errors']:
                print(f"    Errors: {len(type_data['errors'])}")
    
    # List all errors
    all_errors = []
    for season, season_data in results['seasons'].items():
        for season_type, type_data in season_data.items():
            for error in type_data.get('errors', []):
                error['season'] = season
                error['season_type'] = season_type
                all_errors.append(error)
    
    if all_errors:
        print(f"\nERRORS ({len(all_errors)} total):")
        for error in all_errors[:10]:  # Show first 10 errors
            print(f"  - {error['season']} {error['season_type']} Week {error.get('week', '?')}: "
                  f"{error.get('game_id', 'N/A')} - {error.get('error', error)}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more errors")


def main():
    """Main entry point for production scraper."""
    parser = argparse.ArgumentParser(description='Production NFL scraper for multiple seasons')
    parser.add_argument('--seasons', nargs='+', type=int, default=[2022, 2023, 2024],
                       help='List of seasons to scrape')
    parser.add_argument('--season-types', nargs='+', default=['REG', 'POST'],
                       help='Season types to scrape (REG, POST)')
    parser.add_argument('--workers', type=int, default=6,
                       help='Number of parallel workers')
    parser.add_argument('--db-path', default='nfl_production.db',
                       help='Database file path')
    parser.add_argument('--log-file', help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_file)
    
    # Initialize database
    logging.info(f"Initializing database at {args.db_path}")
    db_manager = NFLDatabaseManager(args.db_path)
    logging.info("Database initialized")
    
    # Run the scraper
    results = scrape_multiple_seasons(
        seasons=args.seasons,
        db_path=args.db_path,
        max_workers=args.workers,
        season_types=args.season_types
    )
    
    # Print final report
    print_final_report(results)
    
    # Save results to JSON
    import json
    results_file = f"production_scrape_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to: {results_file}")


if __name__ == '__main__':
    main()