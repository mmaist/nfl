#!/usr/bin/env python3
"""
Parallel NFL game scraper with progress tracking.
Processes multiple games concurrently for better scalability.
"""

import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Tuple, Optional
import multiprocessing
import sys
from tqdm import tqdm
from datetime import datetime
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.scraper import NFLGameScraper
from src.database.db_utils import NFLDatabaseManager


def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(
                f"parallel_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            ),
            logging.StreamHandler(sys.stdout),
        ],
    )


def scrape_single_game(args: Tuple[str, dict]) -> Tuple[str, bool, Optional[str]]:
    """
    Scrape a single game. This function runs in a separate process.

    Args:
        args: Tuple of (game_id, scraper_config)

    Returns:
        Tuple of (game_id, success, error_message)
    """
    game_id, config = args

    # Setup logging for this process
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s - [Game {game_id[:8]}...] - %(levelname)s - %(message)s",
    )

    try:
        # Create scraper instance for this process
        scraper = NFLGameScraper(
            api_only=config.get("api_only", True),
            use_database=False,  # Don't let scraper manage DB
            db_path=config.get("db_path", "nfl_data.db"),
            skip_play_summaries=config.get("skip_play_summaries", True)  # Skip detailed stats for speed
        )

        # Scrape the single game
        logging.info(f"Starting scrape for game {game_id}")
        game = scraper.scrape_single_game(game_id)

        if game:
            # Save to database
            if config.get("save_to_db", True):
                db_manager = NFLDatabaseManager(config.get("db_path", "nfl_data.db"))
                
                try:
                    # Save the game directly
                    saved_game = db_manager.save_game(game)
                    plays_count = len(game.plays) if game.plays else 0
                    logging.info(
                        f"Saved game {game_id} with {plays_count} plays to database"
                    )
                except Exception as e:
                    logging.error(f"Failed to save game {game_id} to database: {e}")
                    raise

            return (game_id, True, None)
        else:
            return (game_id, False, "No data returned")

    except Exception as e:
        error_msg = f"Error scraping game {game_id}: {str(e)}"
        logging.error(error_msg)
        return (game_id, False, str(e))


def get_games_for_week(season: int, week: int) -> List[str]:
    """Get list of game IDs for a specific week."""
    try:
        scraper = NFLGameScraper(api_only=True)

        # Get live scores which contains all games for the week
        week_str = f"WEEK_{week}"
        live_scores = scraper.get_live_scores(season, "REG", week_str)
        
        if not live_scores or "games" not in live_scores:
            logging.error("No games data in response")
            return []

        # Extract game IDs
        game_ids = []
        for game in live_scores["games"]:
            if "gameId" in game:
                game_ids.append(game["gameId"])

        logging.info(f"Found {len(game_ids)} games for {season} Week {week}")
        return game_ids

    except Exception as e:
        logging.error(f"Error fetching games for week: {e}")
        return []


def parallel_scrape_week(
    season: int,
    week: int,
    max_workers: Optional[int] = None,
    api_only: bool = True,
    db_path: str = "nfl_data.db",
    retry_failed: bool = True,
) -> dict:
    """
    Scrape all games for a week in parallel.

    Args:
        season: NFL season year
        week: Week number
        max_workers: Maximum number of parallel workers (defaults to CPU count)
        api_only: Whether to use API-only mode
        db_path: Path to database file
        retry_failed: Whether to retry failed games

    Returns:
        Dictionary with results summary
    """
    if max_workers is None:
        max_workers = min(multiprocessing.cpu_count(), 8)  # Cap at 8 workers

    logging.info(
        f"Starting parallel scrape for {season} Week {week} with {max_workers} workers"
    )

    # Get game IDs for the week
    game_ids = get_games_for_week(season, week)

    if not game_ids:
        logging.error("No games found for the specified week")
        return {"total": 0, "success": 0, "failed": 0}

    # Prepare scraper config for each process
    scraper_config = {
        "api_only": api_only,
        "db_path": db_path,
        "save_to_db": True,
        "skip_play_summaries": False  # Get detailed statistics
    }

    # Create work items
    work_items = [(game_id, scraper_config) for game_id in game_ids]

    results = {"total": len(game_ids), "success": 0, "failed": 0, "failed_games": []}

    # Process games in parallel with progress bar
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_game = {
            executor.submit(scrape_single_game, item): item[0] for item in work_items
        }

        # Process completed tasks with progress bar
        with tqdm(total=len(game_ids), desc="Scraping games", unit="game") as pbar:
            for future in as_completed(future_to_game):
                game_id, success, error = future.result()

                if success:
                    results["success"] += 1
                    pbar.set_postfix(
                        {"success": results["success"], "failed": results["failed"]}
                    )
                else:
                    results["failed"] += 1
                    results["failed_games"].append((game_id, error))
                    pbar.set_postfix(
                        {"success": results["success"], "failed": results["failed"]}
                    )

                pbar.update(1)

    # Retry failed games if requested
    if retry_failed and results["failed_games"]:
        logging.info(f"Retrying {len(results['failed_games'])} failed games...")

        retry_items = [
            (game_id, scraper_config) for game_id, _ in results["failed_games"]
        ]

        with ProcessPoolExecutor(max_workers=max(1, max_workers // 2)) as executor:
            with tqdm(
                total=len(retry_items), desc="Retrying failed games", unit="game"
            ) as pbar:
                futures = [
                    executor.submit(scrape_single_game, item) for item in retry_items
                ]

                for future in as_completed(futures):
                    game_id, success, error = future.result()

                    if success:
                        results["success"] += 1
                        results["failed"] -= 1
                        # Remove from failed list
                        results["failed_games"] = [
                            (gid, err)
                            for gid, err in results["failed_games"]
                            if gid != game_id
                        ]

                    pbar.update(1)

    # Log summary
    logging.info(
        f"Scraping complete: {results['success']}/{results['total']} games successful"
    )

    if results["failed_games"]:
        logging.error("Failed games:")
        for game_id, error in results["failed_games"]:
            logging.error(f"  - {game_id}: {error}")

    return results


def main():
    """Main entry point for parallel scraper."""
    parser = argparse.ArgumentParser(description="Parallel NFL game scraper")
    parser.add_argument("--season", type=int, default=2024, help="NFL season")
    parser.add_argument("--week", type=int, required=True, help="Week number")
    parser.add_argument("--workers", type=int, help="Number of parallel workers")
    parser.add_argument(
        "--api-only",
        action="store_true",
        default=True,
        help="Use API-only mode (no web scraping)",
    )
    parser.add_argument("--db-path", default="nfl_data.db", help="Database file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    parser.add_argument(
        "--no-retry", action="store_true", help="Disable retry for failed games"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    
    # Initialize database to avoid race conditions
    logging.info(f"Initializing database at {args.db_path}")
    db_manager = NFLDatabaseManager(args.db_path)
    logging.info("Database initialized successfully")

    # Run parallel scraper
    results = parallel_scrape_week(
        season=args.season,
        week=args.week,
        max_workers=args.workers,
        api_only=args.api_only,
        db_path=args.db_path,
        retry_failed=not args.no_retry,
    )

    # Exit with error code if any games failed
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
