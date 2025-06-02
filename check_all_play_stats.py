#!/usr/bin/env python3
"""Check if any plays have stats in the API response"""

import os
from dotenv import load_dotenv
from scrapeVideos import NFLGameScraper
import time

load_dotenv()

# Create scraper
scraper = NFLGameScraper(api_only=True, skip_play_summaries=False)

game_id = "7d4019ca-1312-11ef-afd1-646009f18b2e"

# Get plays for the game
plays_data = scraper.get_plays_data(2024, "REG", "WEEK_1", game_id)

if plays_data and plays_data.plays:
    print(f"Checking {len(plays_data.plays)} plays...")
    
    plays_with_stats = 0
    total_stats = 0
    
    # Check first 10 plays
    for i, play in enumerate(plays_data.plays[:10]):
        print(f"\nPlay {i+1} (ID: {play.play_id}): {play.play_description[:60]}...")
        
        summary = scraper.get_play_summary(game_id, play.play_id)
        if summary and summary.play and hasattr(summary.play, 'play_stats'):
            if summary.play.play_stats:
                plays_with_stats += 1
                total_stats += len(summary.play.play_stats)
                print(f"  ✓ Has {len(summary.play.play_stats)} stats")
                for stat in summary.play.play_stats[:2]:  # Show first 2 stats
                    print(f"    - {stat.player_name}: stat_id={stat.stat_id}, yards={stat.yards}")
            else:
                print(f"  ✗ Empty play_stats array")
        else:
            print(f"  ✗ No play summary returned")
        
        time.sleep(0.5)  # Be nice to the API
    
    print(f"\nSummary:")
    print(f"Plays with stats: {plays_with_stats}/10")
    print(f"Total stats found: {total_stats}")
else:
    print("Failed to fetch plays")